"""OAuth2 授权码流程封装 — 钉钉 / 飞书 / 企业微信（不依赖 authlib，用 httpx 直接实现）"""
import os
from urllib.parse import urlencode

import httpx

# ─── Redis 缓存（可选，未配置时降级为无缓存）────────────────────────────────

_redis_pool = None


def _get_redis():
    global _redis_pool
    if _redis_pool is None:
        try:
            import redis
            url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            _redis_pool = redis.ConnectionPool.from_url(
                url, decode_responses=True, socket_connect_timeout=2
            )
        except Exception:
            return None
    try:
        import redis
        return redis.Redis(connection_pool=_redis_pool)
    except Exception:
        return None


def _cache_get(key: str):
    r = _get_redis()
    if r:
        try:
            return r.get(key)
        except Exception:
            pass
    return None


def _cache_set(key: str, value: str, ttl: int):
    r = _get_redis()
    if r:
        try:
            r.setex(key, ttl, value)
        except Exception:
            pass

# ─── 各平台端点配置 ──────────────────────────────────────────────────────────

_PROVIDERS = {
    "dingtalk": {
        "auth_url":  "https://login.dingtalk.com/oauth2/auth",
        "token_url": "https://api.dingtalk.com/v1.0/oauth2/userAccessToken",
        "user_url":  "https://api.dingtalk.com/v1.0/contact/users/me",
        "scope":     "openid",
    },
    "feishu": {
        "auth_url":  "https://open.feishu.cn/open-apis/authen/v1/authorize",
        "token_url": "https://open.feishu.cn/open-apis/authen/v1/oidc/access_token",
        "user_url":  "https://open.feishu.cn/open-apis/authen/v1/user_info",
        "scope":     "contact:user.base:readonly",
    },
    "wecom": {
        "auth_url":  "https://open.weixin.qq.com/connect/oauth2/authorize",
        "token_url": "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo",
        "user_url":  None,
        "scope":     "snsapi_private",  # snsapi_base 只返回 OpenId，无法获取姓名
    },
}


def get_authorize_url(provider: str, app_id: str, redirect_uri: str, state: str) -> str:
    """构造第三方授权页 URL"""
    cfg = _PROVIDERS.get(provider)
    if not cfg:
        raise ValueError(f"不支持的 SSO 提供商: {provider}")

    if provider == "dingtalk":
        from urllib.parse import urlencode as _ue  # noqa — already imported at top
        params = {
            "response_type": "code",
            "client_id": app_id,
            "redirect_uri": redirect_uri,
            "scope": cfg["scope"],
            "state": state,
            # prompt=consent 省略，避免每次登录都弹授权页
        }
        return f"{cfg['auth_url']}?{urlencode(params)}"

    elif provider == "feishu":
        params = {
            "response_type": "code",
            "client_id": app_id,
            "redirect_uri": redirect_uri,
            "scope": cfg["scope"],
            "state": state,
        }
        return f"{cfg['auth_url']}?{urlencode(params)}"

    elif provider == "wecom":
        params = {
            "appid": app_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": cfg["scope"],
            "state": state,
        }
        return f"{cfg['auth_url']}?{urlencode(params)}#wechat_redirect"

    raise ValueError(f"不支持的 SSO 提供商: {provider}")


async def exchange_code_for_user(
    provider: str,
    code: str,
    app_id: str,
    app_secret: str,
    redirect_uri: str,
) -> dict:
    """用授权码换取用户信息，返回 {"openid": str, "name": str, "email": str|None}"""
    if provider == "dingtalk":
        return await _dingtalk_user(code, app_id, app_secret)
    elif provider == "feishu":
        return await _feishu_user(code, app_id, app_secret)
    elif provider == "wecom":
        return await _wecom_user(code, app_id, app_secret)
    raise ValueError(f"不支持的 SSO 提供商: {provider}")


