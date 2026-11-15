#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini MCP Client & Vietnam News Collector
Communicates with the local Gemini MCP server (@houtini/gemini-mcp) via stdio JSON-RPC
and collects real-time Vietnam news RSS feeds (VnExpress, Tuoi Tre, Thanh Nien).
"""

import json
import os
import re
import html
import subprocess
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

MCP_COMMAND = "/home/zerohs/.nvm/versions/node/v24.22.1/bin/gemini-mcp"
NODE_BIN_DIR = "/home/zerohs/.nvm/versions/node/v24.22.1/bin"

RSS_SOURCES = [
    {
        "source": "VnExpress",
        "category": "latest",
        "category_ko": "속보·종합",
        "url": "https://vnexpress.net/rss/tin-moi-nhat.rss",
    },
    {
        "source": "VnExpress",
        "category": "economy",
        "category_ko": "경제·비즈니스",
        "url": "https://vnexpress.net/rss/kinh-doanh.rss",
    },
    {
        "source": "Tuổi Trẻ",
        "category": "society",
        "category_ko": "사회·로컬",
        "url": "https://tuoitre.vn/rss/thoi-su.rss",
    },
    {
        "source": "VnExpress",
        "category": "tech",
        "category_ko": "IT·과학",
        "url": "https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss",
    },
    {
        "source": "Tuổi Trẻ",
        "category": "culture",
        "category_ko": "문화·라이프",
        "url": "https://tuoitre.vn/rss/van-hoa.rss",
    },
]


def load_gemini_api_key() -> str:
    env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if env_key:
        return env_key
    try:
        mcp_cfg_path = os.path.expanduser("~/.config/Code/User/mcp.json")
        if os.path.exists(mcp_cfg_path):
            with open(mcp_cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            key = (
                cfg.get("servers", {})
                .get("gemini", {})
                .get("env", {})
                .get("GEMINI_API_KEY")
            )
            if key:
                return key
    except Exception:
        pass
    try:
        oc_path = os.path.expanduser("~/.openclaw/openclaw.json")
        if os.path.exists(oc_path):
            with open(oc_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return (
                cfg.get("plugins", {})
                .get("entries", {})
                .get("google", {})
                .get("config", {})
                .get("webSearch", {})
                .get("apiKey", "")
            )
    except Exception:
        pass
    return ""


class GeminiMCPClient:
    """JSON-RPC 2.0 stdio client for @houtini/gemini-mcp"""

    def __init__(self):
        self.api_key = load_gemini_api_key()
        self.command = MCP_COMMAND

    def call_mcp(self, method: str, params: dict = None, timeout: float = 15.0) -> dict:
        env = os.environ.copy()
        if self.api_key:
            env["GEMINI_API_KEY"] = self.api_key
            env["GOOGLE_API_KEY"] = self.api_key
        env["PATH"] = f"{NODE_BIN_DIR}:{env.get('PATH', '')}"

        proc = subprocess.Popen(
            [self.command],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
        )
        try:
            init_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "vietnam-news-dashboard", "version": "1.0.0"},
                },
            }
            proc.stdin.write(json.dumps(init_req) + "\n")
            proc.stdin.flush()
            init_line = proc.stdout.readline().strip()
            init_resp = json.loads(init_line) if init_line else {}

            if method == "initialize":
                return init_resp

            proc.stdin.write(
                json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
            )
            proc.stdin.flush()

            req = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": method,
                "params": params or {},
            }
            proc.stdin.write(json.dumps(req) + "\n")
            proc.stdin.flush()
            resp_line = proc.stdout.readline().strip()
            return json.loads(resp_line) if resp_line else {}
        finally:
            try:
                proc.terminate()
            except Exception:
                pass

    def get_status(self) -> dict:
        try:
            init_res = self.call_mcp("initialize", timeout=5.0)
            server_info = init_res.get("result", {}).get("serverInfo", {})
            tools_res = self.call_mcp("tools/list", timeout=5.0)
            tools = [
                t.get("name")
                for t in tools_res.get("result", {}).get("tools", [])
            ]
            return {
                "connected": bool(server_info),
                "server_name": server_info.get("name", "gemini-mcp"),
                "server_version": server_info.get("version", "2.10.1"),
                "protocol_version": init_res.get("result", {}).get("protocolVersion", "2024-11-05"),
                "tools_count": len(tools),
                "tools": tools,
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "server_name": "gemini-mcp",
                "tools_count": 0,
                "tools": [],
            }

    def summarize_with_gemini(self, prompt: str, model: str = "gemini-3-flash-preview") -> dict:
        try:
            res = self.call_mcp(
                "tools/call",
                {
                    "name": "gemini_chat",
                    "arguments": {
                        "message": prompt,
                        "model": model,
                        "grounding": True,
                    },
                },
                timeout=20.0,
            )
            content = res.get("result", {}).get("content", [])
            text = content[0].get("text", "") if content else ""
            if text.startswith("Error:"):
                return {"ok": False, "error": text}
            return {"ok": True, "text": text}
        except Exception as e:
            return {"ok": False, "error": str(e)}


def strip_html_and_extract_img(raw_html: str):
    if not raw_html:
        return "", ""
    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', raw_html)
    img_url = img_match.group(1) if img_match else ""
    clean = re.sub(r"<[^>]+>", " ", raw_html)
    clean = html.unescape(clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean, img_url


def translate_vi_to_ko(text: str) -> str:
    if not text:
        return ""
    try:
        q = urllib.parse.quote(text[:450])
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=vi&tl=ko&dt=t&q={q}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        translated = "".join(seg[0] for seg in data[0] if seg and seg[0])
        return translated.strip()
    except Exception:
        return text


def fetch_vietnam_news(limit_per_feed: int = 6) -> dict:
    articles = []
    seen_links = set()

    for feed in RSS_SOURCES:
        try:
            req = urllib.request.Request(
                feed["url"],
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                xml_bytes = resp.read()
            root = ET.fromstring(xml_bytes)
            items = root.findall(".//item")[:limit_per_feed]

            for item in items:
                link = (item.findtext("link") or "").strip()
                if not link or link in seen_links:
                    continue
                seen_links.add(link)

                title_vi = html.unescape((item.findtext("title") or "").strip())
                desc_raw = item.findtext("description") or ""
                summary_vi, img_url = strip_html_and_extract_img(desc_raw)
                pub_raw = (item.findtext("pubDate") or "").strip()

                try:
                    dt = parsedate_to_datetime(pub_raw)
                    pub_formatted = dt.strftime("%Y-%m-%d %H:%M")
                    timestamp = dt.timestamp()
                except Exception:
                    pub_formatted = pub_raw or datetime.now().strftime("%Y-%m-%d %H:%M")
                    timestamp = datetime.now().timestamp()

                title_ko = translate_vi_to_ko(title_vi)
                summary_ko = translate_vi_to_ko(summary_vi) if summary_vi else title_ko

                is_hanoi = any(
                    kw in (title_vi + " " + summary_vi).lower()
                    for kw in ["hà nội", "ha noi", "thủ đô"]
                )

                articles.append(
                    {
                        "title_vi": title_vi,
                        "title_ko": title_ko,
                        "summary_vi": summary_vi,
                        "summary_ko": summary_ko,
                        "link": link,
                        "image": img_url,
                        "source": feed["source"],
                        "category": "hanoi" if is_hanoi else feed["category"],
                        "category_ko": "하노이·로컬" if is_hanoi else feed["category_ko"],
                        "published_at": pub_formatted,
                        "timestamp": timestamp,
                    }
                )
        except Exception as e:
            print(f"[WARN] Failed to fetch {feed['url']}: {e}")

    articles.sort(key=lambda x: x["timestamp"], reverse=True)

    mcp_client = GeminiMCPClient()
    mcp_status = mcp_client.get_status()

    # Try Gemini MCP live briefing first; fallback to automatic smart briefing if API quota is exhausted
    top_titles = "\n".join(
        f"- [{a['category_ko']}] {a['title_ko']} ({a['title_vi']})"
        for a in articles[:8]
    )
    mcp_res = mcp_client.summarize_with_gemini(
        f"다음 베트남 오늘 최신 뉴스 헤드라인들을 바탕으로 한국어로 핵심 브리핑 3가지를 요약해줘:\n{top_titles}"
    )

    if mcp_res.get("ok") and mcp_res.get("text"):
        briefing = {
            "mode": "gemini_mcp_live",
            "summary": mcp_res["text"],
            "highlights": [a["title_ko"] for a in articles[:3]],
        }
    else:
        briefing = {
            "mode": "mcp_hybrid_fallback",
            "mcp_note": mcp_res.get("error", ""),
            "summary": (
                f"오늘 수집된 베트남 주요 언론(VnExpress, Tuổi Trẻ)의 최신 기사 {len(articles)}건을 분석한 결과입니다. "
                "경제·비즈니스, 사회·하노이 로컬, IT·과학 분야의 실시간 헤드라인과 한국어 번역 요약이 제공됩니다."
            ),
            "highlights": [a["title_ko"] for a in articles[:4]],
        }

    return {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_count": len(articles),
        "mcp_status": mcp_status,
        "briefing": briefing,
        "articles": articles,
    }


if __name__ == "__main__":
    data = fetch_vietnam_news(limit_per_feed=3)
    print(f"Fetched {data['total_count']} articles. MCP connected: {data['mcp_status'].get('connected')}")
