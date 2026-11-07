#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按明确给出的盼之商品编号读取公开详情；不进行搜索扫描/登录/风控绕过。"""
from __future__ import annotations
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

CODE = os.environ.get("PZDS_CODE", "C8PVQM").strip().upper()
GAME = os.environ.get("PZDS_GAME", "6").strip()
assert re.fullmatch(r"[A-Z0-9]{4,12}", CODE)
assert re.fullmatch(r"[0-9]{1,4}", GAME)
DOMAIN = "www.pzds.com"
URL = f"https://{DOMAIN}/goodsDetails/{CODE}/{GAME}"
UA = "ShoppingIntelligenceResearch/0.1 (+single public listing evidence check)"
TIMEOUT = 12

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]
        self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ("script","style"):
            self.skip+=1
    def handle_endtag(self,tag):
        if tag in ("script","style"):
            self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())

def fetch(url):
    parsed=urlparse(url)
    if parsed.scheme!="https" or parsed.hostname!=DOMAIN:
        raise ValueError("refuse external or non-HTTPS URL")
    r=Request(url,headers={"User-Agent":UA,"Accept":"text/html,*/*"})
    with urlopen(r,timeout=TIMEOUT) as f:
        final=urlparse(f.geturl())
        if final.scheme!="https" or final.hostname!=DOMAIN:
            raise ValueError("unexpected redirect")
        return f.status, f.read(350000).decode("utf-8",errors="replace")

def robots_allowed():
    robot_url=f"https://{DOMAIN}/robots.txt"
    try:
        status,txt=fetch(robot_url)
        if status!=200:return False, f"robots HTTP {status}"
        p=RobotFileParser()
        p.parse(txt.splitlines())
        allowed=p.can_fetch(UA,URL)
        return allowed,"robots allow" if allowed else "robots disallow"
    except HTTPError as e:
        if e.code==404:return True,"robots not found"
        return False,f"robots HTTP {e.code}"
    except Exception as e:
        return False, f"robots inaccessible: {type(e).__name__}"

def assess(text):
    parser=TextExtractor()
    parser.feed(text)
    visible=" ".join(parser.parts)
    index=visible.find(CODE)
    around=visible[max(0,index-250):index+1100] if index>=0 else visible[:700]
    # 只提取公开商品价；不存用户名/手机号/其他私密字段。
    price_candidates = re.findall(r"(?<![A-Za-z0-9])(?:¥|￥)\s*([0-9]{1,8}(?:\.[0-9]{1,2})?)",visible[:10000])
    blocked=bool(re.search(r"安全验证|验证码|访问频繁|captcha|滑块验证|verify you are human",visible,re.I))
    return {"编号是否出现在可见页面": CODE in visible,
            "检测到安全验证":blocked,
            "页面可见价格候选": price_candidates[:8],
            "内容摘要":around[:1100],
            "可见字符数":len(visible)}

def main():
    result={"商品编号":CODE,"页面":URL,"探测时间_UTC":datetime.now(timezone.utc).isoformat(),
            "是否核实为真实上架":False,"状态":"未开始"}
    ok,desc=robots_allowed()
    result["访问规则"]=desc
    if not ok:
        result["状态"]="未访问：平台访问规则无法确认或不允许"
    else:
        try:
            code,body=fetch(URL)
            result["HTTP状态"]=code
            result["HTTP提取"]=assess(body)
            result["状态"]="公开HTTP页面可读，尚未确认当前上架" if code==200 else f"HTTP {code}"
        except HTTPError as e:
            result["状态"]=f"HTTP {e.code}"
        except Exception as e:
            result["状态"]=f"HTTP访问失败：{type(e).__name__}"
        # 真实浏览器单次访问，仅在未触发安全验证时继续
        if result.get("HTTP提取",{}).get("检测到安全验证"):
            result["浏览器状态"]="跳过：HTTP已出现安全验证"
        else:
            try:
                from selenium import webdriver
                options=webdriver.ChromeOptions()
                options.add_argument("--headless=new")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--window-size=1400,1000")
                options.page_load_strategy="eager"
                browser=webdriver.Chrome(options=options)
                try:
                    browser.set_page_load_timeout(20)
                    browser.get(URL)
                    browser.implicitly_wait(3)
                    final=urlparse(browser.current_url)
                    if final.scheme!="https" or final.hostname!=DOMAIN:
                        result["浏览器状态"]="页面跳转到非指定域名，不读取"
                    else:
                        result["浏览器状态"]="已访问指定详情页"
                        result["浏览器提取"]=assess(browser.page_source[:350000])
                finally:
                    browser.quit()
            except Exception as e:
                result["浏览器状态"]=f"浏览器访问失败：{type(e).__name__}"
    for mode in ("浏览器提取","HTTP提取"):
        d=result.get(mode,{})
        if d.get("编号是否出现在可见页面") and d.get("页面可见价格候选") and not d.get("检测到安全验证"):
            result["候选判断"]="看到了编号和价格文案，仍需判断是否为当前在售报价"
            break
    else:
        result["候选判断"]="未确认编号与当前在售价格"
    out=Path("output/pzds_exact_listing.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
