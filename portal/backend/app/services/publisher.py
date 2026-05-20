"""WorkflowPublisher — 负责将 Portal Workflow 同步到 DolphinScheduler

拆分职责：
- publish: 翻译 + 创建/更新 DS Process Definition（保持 OFFLINE）+ 处理 Schedule
- online:  单独上线 DS Process Definition
- offline: 单独下线 DS Process Definition
"""
import asyncio
import os
import uuid
from typing import List, Dict, Any, Tuple, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.ds_client import get_ds_client
from app.core.dsl_translator import translate_workflow, translate_workflow_dag
from app.models.workflow import Workflow
from app.models.component import Component
from app.models.datasource import DataSource
from app.models.dqc_rule import DqcRule


class WorkflowPublisher:
    """工作流发布器：封装 DS 同步逻辑"""

    def __init__(self, db: Session):
        self.db = db
        self.ds = get_ds_client()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def publish(self, w: Workflow) -> Tuple[int, Optional[int]]:
        """翻译并同步 workflow 到 DS，返回 (pd_code, schedule_id)。

        Process Definition 创建后保持 OFFLINE 状态，调用方需随后执行 online()。
        """
        comp_ids, node_count = self._extract_nodes(w)
        comps, comp_map = self._load_components(comp_ids)
        datasource_map = await self._sync_datasources(comps)
        dqc_rules_lookup, dqc_count = self._collect_dqc_rules(comps)
        task_codes = await self._allocate_task_codes(node_count, dqc_count)
        svc_token = await self._ensure_service_token(w, dqc_count)
        payload = self._translate(w, comp_map, task_codes, datasource_map, dqc_rules_lookup, svc_token)
        pd_code = await self._upsert_process_definition(w, payload)
        schedule_id = await self._upsert_schedule(w, pd_code)
        return pd_code, schedule_id

    async def online(self, pd_code: int) -> None:
        """上线 DS Process Definition"""
        ok = await self.ds.release_process_definition(pd_code, online=True)
        if not ok:
            raise HTTPException(status_code=502, detail="DS 上线 process-definition 失败")

    async def offline(self, pd_code: int) -> None:
        """下线 DS Process Definition"""
        ok = await self.ds.release_process_definition(pd_code, online=False)
        if not ok:
            raise HTTPException(status_code=502, detail="DS 下线 process-definition 失败")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_nodes(self, w: Workflow) -> Tuple[List[int], int]:
        """提取组件 ID 列表和节点数量"""
        if w.dag_json and w.dag_json.get("nodes"):
            dag_nodes = w.dag_json["nodes"]
            active_nodes = [n for n in dag_nodes if not n.get("skip", False)]
            if not active_nodes:
                raise HTTPException(status_code=400, detail="DAG 中没有可执行的节点（全部被跳过）")
            comp_ids = [n["component_id"] for n in active_nodes]
            return comp_ids, len(active_nodes)
        else:
            steps = w.steps_json or []
            if not steps:
                raise HTTPException(status_code=400, detail="工作流为空")
            comp_ids = [s.get("component_id") for s in steps]
            return comp_ids, len(steps)

    async def _load_components(self, comp_ids: List[int]) -> Tuple[List[Component], Dict[int, Component]]:
        def _fetch():
            comps = self.db.query(Component).filter(Component.id.in_(comp_ids)).all()
            return comps, {c.id: c for c in comps}
        return await asyncio.to_thread(_fetch)

    async def _sync_datasources(self, comps: List[Component]) -> Dict[int, DataSource]:
        """同步 Portal 数据源到 DS，返回 {id: DataSource}"""
        ds_ids = set()
        for c in comps:
            cfg = c.config_json or {}
            if cfg.get("datasource_id"):
                ds_ids.add(cfg["datasource_id"])
            if c.type == "datax":
                if cfg.get("source_id"):
                    ds_ids.add(cfg["source_id"])
                if cfg.get("target_id"):
                    ds_ids.add(cfg["target_id"])

        datasource_map = {}
        if ds_ids:
            def _fetch():
                return self.db.query(DataSource).filter(DataSource.id.in_(list(ds_ids))).all()
            dss = await asyncio.to_thread(_fetch)
            datasource_map = {d.id: d for d in dss}

        for ds_obj in datasource_map.values():
            if ds_obj.ds_datasource_id:
                continue
            ds_list = await self.ds.list_datasources(page_size=200)
            matched = next((x for x in ds_list if x.get("name") == ds_obj.name), None)
            if matched:
                ds_obj.ds_datasource_id = matched.get("id")
                continue
            from app.core.encrypt import decrypt_password
            plain_password = decrypt_password(ds_obj.password) or ""
            new_id = await self.ds.create_datasource(
                name=ds_obj.name,
                ds_type=ds_obj.type,
                host=ds_obj.host,
                port=ds_obj.port,
                database=ds_obj.database_name,
                username=ds_obj.username or "",
                password=plain_password,
            )
            if new_id:
                ds_obj.ds_datasource_id = new_id
            else:
                raise HTTPException(
                    status_code=502,
                    detail=f"数据源 '{ds_obj.name}' 同步到 DS 失败，请检查 DS 连接权限"
                )
        return datasource_map

    async def _collect_dqc_rules(self, comps: List[Component]) -> Tuple[Dict[int, List[DqcRule]], int]:
        """收集组件关联的 DQC 规则"""
        all_rule_ids = set()
        comp_to_rule_ids: Dict[int, List[int]] = {}
        for c in comps:
            rule_ids = c.dqc_rule_ids or []
            if rule_ids:
                comp_to_rule_ids[c.id] = rule_ids
                all_rule_ids.update(rule_ids)

        dqc_rules_lookup: Dict[int, List[DqcRule]] = {}
        dqc_count = 0
        if all_rule_ids:
            def _fetch():
                return self.db.query(DqcRule).filter(
                    DqcRule.id.in_(list(all_rule_ids)),
                    DqcRule.enabled == True,
                ).all()
            rules = await asyncio.to_thread(_fetch)
            rule_map = {r.id: r for r in rules}
            for cid, rid_list in comp_to_rule_ids.items():
                comp_rules = [rule_map[rid] for rid in rid_list if rid in rule_map]
                if comp_rules:
                    dqc_rules_lookup[cid] = comp_rules
                    dqc_count += len(comp_rules)
        return dqc_rules_lookup, dqc_count

    async def _allocate_task_codes(self, node_count: int, dqc_count: int) -> List[int]:
        total = node_count + dqc_count
        task_codes = await self.ds.gen_task_codes(total)
        if not task_codes or len(task_codes) < total:
            raise HTTPException(status_code=502, detail="DS 生成 task code 失败")
        return [int(x) for x in task_codes[:total]]

    async def _ensure_service_token(self, w: Workflow, dqc_count: int) -> str:
        if dqc_count > 0:
            if not w.service_token:
                w.service_token = str(uuid.uuid4())
                def _flush():
                    self.db.flush()
                await asyncio.to_thread(_flush)
            return w.service_token
        return ""

    def _translate(
        self,
        w: Workflow,
        comp_map: Dict[int, Component],
        task_codes: List[int],
        datasource_map: Dict[int, DataSource],
        dqc_rules_lookup: Dict[int, List[DqcRule]],
        svc_token: str,
    ) -> Dict[str, Any]:
        portal_url = os.environ.get("PORTAL_BASE_URL", "http://portal:8000")
        kwargs = {
            "datasource_lookup": datasource_map,
            "dqc_rules_lookup": dqc_rules_lookup,
            "portal_base_url": portal_url,
            "service_token": svc_token,
        }
        if w.dag_json and w.dag_json.get("nodes"):
            return translate_workflow_dag(w, comp_map, task_codes, **kwargs)
        return translate_workflow(w, comp_map, task_codes, **kwargs)

    async def _upsert_process_definition(self, w: Workflow, payload: Dict[str, Any]) -> int:
        """创建或更新 DS Process Definition（保持 OFFLINE）"""
        if w.ds_process_code:
            # 先 offline 才能更新
            await self.ds.release_process_definition(w.ds_process_code, online=False)
            ok = await self.ds.update_process_definition(
                w.ds_process_code,
                payload["name"], payload["description"],
                payload["taskDefinitionJson"], payload["taskRelationJson"], payload["locations"],
            )
            if not ok:
                raise HTTPException(status_code=502, detail="DS 更新 process-definition 失败")
            return w.ds_process_code
        else:
            pd_code = await self.ds.save_process_definition(
                payload["name"], payload["description"],
                payload["taskDefinitionJson"], payload["taskRelationJson"], payload["locations"],
            )
            if not pd_code:
                raise HTTPException(status_code=502, detail="DS 创建 process-definition 失败")
            return pd_code

    async def _upsert_schedule(self, w: Workflow, pd_code: int) -> Optional[int]:
        schedule_id = w.ds_schedule_id
        if w.cron_expression:
            if schedule_id:
                await self.ds.update_schedule(schedule_id, w.cron_expression)
            else:
                schedule_id = await self.ds.create_schedule(pd_code, w.cron_expression)
        return schedule_id
