"""API for previewing and downloading YouTube results."""

from flask import jsonify
from flask_smorest import Blueprint
from marshmallow import Schema, fields, validate

from pikaraoke.lib.auth import public
from pikaraoke.lib.current_app import get_karaoke_instance
from pikaraoke.lib.youtube_dl import get_stream_url

search_api_bp = Blueprint("search_api", __name__)


class PreviewQuery(Schema):
    url = fields.String(required=True, metadata={"description": "YouTube video URL to preview"})


class DownloadBody(Schema):
    song_url = fields.String(required=True, metadata={"description": "YouTube URL to download"})
    song_added_by = fields.String(
        required=True, metadata={"description": "Name of the user requesting the download"}
    )
    song_title = fields.String(
        required=True, metadata={"description": "Display title for the song"}
    )
    queue = fields.Boolean(
        load_default=False, metadata={"description": "Whether to queue the song after download"}
    )


class FavoriteBody(Schema):
    youtube_id = fields.String(
        required=True,
        validate=validate.Regexp(r"^[A-Za-z0-9_-]{11}$"),
        metadata={"description": "11-character YouTube video ID"},
    )
    title = fields.String(required=True, validate=validate.Length(min=1, max=500))
    channel = fields.String(load_default="", validate=validate.Length(max=300))
    duration = fields.String(load_default="", validate=validate.Length(max=20))


@search_api_bp.route("/api/preview")
@public
@search_api_bp.arguments(PreviewQuery, location="query")
def preview(query):
    """Get a direct stream URL for previewing a YouTube video."""
    stream_url = get_stream_url(query["url"])
    if stream_url is None:
        return jsonify({"error": "Could not fetch stream URL"}), 500
    return jsonify({"stream_url": stream_url})


@search_api_bp.route("/api/download", methods=["POST"])
@public
@search_api_bp.arguments(DownloadBody, location="json")
def download(form):
    """Download a video from YouTube."""
    k = get_karaoke_instance()
    song = form["song_url"]
    user = form["song_added_by"]
    title = form["song_title"]
    queue = form.get("queue", False)

    # Queue the download (processed serially by the download worker)
    k.download_manager.queue_download(song, queue, user, title)

    return jsonify({"status": "ok"})


@search_api_bp.route("/api/favorites", methods=["POST"])
@public
@search_api_bp.arguments(FavoriteBody, location="json")
def add_favorite(form):
    """Save a song to the server-wide favorites list."""
    k = get_karaoke_instance()
    k.db.add_favorite(
        form["youtube_id"],
        form["title"],
        form["channel"],
        form["duration"],
    )
    return jsonify({"success": True})


@search_api_bp.route("/api/favorites/<youtube_id>", methods=["DELETE"])
@public
def delete_favorite(youtube_id):
    """Remove a song from the server-wide favorites list."""
    k = get_karaoke_instance()
    if not k.db.delete_favorite(youtube_id):
        return jsonify({"success": False, "error": "Favorite not found"}), 404
    return jsonify({"success": True})
