"""Tests for app/api/auth.py — 认证相关 API"""
import pytest
from unittest.mock import patch, MagicMock


class TestLogin:
    def test_login_success(self, client, test_user):
        resp = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "TestPass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        # access_token 不再返回响应体，仅通过 httponly cookie 下发
        assert "user" in data
        assert data["user"]["username"] == "testuser"
        # cookie 应设置 access_token
        assert "access_token" in resp.cookies

    def test_login_wrong_password(self, client, test_user):
        resp = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "nobody",
            "password": "anypass",
        })
        assert resp.status_code == 401

    def test_login_disabled_user(self, client, test_user, db_session):
        """禁用账号应返回 403"""
        from app.models.user import SysUser
        user = db_session.query(SysUser).filter(SysUser.username == "testuser").first()
        user.status = 0
        db_session.commit()
        resp = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "TestPass123",
        })
        assert resp.status_code == 403

    def test_login_password_too_long(self, client):
        """密码超过 128 位应直接拒绝，避免 bcrypt DoS"""
        resp = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "x" * 129,
        })
        assert resp.status_code == 400

    def test_login_rate_limit(self, client, test_user):
        """连续失败超过上限后应触发 429"""
        from app.core.config import settings
        original_max = settings.LOGIN_MAX_ATTEMPTS
        settings.LOGIN_MAX_ATTEMPTS = 5
        try:
            for _ in range(5):
                client.post("/api/auth/login", json={
                    "username": "testuser",
                    "password": "wrong",
                })
            resp = client.post("/api/auth/login", json={
                "username": "testuser",
                "password": "wrong",
            })
            assert resp.status_code == 429
        finally:
            settings.LOGIN_MAX_ATTEMPTS = original_max


class TestCsrf:
    def test_csrf_token_endpoint(self, client):
        """CSRF 端点应返回 token 并设置 cookie"""
        resp = client.get("/api/auth/csrf")
        assert resp.status_code == 200
        data = resp.json()
        assert "csrf_token" in data
        assert "csrf_token" in resp.cookies


class TestMe:
    def test_get_me_authenticated(self, auth_client, test_user):
        resp = auth_client.get("/api/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testuser"

    def test_get_me_unauthenticated(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_get_permissions(self, auth_client):
        resp = auth_client.get("/api/auth/me/permissions")
        assert resp.status_code == 200
        data = resp.json()
        assert "permissions" in data
        assert isinstance(data["permissions"], list)


class TestPassword:
    def test_change_password_success(self, auth_client, test_user, db_session):
        resp = auth_client.put("/api/auth/password", json={
            "old_password": "TestPass123",
            "new_password": "NewPass456",
        })
        assert resp.status_code == 200

        # 用新密码登录
        resp2 = auth_client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "NewPass456",
        })
        assert resp2.status_code == 200

    def test_change_password_wrong_old(self, auth_client):
        resp = auth_client.put("/api/auth/password", json={
            "old_password": "wrong",
            "new_password": "NewPass456",
        })
        assert resp.status_code == 400

    def test_change_password_weak(self, auth_client):
        resp = auth_client.put("/api/auth/password", json={
            "old_password": "TestPass123",
            "new_password": "123",
        })
        assert resp.status_code == 400

    def test_change_password_missing_uppercase(self, auth_client):
        resp = auth_client.put("/api/auth/password", json={
            "old_password": "TestPass123",
            "new_password": "newpass456",
        })
        assert resp.status_code == 400

    def test_change_password_missing_lowercase(self, auth_client):
        resp = auth_client.put("/api/auth/password", json={
            "old_password": "TestPass123",
            "new_password": "NEWPASS456",
        })
        assert resp.status_code == 400

    def test_change_password_missing_digit(self, auth_client):
        resp = auth_client.put("/api/auth/password", json={
            "old_password": "TestPass123",
            "new_password": "NewPassword",
        })
        assert resp.status_code == 400


class TestLogout:
    def test_logout_clears_cookie(self, auth_client):
        resp = auth_client.post("/api/auth/logout")
        assert resp.status_code == 200
        # delete_cookie 会从响应中移除 cookie
        assert "access_token" not in resp.cookies


class TestCsrfMiddleware:
    def test_post_without_csrf_header_rejected(self, client, test_user):
        """携带 auth cookie 但无 X-CSRF-Token 的 POST 应被 403"""
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": test_user.username})
        client.cookies.set("access_token", token)
        resp = client.put("/api/auth/password", json={
            "old_password": "TestPass123",
            "new_password": "NewPass456",
        })
        assert resp.status_code == 403
        assert "CSRF" in resp.json()["detail"]

    def test_post_with_csrf_header_allowed(self, client, test_user):
        """同时携带 auth cookie 和匹配的 X-CSRF-Token 应通过"""
        import secrets
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": test_user.username})
        csrf = secrets.token_urlsafe(32)
        client.cookies.set("access_token", token)
        client.cookies.set("csrf_token", csrf)
        client.headers["X-CSRF-Token"] = csrf
        resp = client.put("/api/auth/password", json={
            "old_password": "TestPass123",
            "new_password": "NewPass456",
        })
        assert resp.status_code == 200


