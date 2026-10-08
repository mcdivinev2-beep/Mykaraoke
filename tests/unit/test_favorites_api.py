"""Tests for the shared song favorites API."""

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from flask_babel import Babel

from pikaraoke.routes.search_api import search_api_bp


@pytest.fixture
def client():
    app = Flask(__name__)
    app.secret_key = "test"
    Babel(app)
    app.register_blueprint(search_api_bp)
    return app.test_client()


class TestFavoritesApi:
    @patch("pikaraoke.routes.search_api.get_karaoke_instance")
    def test_adds_favorite_metadata(self, get_instance, client):
        karaoke = MagicMock()
        get_instance.return_value = karaoke

        response = client.post(
            "/api/favorites",
            json={
                "youtube_id": "aaaaaaaaaaa",
                "title": "Song",
                "channel": "Artist",
                "duration": "3:21",
            },
        )

        assert response.status_code == 200
        assert response.get_json() == {"success": True}
        karaoke.db.add_favorite.assert_called_once_with(
            "aaaaaaaaaaa", "Song", "Artist", "3:21"
        )

    def test_rejects_invalid_video_ids(self, client):
        response = client.post(
            "/api/favorites",
            json={"youtube_id": "invalid", "title": "Song"},
        )

        assert response.status_code == 422

    @patch("pikaraoke.routes.search_api.get_karaoke_instance")
    def test_deletes_existing_favorite(self, get_instance, client):
        karaoke = MagicMock()
        karaoke.db.delete_favorite.return_value = True
        get_instance.return_value = karaoke

        response = client.delete("/api/favorites/aaaaaaaaaaa")

        assert response.status_code == 200
        assert response.get_json() == {"success": True}
        karaoke.db.delete_favorite.assert_called_once_with("aaaaaaaaaaa")

    @patch("pikaraoke.routes.search_api.get_karaoke_instance")
    def test_returns_not_found_for_unknown_favorite(self, get_instance, client):
        karaoke = MagicMock()
        karaoke.db.delete_favorite.return_value = False
        get_instance.return_value = karaoke

        response = client.delete("/api/favorites/aaaaaaaaaaa")

        assert response.status_code == 404
