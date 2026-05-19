"""Tests for app/api/workflow.py — 工作流 API"""
import pytest


@pytest.fixture
def sample_workflow(db_session, test_user, sample_component):
    """创建一个测试工作流。"""
    from app.models.workflow import Workflow
    w = Workflow(
        name="test_workflow",
        description="测试工作流",
        steps_json=[{"component_id": sample_component.id, "name": "step1"}],
        dag_json={
            "nodes": [{"id": "n1", "component_id": sample_component.id, "name": "step1", "position": {"x": 0, "y": 0}}],
            "edges": [],
        },
        status="draft",
        created_by=test_user.id,
    )
    db_session.add(w)
    db_session.flush()
    db_session.refresh(w)
    return w


class TestList:
    def test_list_empty(self, auth_client):
        resp = auth_client.get("/api/workflows")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_with_items(self, auth_client, sample_workflow):
        resp = auth_client.get("/api/workflows")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "test_workflow"


class TestCreate:
    def test_create_success(self, auth_client, sample_component):
        resp = auth_client.post("/api/workflows", json={
            "name": "new_flow",
            "steps": [{"component_id": sample_component.id}],
            "dag": {
                "nodes": [{"id": "n1", "component_id": sample_component.id, "position": {"x": 0, "y": 0}}],
                "edges": [],
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "new_flow"
        assert data["status"] == "draft"

    def test_create_missing_component(self, auth_client):
        resp = auth_client.post("/api/workflows", json={
            "name": "bad_flow",
            "steps": [{"component_id": 99999}],
        })
        assert resp.status_code == 400


class TestGet:
    def test_get_success(self, auth_client, sample_workflow):
        resp = auth_client.get(f"/api/workflows/{sample_workflow.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "test_workflow"
        assert len(data["steps"]) == 1

    def test_get_not_found(self, auth_client):
        resp = auth_client.get("/api/workflows/99999")
        assert resp.status_code == 404


class TestUpdate:
    def test_update_success(self, auth_client, sample_workflow):
        resp = auth_client.put(f"/api/workflows/{sample_workflow.id}", json={
            "name": "updated_flow",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "updated_flow"

    def test_update_not_found(self, auth_client):
        resp = auth_client.put("/api/workflows/99999", json={"name": "x"})
        assert resp.status_code == 404


class TestDelete:
    def test_delete_success(self, auth_client, sample_workflow):
        resp = auth_client.delete(f"/api/workflows/{sample_workflow.id}")
        assert resp.status_code == 200
        resp2 = auth_client.get(f"/api/workflows/{sample_workflow.id}")
        assert resp2.status_code == 404

    def test_delete_not_found(self, auth_client):
        resp = auth_client.delete("/api/workflows/99999")
        assert resp.status_code == 404
