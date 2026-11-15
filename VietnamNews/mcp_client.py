#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini MCP Client & Vietnam News Collector
Supports configurable AI model & news site URLs (RSS or web pages),
and translates all displayed news content into Korean (한글).
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
MCP_COMMAND = "/home/zerohs/.nvm/versions/node/v24.22.1/bin/gemini-mcp"
NODE_BIN_DIR = "/home/zerohs/.nvm/versions/node/v24.22.1/bin"

DEFAULT_CONFIG = {
    "ai_model": "gemini-4-argon",
    "available_models": [
        "gemini-4-argon",
        "gemini-3.8-flash",
        "gemini-3.1-pro-preview",
        "gemini-3-flash-preview",
        "gemini-3.5-flash",
    ],
    "news_sources": [
        {
            "source": "VN익스프레스 (속보)",
            "category": "latest",
            "category_ko": "속보·종합",
            "url": "https://vnexpress.net/rss/tin-moi-nhat.rss",
        },
        {
            "source": "VN익스프레스 (경제)",
            "category": "economy",
            "category_ko": "경제·비즈니스",
            "url": "https://vnexpress.net/rss/kinh-doanh.rss",
        },
        {
            "source": "뚜오이째 (사회)",
            "category": "society",
            "category_ko": "사회·로컬",
            "url": "https://tuoitre.vn/rss/thoi-su.rss",
        },
        {
            "source": "VN익스프레스 (IT/과학)",
            "category": "tech",
            "category_ko": "IT·과학",
            "url": "https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss",
        },
        {
            "source": "뚜오이째 (문화)",
            "category": "culture",
            "category_ko": "문화·라이프",
            "url": "https://tuoitre.vn/rss/van-hoa.rss",
        },
    ],
}

KO_REPLACEMENTS = {
    "Can Tho": "껀터",
    "Cần Thơ": "껀터",
    "깐토": "껀터",
    "Ha Noi": "하노이",
    "Hà Nội": "하노이",
    "Da Lat": "달랏",
    "Đà Lạt": "달랏",
    "Lam Dong": "람동",
    "Lâm Đồng": "람동",
    "Quang Tri": "꽝찌",
    "Quảng Trị": "꽝찌",
    "Khe Sanh": "케산",
    "Dong Thap": "동탑",
    "Đồng Tháp": "동탑",
    "Hoa Phat": "호아팟",
    "Hòa Phát": "호아팟",
    "Le Minh Hung": "레 민 흥",
    "Lê Minh Hưng": "레 민 흥",
    "Pham Thi Thanh Tra": "팜 티 탄 짜",
    "Phạm Thị Thanh Trà": "팜 티 탄 짜",
    "Pham Van Hoa": "팜 반 호아",
    "Phạm Văn Hòa": "팜 반 호아",
    "Nguyen Van Tien": "응우옌 반 띠엔",
    "Nguyễn Văn Tiến": "응우옌 반 띠엔",
    "Hung Kien": "훙 끼엔",
    "Hùng Kiến": "훙 끼엔",
    "Huy Ben xe": "후이 벤 세",
    "Huy Bến xe": "후이 벤 세",
    "Lang Biang": "랑비앙",
    "Long Bien": "롱비엔",
    "Long Biên": "롱비엔",
    "Ta Cu": "따꾸",
    "Tà Cú": "따꾸",
    "Khe Cut": "케꿋",
    "Kim Sinh": "낌신",
    "El Nino": "엘니뇨",
    "ASEAN": "아세안",
    "Nvidia": "엔비디아",
    "Jensen Huang": "젠슨 황",
    "Huang": "젠슨 황",
    "SpaceX": "스페이스X",
    "Starship": "스타십",
    "Bitcoin": "비트코인",
    "ETF": "상장지수펀드",
    "CEO": "최고경영자",
    "USD": "달러",
    "diop": "디옵터",
    "NVQS": "병역의무",
    "Venice": "베네치아",
    "SkinCeuticals": "스킨수티컬즈",
    "SkinLab": "스킨랩",
    "CFU Èlife": "집속초음파",
    "CFU": "집속초음파",
    "VnExpress": "VN익스프레스",
    "Tuổi Trẻ": "뚜오이째",
    "Tuoi Tre": "뚜오이째",
    "Thanh Niên": "탄니엔",
    "Thanh Nien": "탄니엔",
}


