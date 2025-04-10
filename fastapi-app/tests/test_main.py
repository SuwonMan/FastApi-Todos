import sys
import os
import json
import pytest
from fastapi.testclient import TestClient

# main.py가 있는 디렉토리 기준으로 import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "fastapi-app")))

from main import app, save_todos, load_todos, TodoItem

client = TestClient(app)
TODO_FILE = "fastapi-app/todo.json"

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # 테스트 전 초기화
    save_todos([])
    yield
    # 테스트 후 정리
    save_todos([])

def test_get_todos_empty():
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []

def test_create_todo():
    todo = {"id": 1, "title": "Test", "description": "Test description", "completed": False}
    response = client.post("/todos", json=todo)
    assert response.status_code == 200
    assert response.json()["title"] == "Test"

def test_create_todo_invalid():
    # description, completed 없음 → 422
    todo = {"id": 1, "title": "Invalid"}
    response = client.post("/todos", json=todo)
    assert response.status_code == 422

def test_get_todos_with_items():
    todo = TodoItem(id=1, title="Meeting", description="Project meeting", completed=False)
    save_todos([todo.dict()])
    response = client.get("/todos")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Meeting"

def test_update_todo():
    todo = TodoItem(id=1, title="Old", description="Old desc", completed=False)
    save_todos([todo.dict()])
    updated = {"id": 1, "title": "Updated", "description": "New desc", "completed": True}
    response = client.put("/todos/1", json=updated)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"

def test_update_todo_not_found():
    updated = {"id": 1, "title": "New", "description": "desc", "completed": True}
    response = client.put("/todos/1", json=updated)
    assert response.status_code == 404

def test_delete_todo():
    todo = TodoItem(id=1, title="Del", description="To delete", completed=False)
    save_todos([todo.dict()])
    response = client.delete("/todos/1")
    assert response.status_code == 200
    assert response.json()["message"] == "To-Do item deleted"

def test_delete_todo_not_found():
    response = client.delete("/todos/999")
    assert response.status_code == 200  # 삭제 없지만 일단 성공으로 처리
    assert response.json()["message"] == "To-Do item deleted"

def test_search_todos_found():
    todos = [
        TodoItem(id=1, title="Buy milk", description="Groceries", completed=False).dict(),
        TodoItem(id=2, title="Math homework", description="due Sunday", completed=False).dict(),
        TodoItem(id=3, title="Meeting", description="Team sync", completed=True).dict()
    ]
    save_todos(todos)
    response = client.get("/todos/search?q=homework")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Math homework"

def test_search_todos_not_found():
    todos = [TodoItem(id=1, title="Lunch", description="with team", completed=False).dict()]
    save_todos(todos)
    response = client.get("/todos/search?q=nonexistent")
    assert response.status_code == 200
    assert response.json() == []
