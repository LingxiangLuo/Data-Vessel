"""Tests for app/api/datasources.py — 数据源 API"""
import pytest
from unittest.mock import patch, MagicMock


class TestList:
    def test_list_empty(self, auth_client):
        resp = auth_client.get("/api/datasources")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_with_keyword(self, auth_client, sample_datasource):
        resp = auth_client.get("/api/datasources?keyword=test_mysql")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "test_mysql"

    def test_list_unauthenticated(self, client):
        resp = client.get("/api/datasources")
        assert resp.status_code == 401


class TestCreate:
    def test_create_success(self, auth_client):
        resp = auth_client.post("/api/datasources", json={
            "name": "new_ds",
            "type": "mysql",
            "host": "127.0.0.1",
            "port": 3306,
            "database_name": "db1",
            "username": "user",
            "password": "pass",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "new_ds"
        assert data["type"] == "mysql"
        # 密码应被掩码
        assert "****" in data["username"]

    def test_create_invalid_type(self, auth_client):
        resp = auth_client.post("/api/datasources", json={
            "name": "bad_ds",
            "type": "unknown",
            "host": "127.0.0.1",
            "port": 3306,
            "database_name": "db1",
        })
        assert resp.status_code == 422

    def test_create_no_permission(self, client):
        """未登录用户应 401"""
        resp = client.post("/api/datasources", json={
            "name": "new_ds",
            "type": "mysql",
            "host": "127.0.0.1",
            "port": 3306,
            "database_name": "db1",
        })
        assert resp.status_code == 401


class TestGet:
    def test_get_success(self, auth_client, sample_datasource):
        resp = auth_client.get(f"/api/datasources/{sample_datasource.id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "test_mysql"

    def test_get_not_found(self, auth_client):
        resp = auth_client.get("/api/datasources/99999")
        assert resp.status_code == 404


class TestUpdate:
    def test_update_success(self, auth_client, sample_datasource):
        resp = auth_client.put(f"/api/datasources/{sample_datasource.id}", json={
            "host": "new_host",
        })
        assert resp.status_code == 200
        assert resp.json()["host"] == "new_host"

    def test_update_not_found(self, auth_client):
        resp = auth_client.put("/api/datasources/99999", json={"host": "x"})
        assert resp.status_code == 404


class TestDelete:
    def test_delete_success(self, auth_client, sample_datasource):
        resp = auth_client.delete(f"/api/datasources/{sample_datasource.id}")
        assert resp.status_code == 200
        # 再次获取应 404
        resp2 = auth_client.get(f"/api/datasources/{sample_datasource.id}")
        assert resp2.status_code == 404

    def test_delete_not_found(self, auth_client):
        resp = auth_client.delete("/api/datasources/99999")
        assert resp.status_code == 404


class TestConnection:
    @patch("app.core.db_adapter.test_connection")
    def test_test_connection_success(self, mock_test, auth_client, sample_datasource):
        mock_test.return_value = (True, "OK")
        resp = auth_client.post(f"/api/datasources/{sample_datasource.id}/test")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == 1
        assert data["message"] == "OK"

    @patch("app.core.db_adapter.test_connection")
    def test_test_connection_failure(self, mock_test, auth_client, sample_datasource):
        mock_test.return_value = (False, "Connection refused")
        resp = auth_client.post(f"/api/datasources/{sample_datasource.id}/test")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == 0
        assert data["message"] == "Connection refused"