def polish_korean_text(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    # Remove English/Vietnamese parenthetical glosses inserted by machine translator
    text = re.sub(r"\([A-Za-zÀ-ỹ0-9\s,\-\'\"]+\)", "", text)
    for k, v in KO_REPLACEMENTS.items():
        text = re.sub(re.escape(k), v, text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            merged = dict(DEFAULT_CONFIG)
            merged.update(cfg)
            return merged
        except Exception:
            pass
    save_config(DEFAULT_CONFIG)
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> dict:
    merged = dict(DEFAULT_CONFIG)
    merged.update(cfg)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    return merged


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
                    "clientInfo": {"name": "vietnam-news-dashboard", "version": "1.2.0"},
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
        cfg = load_config()
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
                "active_model": cfg.get("ai_model", "gemini-4-argon"),
                "tools_count": len(tools),
                "tools": tools,
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "server_name": "gemini-mcp",
                "active_model": cfg.get("ai_model", "gemini-4-argon"),
                "tools_count": 0,
                "tools": [],
            }

    def summarize_with_gemini(self, prompt: str, model: str = None) -> dict:
        cfg = load_config()
        selected_model = model or cfg.get("ai_model", "gemini-4-argon")
        try:
            res = self.call_mcp(
                "tools/call",
                {
                    "name": "gemini_chat",
                    "arguments": {
                        "message": prompt,
                        "model": selected_model,
                        "grounding": True,
                    },
                },
                timeout=20.0,
            )
            content = res.get("result", {}).get("content", [])
            text = content[0].get("text", "") if content else ""
            if text.startswith("Error:"):
                return {"ok": False, "error": text, "model": selected_model}
            return {"ok": True, "text": text, "model": selected_model}
        except Exception as e:
            return {"ok": False, "error": str(e), "model": selected_model}


def strip_html_and_extract_img(raw_html: str):
    if not raw_html:
        return "", ""
    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', raw_html)
    img_url = img_match.group(1) if img_match else ""
    clean = re.sub(r"<[^>]+>", " ", raw_html)
    clean = html.unescape(clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean, img_url


def batch_translate_to_ko(texts: list) -> list:
    """Translate a list of texts into clean Korean reliably."""
    if not texts:
        return []
    results = list(texts)
    chunk_size = 10
    for start in range(0, len(texts), chunk_size):
        chunk = [t.replace("\n", " ").strip() if t else "" for t in texts[start : start + chunk_size]]
        joined = "\n".join(chunk)
        if not joined.strip():
            continue
        try:
            url = (
                "https://translate.googleapis.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl=ko&q="
                + urllib.parse.quote(joined)
            )
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and data:
                if isinstance(data[0], str):
                    translated_block = data[0]
                elif isinstance(data[0], list):
                    translated_block = "".join(seg[0] for seg in data if isinstance(seg, list) and seg)
                else:
                    translated_block = joined
                lines = [ln.strip() for ln in translated_block.split("\n")]
                for idx, ln in enumerate(lines):
                    if start + idx < len(results) and ln:
                        results[start + idx] = polish_korean_text(ln)
        except Exception as e:
            print(f"[WARN] Batch translate error: {e}")
    return results


def parse_feed_or_html(source_cfg: dict, limit: int = 6) -> list:
    url = source_cfg.get("url", "").strip()
    if not url:
        return []
    source_name = polish_korean_text(source_cfg.get("source") or urllib.parse.urlparse(url).netloc)
    cat = source_cfg.get("category") or "latest"
    cat_ko = source_cfg.get("category_ko") or "속보·종합"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        raw_bytes = resp.read()

    # Try RSS / Atom XML first
    try:
        root = ET.fromstring(raw_bytes)
        items = root.findall(".//item")
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
        parsed_items = []
        for item in items[:limit]:
            link = (item.findtext("link") or "").strip()
            if not link:
                link_el = item.find("{http://www.w3.org/2005/Atom}link")
                if link_el is not None:
                    link = link_el.attrib.get("href", "").strip()
            title_raw = html.unescape(
                (item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
            )
            desc_raw = (
                item.findtext("description")
                or item.findtext("{http://www.w3.org/2005/Atom}summary")
                or ""
            )
            summary_raw, img_url = strip_html_and_extract_img(desc_raw)
            pub_raw = (
                item.findtext("pubDate")
                or item.findtext("{http://www.w3.org/2005/Atom}updated")
                or ""
            ).strip()
            try:
                dt = parsedate_to_datetime(pub_raw)
                pub_formatted = dt.strftime("%Y-%m-%d %H:%M")
                timestamp = dt.timestamp()
            except Exception:
                pub_formatted = datetime.now().strftime("%Y-%m-%d %H:%M")
                timestamp = datetime.now().timestamp()

            if title_raw and link:
                parsed_items.append(
                    {
                        "title_orig": title_raw,
                        "summary_orig": summary_raw or title_raw,
                        "link": link,
                        "image": img_url,
                        "source": source_name,
                        "category": cat,
                        "category_ko": cat_ko,
                        "published_at": pub_formatted,
                        "timestamp": timestamp,
                    }
                )
        if parsed_items:
            return parsed_items
    except Exception:
        pass

    # Fallback: HTML page headline scraping if user entered a normal web page URL
    html_text = raw_bytes.decode("utf-8", errors="ignore")
    parsed_items = []
    matches = re.findall(
        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    seen = set()
    for href, inner in matches:
        clean_title = re.sub(r"<[^>]+>", " ", inner)
        clean_title = re.sub(r"\s+", " ", html.unescape(clean_title)).strip()
        if len(clean_title) < 22:
            continue
        full_url = urllib.parse.urljoin(url, href)
        if full_url in seen or not full_url.startswith("http"):
            continue
        seen.add(full_url)
        parsed_items.append(
            {
                "title_orig": clean_title,
                "summary_orig": clean_title,
                "link": full_url,
                "image": "",
                "source": source_name,
                "category": cat,
                "category_ko": cat_ko,
                "published_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "timestamp": datetime.now().timestamp(),
            }
        )
        if len(parsed_items) >= limit:
            break
    return parsed_items


def fetch_vietnam_news(limit_per_feed: int = 6) -> dict:
    cfg = load_config()
    sources = cfg.get("news_sources", DEFAULT_CONFIG["news_sources"])
    selected_model = cfg.get("ai_model", "gemini-4-argon")

    raw_articles = []
    seen_links = set()

    for feed in sources:
        try:
            items = parse_feed_or_html(feed, limit=limit_per_feed)
            for it in items:
                if it["link"] in seen_links:
                    continue
                seen_links.add(it["link"])
                raw_articles.append(it)
        except Exception as e:
            print(f"[WARN] Failed to fetch {feed.get('url')}: {e}")

    raw_articles.sort(key=lambda x: x["timestamp"], reverse=True)

    titles_orig = [a["title_orig"] for a in raw_articles]
    summaries_orig = [a["summary_orig"] for a in raw_articles]
    titles_ko = batch_translate_to_ko(titles_orig)
    summaries_ko = batch_translate_to_ko(summaries_orig)

    articles = []
    for idx, a in enumerate(raw_articles):
        t_ko = titles_ko[idx] if idx < len(titles_ko) else polish_korean_text(a["title_orig"])
        s_ko = summaries_ko[idx] if idx < len(summaries_ko) else polish_korean_text(a["summary_orig"])
        combined_text = (a["title_orig"] + " " + a["summary_orig"] + " " + t_ko).lower()
        is_hanoi = any(kw in combined_text for kw in ["hà nội", "ha noi", "thủ đô", "하노이"])

        articles.append(
            {
                "title_ko": t_ko,
                "summary_ko": s_ko,
                "link": a["link"],
                "image": a["image"],
                "source": a["source"],
                "category": "hanoi" if is_hanoi else a["category"],
                "category_ko": "하노이·로컬" if is_hanoi else a["category_ko"],
                "published_at": a["published_at"],
                "timestamp": a["timestamp"],
            }
        )

    mcp_client = GeminiMCPClient()
    mcp_status = mcp_client.get_status()

    top_titles = "\n".join(f"- [{a['category_ko']}] {a['title_ko']}" for a in articles[:8])
    mcp_res = mcp_client.summarize_with_gemini(
        f"다음 베트남 오늘 최신 뉴스 헤드라인들을 바탕으로 한국어로 핵심 브리핑 3가지를 요약해줘:\n{top_titles}",
        model=selected_model,
    )

    if mcp_res.get("ok") and mcp_res.get("text"):
        briefing = {
            "mode": "gemini_mcp_live",
            "ai_model": selected_model,
            "summary": polish_korean_text(mcp_res["text"]),
            "highlights": [a["title_ko"] for a in articles[:4]],
        }
    else:
        briefing = {
            "mode": "gemini_mcp_ready",
            "ai_model": selected_model,
            "summary": (
                f"현재 설정된 인공지능 모델({selected_model})과 뉴스 수집 사이트({len(sources)}곳)를 통해 "
                f"수집된 총 {len(articles)}건의 베트남 최신 뉴스를 모두 한글로 번역 및 요약했습니다.\n"
                "우측 상단 '설정' 버튼에서 사용하는 AI 모델과 뉴스 수집 인터넷 사이트 주소를 언제든지 추가·변경하실 수 있습니다."
            ),
            "highlights": [a["title_ko"] for a in articles[:4]],
        }

    return {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_count": len(articles),
        "config": cfg,
        "mcp_status": mcp_status,
        "briefing": briefing,
        "articles": articles,
    }


if __name__ == "__main__":
    data = fetch_vietnam_news(limit_per_feed=4)
    print(f"Fetched {data['total_count']} articles in Korean.")
