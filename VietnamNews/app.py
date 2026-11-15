#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vietnam Today News Dashboard - Python Web Server
Serves the dashboard web UI, settings API (/api/config), and JSON API endpoints at http://127.0.0.1:8088
"""

import json
import os
import threading
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from mcp_client import fetch_vietnam_news, GeminiMCPClient, load_config, save_config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "news_cache.json")
PORT = int(os.environ.get("PORT", "8088"))

_cache_lock = threading.Lock()
_cached_data = None


def get_news_data(force_refresh: bool = False) -> dict:
    global _cached_data
    with _cache_lock:
        if not force_refresh and _cached_data is not None:
            _cached_data["config"] = load_config()
            return _cached_data
        if not force_refresh and os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    _cached_data = json.load(f)
                _cached_data["config"] = load_config()
                return _cached_data
            except Exception:
                pass

        data = fetch_vietnam_news(limit_per_feed=6)
        _cached_data = data
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARN] Could not write cache file: {e}")
        return data


class DashboardHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filepath: str, content_type: str = None):
        if not os.path.isfile(filepath):
            self.send_error(404, "File not found")
            return
        with open(filepath, "rb") as f:
            content = f.read()
        if not content_type:
            content_type, _ = mimetypes.guess_type(filepath)
            content_type = content_type or "application/octet-stream"
        self.send_response(200)
        self.send_header(
            "Content-Type",
            f"{content_type}; charset=utf-8"
            if content_type.startswith("text/") or content_type == "application/javascript"
            else content_type,
        )
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self._send_file(os.path.join(BASE_DIR, "templates", "index.html"), "text/html")
        elif path.startswith("/static/"):
            rel = path[len("/static/"):]
            safe_path = os.path.normpath(os.path.join(BASE_DIR, "static", rel))
            if not safe_path.startswith(os.path.join(BASE_DIR, "static")):
                self.send_error(403)
                return
            self._send_file(safe_path)
        elif path == "/api/news":
            qs = parse_qs(parsed.query)
            force = qs.get("refresh", ["0"])[0] == "1"
            data = get_news_data(force_refresh=force)
            self._send_json(data)
        elif path == "/api/config":
            self._send_json(load_config())
        elif path == "/api/mcp-status":
            client = GeminiMCPClient()
            self._send_json(client.get_status())
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/refresh":
            data = get_news_data(force_refresh=True)
            self._send_json(data)
        elif parsed.path == "/api/config":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
                payload = json.loads(raw_body)
                current = load_config()
                if "ai_model" in payload and str(payload["ai_model"]).strip():
                    current["ai_model"] = str(payload["ai_model"]).strip()
                if "news_sources" in payload and isinstance(payload["news_sources"], list):
                    cleaned_sources = []
                    cat_map = {
                        "latest": "속보·종합",
                        "economy": "경제·비즈니스",
                        "hanoi": "하노이·로컬",
                        "society": "사회·로컬",
                        "tech": "IT·과학",
                        "culture": "문화·라이프",
                    }
                    for item in payload["news_sources"]:
                        if isinstance(item, dict) and str(item.get("url", "")).strip():
                            c_code = item.get("category") or "latest"
                            cleaned_sources.append({
                                "source": str(item.get("source") or "뉴스 사이트").strip(),
                                "category": c_code,
                                "category_ko": item.get("category_ko") or cat_map.get(c_code, "속보·종합"),
                                "url": str(item["url"]).strip(),
                            })
                    if cleaned_sources:
                        current["news_sources"] = cleaned_sources
                saved = save_config(current)
                refresh_now = bool(payload.get("refresh_now", True))
                data = get_news_data(force_refresh=refresh_now)
                self._send_json({"ok": True, "config": saved, "news": data})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=400)
        else:
            self.send_error(404, "Not Found")

    def log_message(self, fmt, *args):
        pass


def main():
    print("[VietnamNews] Initializing initial news cache...")
    get_news_data(force_refresh=False)
    server = HTTPServer(("0.0.0.0", PORT), DashboardHandler)
    print(f"[VietnamNews] Dashboard running on http://127.0.0.1:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
