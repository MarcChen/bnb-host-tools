from unittest.mock import patch

import pytest

from services.notion_client.notion_api_client import NotionClient


@pytest.fixture
def mock_client(monkeypatch):  # added monkeypatch parameter
    monkeypatch.setenv("NOTION_API", "dummy")
    monkeypatch.setenv("DATABASE_ID", "dummy")
    with patch("services.notion_client.notion_api_client.Client") as mock_cls:
        yield mock_cls


def test_create_page(mock_client):
    instance = NotionClient()
    instance.client.pages.create.return_value = {"id": "test_page_id"}
    result = instance.create_page(confirmation_code="TEST123")
    assert result["id"] == "test_page_id"


def test_delete_page_by_reservation_code(mock_client):
    instance = NotionClient()
    instance.client.databases.query.return_value = {"results": [{"id": "page_id_1"}]}
    deleted_count = instance.delete_page_by_reservation_code("TEST123")
    assert deleted_count == 1


def test_row_exists_by_reservation_id_true(mock_client):
    instance = NotionClient()
    instance.client.databases.query.return_value = {"results": [{"id": "page_id_1"}]}
    assert instance.row_exists_by_reservation_id("TEST123")


def test_row_exists_by_reservation_id_false(mock_client):
    instance = NotionClient()
    instance.client.databases.query.return_value = {"results": []}
    assert not instance.row_exists_by_reservation_id("TEST123")
