"""Tests for app/api/auth.py — 认证相关 API"""
import pytest
from unittest.mock import patch


class TestLogin:
    def test_login_success(self, client, test_user):
        resp = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "TestPass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
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

    def test_login_rate_limit(self, client, test_user):
        """连续失败 5 次后应触发 429"""
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


class TestLogout:
    def test_logout_clears_cookie(self, auth_client):
        resp = auth_client.post("/api/auth/logout")
        assert resp.status_code == 200
        # cookie 应被清除（delete_cookie 会从响应中移除 cookie）
        assert "access_token" not in resp.cookies or resp.cookies.get("access_token") is None
