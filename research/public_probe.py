#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""免费公开网页采集可行性试验（仅一页/平台，不登录、不绕过风控）。
输出为测试证据，不能当成已核实商品报价。
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

UA = "ShoppingIntelligenceResearch/0.1 (+public single-page feasibility check)"
MAX_BYTES = 250_000
MAX_REDIRECTS = 2
PLATFORMS = {
    "1688": {
        "hosts": ("1688.com",),
        "entry": "https://s.1688.com/selloffer/offer_search.htm?keywords=" + quote("耳机".encode("gbk")),
        "mode": "关键词搜索页",
        "item_pattern": r"/offer/\d+\.html",
    },
    "闲鱼": {
        "hosts": ("goofish.com",),
        "entry": "https://www.goofish.com/search?q=" + quote("耳机"),
        "mode": "关键词搜索页",
        "item_pattern": r"/item\?[^#]*\bid=\d+",
    },
    "盼之代售": {
        "hosts": ("pzds.com",),
        "entry": "https://www.pzds.com/selectGame?buyType=RECOVERY",
        "mode": "公开游戏目录（非关键词搜索）",
        "item_pattern": r"/(?:goods|product|detail|trade|item)/[A-Za-z0-9/?=&_-]+",
    },
}

def host_allowed(host: str, roots: tuple[str, ...]) -> bool:
    host = (host or "").lower().rstrip(".")
    return any(host == h or host.endswith("." + h) for h in roots)

class LimitedRedirect(HTTPRedirectHandler):
    def __init__(self, roots):
        super().__init__()
        self.roots = roots
        self.count = 0
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.count += 1
        parsed = urlparse(newurl)
        if self.count > MAX_REDIRECTS or parsed.scheme != "https" or not host_allowed(parsed.hostname, self.roots):
            raise ValueError("重定向超出平台许可域名或跳转次数限制")
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def limited_get(url: str, roots: tuple[str, ...]) -> tuple[int, str, bytes, str]:
    p = urlparse(url)
    if p.scheme != "https" or not host_allowed(p.hostname, roots) or p.username or p.password:
        raise ValueError("拒绝非HTTPS或非平台域名")
    opener = build_opener(LimitedRedirect(roots))
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.3"})
    try:
        with opener.open(req, timeout=12) as resp:
            end = resp.geturl()
            ep = urlparse(end)
            if ep.scheme != "https" or not host_allowed(ep.hostname, roots):
                raise ValueError("最终跳转目标不合法")
            data = resp.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                data = data[:MAX_BYTES]
            return resp.status, end, data, resp.headers.get("Content-Type", "")
    except HTTPError as e:
        return e.code, url, b"", ""

def robots_check(url: str, roots: tuple[str, ...]) -> tuple[str, bool]:
    p = urlparse(url)
    robots_url = f"{p.scheme}://{p.netloc}/robots.txt"
    try:
        status, _, body, _ = limited_get(robots_url, roots)
        if status == 404:
            return "未提供robots.txt", True
        if status != 200:
            return f"robots.txt状态{status}，保守停止", False
        parser = RobotFileParser()
        parser.parse(body.decode("utf-8", errors="replace").splitlines())
        allowed = parser.can_fetch(UA, url)
        return ("允许访问" if allowed else "robots.txt禁止访问"), bool(allowed)
    except (OSError, ValueError, URLError) as e:
        return f"robots.txt无法确认，保守停止：{type(e).__name__}", False

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title_active = False
        self.title = ""
        self.links = []
        self.meta = {}
    def handle_starttag(self, tag, attrs):
        at = dict(attrs)
        if tag == "title":
            self.title_active = True
        if tag == "a" and at.get("href"):
            self.links.append(at["href"])
        if tag == "meta":
            key = at.get("property", at.get("name", "")).lower()
            if key and at.get("content"):
                self.meta[key] = at["content"][:240]
    def handle_endtag(self, tag):
        if tag == "title":
            self.title_active = False
    def handle_data(self, data):
        if self.title_active:
            self.title += data[:200]

def analyze_html(data: bytes, origin: str, conf: dict) -> dict:
    doc = data.decode("utf-8", errors="replace")
    parsed = PageParser()
    parsed.feed(doc)
    links = []
    pattern = re.compile(conf["item_pattern"], re.I)
    for href in parsed.links:
        normalized = urljoin(origin, html.unescape(href))
        p = urlparse(normalized)
        if p.scheme == "https" and host_allowed(p.hostname, conf["hosts"]) and pattern.search(normalized):
            if normalized not in links:
                links.append(normalized[:400])
        if len(links) >= 10:
            break
    is_blocked = bool(re.search(r"验证码|滑块验证|访问过于频繁|安全验证|captcha|verify you are human", doc[:150_000], re.I))
    is_login = bool(re.search(r"需要登录|请先登录|登录后查看|login required", doc[:150_000], re.I))
    return {
        "页面标题": (parsed.meta.get("og:title") or parsed.title).strip()[:120],
        "网页字节数": len(data),
        "发现详情链接数": len(links),
        "候选详情链接": links,
        "检测到风控文案": is_blocked,
        "检测到登录限制文案": is_login,
        "有公开结构化商品价格": '"offers"' in doc and '"price"' in doc and '"@type"' in doc,
    }

def run_one(name: str, conf: dict) -> dict:
    result = {"平台": name, "入口类型": conf["mode"], "测试入口": conf["entry"],
              "采集时间_UTC": dt.datetime.now(dt.timezone.utc).isoformat(),
              "结果": "未开始", "价格可验证": False, "实际到手价": None}
    robots_state, can_fetch = robots_check(conf["entry"], conf["hosts"])
    result["robots检查"] = robots_state
    if not can_fetch:
        result["结果"] = "受robots或访问限制，未请求商品页面"
        return result
    try:
        status, final, body, content_type = limited_get(conf["entry"], conf["hosts"])
        result.update({"HTTP状态": status, "最终地址": final, "内容类型": content_type})
        if status in (401,403,429):
            result["结果"] = "平台限制匿名访问"
        elif status >= 400:
            result["结果"] = "网络或HTTP错误"
        elif "html" not in content_type.lower():
            result["结果"] = "非HTML页面，跳过"
        else:
            signals = analyze_html(body, final, conf)
            result.update(signals)
            if signals["检测到风控文案"]:
                result["结果"] = "出现风控验证，立即停止"
            elif signals["发现详情链接数"] > 0:
                result["结果"] = "发现候选链接（尚未核价）"
            else:
                result["结果"] = "网页可读但未取得可核验商品链接"
    except (OSError, ValueError, URLError) as e:
        result["结果"] = "网络访问失败"
        result["异常类型"] = type(e).__name__
    return result

def main():
    ap = argparse.ArgumentParser(description="三平台真实公开网页可行性实验")
    ap.add_argument("--output", default="output/公开网页采集实验.json")
    args = ap.parse_args()
    records = [run_one(name, conf) for name, conf in PLATFORMS.items()]
    result = {"实验性质": "真实访问实验：不得把发现链接或结构化价格提示当成真实到手价",
              "版本": "0.1", "平台数": len(records), "平台结果": records,
              "判定": "只有完整商品详情、SKU、费用、运费和人工核验后才可进入购买推荐"}
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in records:
        print(f"{r['平台']}｜{r['结果']}｜{r.get('robots检查', '')}｜链接 {r.get('发现详情链接数','—')}")
    print(f"已保存：{dest}")
if __name__ == "__main__":
    main()
