from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_permission

router = APIRouter()


class OAuthConfigUpdate(BaseModel):
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    enabled: Optional[bool] = None
    extra_config: Optional[dict] = None


@router.get("/sso/public")
def list_sso_public(db: Session = Depends(get_db)):
    from app.models.oauth_config import SysOAuthConfig
    configs = db.query(SysOAuthConfig).filter(SysOAuthConfig.enabled == True).all()
    return [{"provider": c.provider} for c in configs]


@router.get("/sso")
def list_sso(
    db: Session = Depends(get_db),
    _=Depends(require_permission("system:config")),
):
    from app.models.oauth_config import SysOAuthConfig
    from .config import _redact
    configs = db.query(SysOAuthConfig).all()
    return [
        {
            "id": c.id,
            "provider": c.provider,
            "app_id": c.app_id,
            "redirect_uri": c.redirect_uri,
            "enabled": c.enabled,
            "extra_config": _redact(c.extra_config) if c.extra_config else None,
        }
        for c in configs
    ]


@router.put("/sso/{provider}")
def update_sso(
    provider: str,
    body: OAuthConfigUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("system:config")),
):
    from app.models.oauth_config import SysOAuthConfig
    cfg = db.query(SysOAuthConfig).filter(SysOAuthConfig.provider == provider).first()
    if not cfg:
        cfg = SysOAuthConfig(provider=provider)
        db.add(cfg)
    if body.app_id is not None:
        cfg.app_id = body.app_id
    if body.app_secret is not None:
        cfg.app_secret = body.app_secret
    if body.redirect_uri is not None:
        cfg.redirect_uri = body.redirect_uri
    if body.enabled is not None:
        cfg.enabled = body.enabled
    if body.extra_config is not None:
        cfg.extra_config = body.extra_config
    db.commit()
    return {"ok": True}