async def _dingtalk_user(code: str, app_id: str, app_secret: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        # 1. 换 user_access_token
        resp = await client.post(
            "https://api.dingtalk.com/v1.0/oauth2/userAccessToken",
            json={"clientId": app_id, "clientSecret": app_secret, "code": code, "grantType": "authorization_code"},
        )
        resp.raise_for_status()
        token_data = resp.json()
        access_token = token_data.get("accessToken") or token_data.get("access_token")
        if not access_token:
            raise RuntimeError(f"钉钉换 token 失败: {token_data}")

        # 2. 获取用户信息
        resp2 = await client.get(
            "https://api.dingtalk.com/v1.0/contact/users/me",
            headers={"x-acs-dingtalk-access-token": access_token},
        )
        resp2.raise_for_status()
        info = resp2.json()
        return {
            "openid": info.get("openId") or info.get("unionId", ""),
            "name": info.get("nick") or info.get("name", ""),
            "email": info.get("email"),
            "avatar": info.get("avatarUrl"),
        }


async def _feishu_user(code: str, app_id: str, app_secret: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        # 1. 获取 app_access_token（带缓存，TTL 7000s）
        cache_key = f"feishu_app_token:{app_id}"
        app_token = _cache_get(cache_key)
        if not app_token:
            resp = await client.post(
                "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal",
                json={"app_id": app_id, "app_secret": app_secret},
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code", -1) != 0:
                raise RuntimeError(f"飞书 app_token 失败: {data.get('msg') or data.get('message', '未知错误')}")
            app_token = data.get("app_access_token", "")
            expire = data.get("expire", 7200)
            if app_token:
                _cache_set(cache_key, app_token, expire - 200)

        # 2. 用 code 换 user_access_token
        resp2 = await client.post(
            "https://open.feishu.cn/open-apis/authen/v1/oidc/access_token",
            headers={"Authorization": f"Bearer {app_token}"},
            json={"grant_type": "authorization_code", "code": code},
        )
        resp2.raise_for_status()
        data2_raw = resp2.json()
        if data2_raw.get("code", -1) != 0:
            raise RuntimeError(f"飞书换 token 失败: {data2_raw.get('msg') or data2_raw.get('message', '未知错误')}")
        data2 = data2_raw.get("data", {})
        user_token = data2.get("access_token", "")
        if not user_token:
            raise RuntimeError("飞书未返回 user_access_token")

        # 3. 获取用户信息
        resp3 = await client.get(
            "https://open.feishu.cn/open-apis/authen/v1/user_info",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        resp3.raise_for_status()
        data3_raw = resp3.json()
        if data3_raw.get("code", -1) != 0:
            raise RuntimeError(f"飞书获取用户信息失败: {data3_raw.get('msg') or data3_raw.get('message', '未知错误')}")
        info = data3_raw.get("data", {})
        return {
            "openid": info.get("open_id", ""),
            "name": info.get("name", ""),
            "email": info.get("email"),
            "avatar": info.get("avatar_url"),
        }


async def _wecom_user(code: str, app_id: str, app_secret: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        # 1. 获取 access_token（带缓存，TTL 7000s）
        cache_key = f"wecom_access_token:{app_id}"
        access_token = _cache_get(cache_key)
        if not access_token:
            resp = await client.get(
                "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
                params={"corpid": app_id, "corpsecret": app_secret},
            )
            resp.raise_for_status()
            token_data = resp.json()
            access_token = token_data.get("access_token", "")
            expires_in = token_data.get("expires_in", 7200)
            if access_token:
                _cache_set(cache_key, access_token, expires_in - 200)

        # 2. 用 code 获取 userid
        resp2 = await client.get(
            "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo",
            params={"access_token": access_token, "code": code},
        )
        resp2.raise_for_status()
        info2 = resp2.json()
        userid = info2.get("UserId") or info2.get("OpenId", "")

        # 3. 获取用户详情（企业成员）
        name = userid
        email = None
        avatar = None
        if info2.get("UserId"):
            resp3 = await client.get(
                "https://qyapi.weixin.qq.com/cgi-bin/user/get",
                params={"access_token": access_token, "userid": userid},
            )
            if resp3.status_code == 200:
                detail = resp3.json()
                name = detail.get("name", userid)
                email = detail.get("email")
                avatar = detail.get("avatar")

        return {
            "openid": userid,
            "name": name,
            "email": email,
            "avatar": avatar,
        }
