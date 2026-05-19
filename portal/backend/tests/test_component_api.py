"""Tests for app/api/component.py — 组件 API"""
import pytest


@pytest.fixture
def sample_folder(db_session):
    """创建一个测试文件夹。"""
    from app.models.component_folder import ComponentFolder
    f = ComponentFolder(name="test_folder", type="sql")
    db_session.add(f)
    db_session.flush()
    db_session.refresh(f)
    return f


class TestList:
    def test_list_empty(self, auth_client):
        resp = auth_client.get("/api/components")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_with_filter(self, auth_client, sample_component):
        resp = auth_client.get("/api/components?type=sql")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "test_sql_comp"

    def test_list_unauthenticated(self, client):
        resp = client.get("/api/components")
        assert resp.status_code == 401


class TestCreate:
    def test_create_sql_component(self, auth_client):
        resp = auth_client.post("/api/components", json={
            "name": "new_comp",
            "type": "sql",
            "config_json": {"sql": "SELECT 1"},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "new_comp"
        assert data["type"] == "sql"
        assert data["status"] == "draft"

    def test_create_invalid_type(self, auth_client):
        resp = auth_client.post("/api/components", json={
            "name": "bad_comp",
            "type": "unknown",
        })
        assert resp.status_code == 400

    def test_create_datax_missing_fields(self, auth_client):
        resp = auth_client.post("/api/components", json={
            "name": "datax_comp",
            "type": "datax",
            "config_json": {},
        })
        assert resp.status_code == 400

    def test_create_unauthenticated(self, client):
        resp = client.post("/api/components", json={"name": "x", "type": "sql"})
        assert resp.status_code == 401


class TestGet:
    def test_get_success(self, auth_client, sample_component):
        resp = auth_client.get(f"/api/components/{sample_component.id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "test_sql_comp"

    def test_get_not_found(self, auth_client):
        resp = auth_client.get("/api/components/99999")
        assert resp.status_code == 404


class TestUpdate:
    def test_update_success(self, auth_client, sample_component):
        resp = auth_client.put(f"/api/components/{sample_component.id}", json={
            "name": "updated_name",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "updated_name"

    def test_update_non_editable_status(self, auth_client, sample_component):
        sample_component.status = "online"
        from app.api.component import STATUS_ONLINE
        resp = auth_client.put(f"/api/components/{sample_component.id}", json={
            "name": "should_fail",
        })
        assert resp.status_code == 400

    def test_update_not_found(self, auth_client):
        resp = auth_client.put("/api/components/99999", json={"name": "x"})
        assert resp.status_code == 404


class TestDelete:
    def test_delete_success(self, auth_client, sample_component):
        resp = auth_client.delete(f"/api/components/{sample_component.id}")
        assert resp.status_code == 200
        resp2 = auth_client.get(f"/api/components/{sample_component.id}")
        assert resp2.status_code == 404

    def test_delete_not_found(self, auth_client):
        resp = auth_client.delete("/api/components/99999")
        assert resp.status_code == 404


class TestFolder:
    def test_create_folder(self, auth_client):
        resp = auth_client.post("/api/components/folders", json={
            "name": "my_folder",
            "type": "sql",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "my_folder"

    def test_list_folders(self, auth_client, sample_folder):
        resp = auth_client.get("/api/components/folders?type=sql")
        assert resp.status_code == 200
        items = resp.json()
        assert any(f["name"] == "test_folder" for f in items)

    def test_rename_folder(self, auth_client, sample_folder):
        resp = auth_client.put(f"/api/components/folders/{sample_folder.id}", json={
            "name": "renamed_folder",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "renamed_folder"

    def test_delete_folder(self, auth_client, sample_folder):
        resp = auth_client.delete(f"/api/components/folders/{sample_folder.id}")
        assert resp.status_code == 200

    def test_delete_folder_with_children(self, auth_client, sample_folder, db_session):
        from app.models.component_folder import ComponentFolder
        child = ComponentFolder(name="child", type="sql", parent_id=sample_folder.id)
        db_session.add(child)
        db_session.flush()
        resp = auth_client.delete(f"/api/components/folders/{sample_folder.id}")
        assert resp.status_code == 400

    def test_delete_folder_with_components(self, auth_client, sample_folder, sample_component):
        sample_component.folder_id = sample_folder.id
        resp = auth_client.delete(f"/api/components/folders/{sample_folder.id}")
        assert resp.status_code == 400
