"""Tests for app/api/dqc_rules.py — 数据质量规则 API"""
import pytest


@pytest.fixture
def sample_rule(db_session, test_user, sample_datasource):
    """创建一个测试 DQC 规则。"""
    from app.models.dqc_rule import DqcRule
    r = DqcRule(
        name="row_count_check",
        datasource_id=sample_datasource.id,
        table_name="orders",
        rule_type="row_count",
        operator=">",
        threshold="100",
        is_strong=True,
        enabled=True,
        created_by=test_user.id,
    )
    db_session.add(r)
    db_session.flush()
    db_session.refresh(r)
    return r


class TestList:
    def test_list_empty(self, auth_client):
        resp = auth_client.get("/api/dqc-rules")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    def test_list_with_filter(self, auth_client, sample_rule):
        resp = auth_client.get(f"/api/dqc-rules?datasource_id={sample_rule.datasource_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "row_count_check"


class TestCreate:
    def test_create_success(self, auth_client, sample_datasource):
        resp = auth_client.post("/api/dqc-rules", json={
            "name": "null_check",
            "datasource_id": sample_datasource.id,
            "table_name": "users",
            "column_name": "email",
            "rule_type": "null_count",
            "operator": "<=",
            "threshold": "5",
            "is_strong": False,
            "enabled": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "null_check"
        assert data["rule_type"] == "null_count"

    def test_create_missing_datasource(self, auth_client):
        resp = auth_client.post("/api/dqc-rules", json={
            "name": "bad_rule",
            "datasource_id": 99999,
            "table_name": "t",
            "rule_type": "row_count",
            "operator": ">",
            "threshold": "0",
        })
        assert resp.status_code == 404


class TestGet:
    def test_get_success(self, auth_client, sample_rule):
        resp = auth_client.get(f"/api/dqc-rules/{sample_rule.id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "row_count_check"

    def test_get_not_found(self, auth_client):
        resp = auth_client.get("/api/dqc-rules/99999")
        assert resp.status_code == 404


class TestUpdate:
    def test_update_success(self, auth_client, sample_rule):
        resp = auth_client.put(f"/api/dqc-rules/{sample_rule.id}", json={
            "threshold": "200",
        })
        assert resp.status_code == 200
        assert resp.json()["threshold"] == "200"

    def test_update_not_found(self, auth_client):
        resp = auth_client.put("/api/dqc-rules/99999", json={"threshold": "1"})
        assert resp.status_code == 404


class TestDelete:
    def test_delete_success(self, auth_client, sample_rule):
        resp = auth_client.delete(f"/api/dqc-rules/{sample_rule.id}")
        assert resp.status_code == 200
        resp2 = auth_client.get(f"/api/dqc-rules/{sample_rule.id}")
        assert resp2.status_code == 404

    def test_delete_not_found(self, auth_client):
        resp = auth_client.delete("/api/dqc-rules/99999")
        assert resp.status_code == 404


class TestToggle:
    def test_toggle(self, auth_client, sample_rule):
        assert sample_rule.enabled is True
        resp = auth_client.patch(f"/api/dqc-rules/{sample_rule.id}/toggle")
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False
        # 再次 toggle 恢复
        resp2 = auth_client.patch(f"/api/dqc-rules/{sample_rule.id}/toggle")
        assert resp2.status_code == 200
        assert resp2.json()["enabled"] is True

    def test_toggle_not_found(self, auth_client):
        resp = auth_client.patch("/api/dqc-rules/99999/toggle")
        assert resp.status_code == 404
