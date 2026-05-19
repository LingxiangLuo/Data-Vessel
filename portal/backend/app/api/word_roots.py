from typing import Optional, List
import io
import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_permission
from app.models.word_root import WordRoot
from app.models.user import SysUser

router = APIRouter(prefix="/word-roots", tags=["词根管理"])


class WordRootCreate(BaseModel):
    en: str = Field(..., min_length=1, max_length=64)
    cn: str = Field(..., min_length=1, max_length=64)
    category: str = Field(default="business")
    description: Optional[str] = None
    example: Optional[str] = None


class WordRootUpdate(BaseModel):
    en: Optional[str] = None
    cn: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    example: Optional[str] = None


def _serialize(r: WordRoot) -> dict:
    return {
        "id": r.id,
        "en": r.en,
        "cn": r.cn,
        "category": r.category,
        "description": r.description,
        "example": r.example,
        "created_at": str(r.created_at) if r.created_at else None,
        "updated_at": str(r.updated_at) if r.updated_at else None,
    }


@router.get("")
def list_word_roots(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    q = db.query(WordRoot)
    if keyword:
        q = q.filter(or_(
            WordRoot.en.contains(keyword),
            WordRoot.cn.contains(keyword),
            WordRoot.description.contains(keyword),
        ))
    if category:
        q = q.filter(WordRoot.category == category)
    total = q.count()
    items = q.order_by(WordRoot.en).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [_serialize(r) for r in items], "total": total}


@router.post("")
def create_word_root(
    req: WordRootCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("metadata:write")),
):
    existing = db.query(WordRoot).filter(WordRoot.en == req.en.strip().lower()).first()
    if existing:
        raise HTTPException(400, f"词根 '{req.en}' 已存在")
    r = WordRoot(
        en=req.en.strip().lower(),
        cn=req.cn.strip(),
        category=req.category,
        description=req.description,
        example=req.example,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return _serialize(r)


@router.put("/{root_id}")
def update_word_root(
    root_id: int,
    req: WordRootUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("metadata:write")),
):
    r = db.query(WordRoot).filter(WordRoot.id == root_id).first()
    if not r:
        raise HTTPException(404, "词根不存在")
    updates = req.model_dump(exclude_unset=True)
    if "en" in updates:
        updates["en"] = updates["en"].strip().lower()
    for k, v in updates.items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return _serialize(r)


@router.delete("/{root_id}")
def delete_word_root(
    root_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("metadata:write")),
):
    r = db.query(WordRoot).filter(WordRoot.id == root_id).first()
    if not r:
        raise HTTPException(404, "词根不存在")
    db.delete(r)
    db.commit()
    return {"message": "已删除"}


@router.post("/import")
async def import_word_roots(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("metadata:write")),
):
    """Excel 批量导入词根（xlsx 格式，列：英文词根/中文名/分类/说明/示例）"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "请上传 .xlsx 文件")
    try:
        import openpyxl
        content = await file.read()
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(min_row=2, values_only=True))  # skip header
    except Exception as e:
        raise HTTPException(400, f"解析 Excel 失败: {e}")

    created = 0
    skipped = 0
    for row in rows:
        if not row or not row[0]:
            continue
        en = str(row[0]).strip().lower()
        cn = str(row[1]).strip() if len(row) > 1 and row[1] else en
        category = str(row[2]).strip() if len(row) > 2 and row[2] else "business"
        desc = str(row[3]).strip() if len(row) > 3 and row[3] else None
        example = str(row[4]).strip() if len(row) > 4 and row[4] else None
        # category 映射
        cat_map = {"业务词根": "business", "技术词根": "technical", "度量词根": "metric",
                   "business": "business", "technical": "technical", "metric": "metric"}
        category = cat_map.get(category, "business")
        existing = db.query(WordRoot).filter(WordRoot.en == en).first()
        if existing:
            skipped += 1
            continue
        db.add(WordRoot(en=en, cn=cn, category=category, description=desc, example=example))
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped, "total_rows": len(rows)}


@router.get("/suggest")
def suggest_naming(
    q: str,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """中文输入 → 推荐英文命名。将输入拆分为词根并组合"""
    if not q.strip():
        return {"input": q, "suggestion": "", "matches": []}
    # 获取所有词根
    all_roots = db.query(WordRoot).all()
    cn_to_en = {r.cn: r.en for r in all_roots}
    # 贪心匹配：从左到右尝试最长匹配
    input_text = q.strip()
    parts = []
    matches = []
    i = 0
    while i < len(input_text):
        matched = False
        for length in range(min(8, len(input_text) - i), 0, -1):
            segment = input_text[i:i+length]
            if segment in cn_to_en:
                parts.append(cn_to_en[segment])
                matches.append({"cn": segment, "en": cn_to_en[segment]})
                i += length
                matched = True
                break
        if not matched:
            i += 1
    suggestion = "_".join(parts) if parts else ""
    return {"input": q, "suggestion": suggestion, "matches": matches}