class TestValidation:
    def test_login_missing_password_422(self, client):
        """缺少必填字段应返回 422"""
        resp = client.post("/api/auth/login", json={"username": "testuser"})
        assert resp.status_code == 422

    def test_change_password_missing_field_422(self, auth_client):
        resp = auth_client.put("/api/auth/password", json={"old_password": "TestPass123"})
        assert resp.status_code == 422


def _get_or_create_oauth_config(db_session, provider="dingtalk"):
    """获取或创建 OAuth 配置，避免跨测试 UNIQUE 冲突"""
    from app.models.oauth_config import SysOAuthConfig
    cfg = db_session.query(SysOAuthConfig).filter(SysOAuthConfig.provider == provider).first()
    if not cfg:
        cfg = SysOAuthConfig(
            provider=provider,
            app_id="test_app_id",
            app_secret="test_secret",
            redirect_uri="http://localhost/callback",
            enabled=True,
        )
        db_session.add(cfg)
        db_session.commit()
    return cfg


class TestOAuthRedirect:
    def test_oauth_redirect_unconfigured_provider(self, client):
        """未配置的 OAuth 提供商应返回 400"""
        resp = client.get("/api/auth/oauth/dingtalk", follow_redirects=False)
        assert resp.status_code == 400

    def test_oauth_redirect_sets_state_cookie(self, client, db_session):
        """已配置的 OAuth 提供商应重定向并设置 state cookie"""
        _get_or_create_oauth_config(db_session)

        with patch("app.core.oauth.get_authorize_url", return_value="http://mock-auth-url"):
            resp = client.get("/api/auth/oauth/dingtalk", follow_redirects=False)
        assert resp.status_code == 307
        assert "oauth_state" in resp.cookies


class TestOAuthCallback:
    def test_oauth_callback_invalid_state(self, client):
        """state 验证失败应返回 400"""
        resp = client.get("/api/auth/oauth/dingtalk/callback?code=abc&state=xyz", follow_redirects=False)
        assert resp.status_code == 400

    def test_oauth_callback_valid_state_creates_user(self, client, db_session):
        """合法 state + 新用户 → 创建用户并重定向到 /oauth-callback#status=ok"""
        _get_or_create_oauth_config(db_session)

        # 构造合法 state cookie
        from app.api.auth import _sign_state
        state = "test_state_123"
        signed = _sign_state(state, "dingtalk")
        client.cookies.set("oauth_state", signed)

        mock_user = {"openid": "openid_123", "name": "Test Ding", "email": "test@example.com"}
        with patch("app.core.oauth.exchange_code_for_user", return_value=mock_user):
            resp = client.get(
                f"/api/auth/oauth/dingtalk/callback?code=abc&state={state}",
                follow_redirects=False,
            )
        assert resp.status_code == 307
        assert resp.headers["location"] == "/oauth-callback#status=ok"
        assert "access_token" in resp.cookies

    def test_oauth_callback_existing_bound_user(self, client, db_session):
        """已绑定 OAuth 的用户再次登录 → 直接签发 token，不重复创建"""
        from app.models.user import SysUser
        from app.core.security import hash_password
        _get_or_create_oauth_config(db_session)

        # 预创建一个已绑定的用户
        user = SysUser(
            username="dingtalk_existing",
            password=hash_password("irrelevant"),
            real_name="Existing User",
            oauth_provider="dingtalk",
            oauth_openid="openid_existing",
            status=1,
            role="user",
        )
        db_session.add(user)
        db_session.commit()

        from app.api.auth import _sign_state
        state = "state_existing"
        signed = _sign_state(state, "dingtalk")
        client.cookies.set("oauth_state", signed)

        mock_user = {"openid": "openid_existing", "name": "Existing User", "email": "ex@example.com"}
        with patch("app.core.oauth.exchange_code_for_user", return_value=mock_user):
            resp = client.get(
                f"/api/auth/oauth/dingtalk/callback?code=abc&state={state}",
                follow_redirects=False,
            )
        assert resp.status_code == 307
        assert resp.headers["location"] == "/oauth-callback#status=ok"
        assert "access_token" in resp.cookies

    def test_oauth_callback_username_conflict_409(self, client, db_session):
        """同名本地用户无 OAuth 绑定 → 返回 409 避免账号劫持"""
        from app.models.user import SysUser
        from app.core.security import hash_password
        _get_or_create_oauth_config(db_session)

        # 预创建同名本地用户（无 oauth_provider）
        openid = "openid_conflict"
        import hashlib
        short_hash = hashlib.sha256(openid.encode()).hexdigest()[:12]
        username = f"dingtalk_{short_hash}"
        user = SysUser(
            username=username,
            password=hash_password("localpass"),
            real_name="Local User",
            status=1,
            role="user",
        )
        db_session.add(user)
        db_session.commit()

        from app.api.auth import _sign_state
        state = "state_conflict"
        signed = _sign_state(state, "dingtalk")
        client.cookies.set("oauth_state", signed)

        mock_user = {"openid": openid, "name": "Conflict User", "email": "c@example.com"}
        with patch("app.core.oauth.exchange_code_for_user", return_value=mock_user):
            resp = client.get(
                f"/api/auth/oauth/dingtalk/callback?code=abc&state={state}",
                follow_redirects=False,
            )
        assert resp.status_code == 409
