#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""王者荣耀公开在售列表单页校准样本：限单页、遵守robots，不登录不绕风控。"""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json,re
from selenium import webdriver
from selenium.webdriver.common.by import By

URL="https://www.pzds.com/goodsList/7/6"
HOST="www.pzds.com"
UA="ShoppingIntelligenceResearch/0.1 (+single public price comparison)"
def check_robots():
    try:
        rq=Request("https://www.pzds.com/robots.txt",headers={"User-Agent":UA})
        with urlopen(rq,timeout=12) as resp:
            raw=resp.read(150000).decode("utf-8",errors="replace")
        rp=RobotFileParser()
        rp.parse(raw.splitlines())
        return rp.can_fetch(UA,URL),"robots allow" if rp.can_fetch(UA,URL) else "robots disallow"
    except HTTPError as e:
        if e.code==404:return True,"robots 404"
        return False,f"robots HTTP {e.code}"
    except Exception as e:return False,f"robots inaccessible ({type(e).__name__})"

def extract(text):
    def group(pattern):
        m=re.search(pattern,text)
        return int(m.group(1)) if m else None
    def price():
        for pattern in [r"[¥￥]\s*([\d,]+)(?![0-9])",r"(?:现价|售价|价格)\s*[¥￥]?\s*([\d,]+)"]:
            m=re.search(pattern,text)
            if m:return int(m.group(1).replace(",",""))
        return None
    region=next((v for v in ["安卓QQ","苹果QQ","安卓微信","苹果微信"] if v in text),None)
    return {"挂牌价":price(),"区服":region,
            "皮肤":group(r"皮肤数量\s*(\d{1,4})"),
            "典藏":group(r"荣耀典藏\s*(\d{1,3})"),
            "无双":group(r"(?:^|\s)无双\s*(\d{1,3})"),
            "珍品无双":group(r"珍品无双\s*(\d{1,3})"),
            "珍品传说":group(r"珍品传说\s*(\d{1,3})"),
            "贵族":group(r"贵族\s*(\d{1,2})"),
            "可二次实名": "可二次实名" in text and "不可二次实名" not in text,
            "疑似国标溢价":bool(re.search(r"国标|省标|万战|小国标|大国标",text))}

def main():
    out={"网址":URL,"采集时间UTC":datetime.now(timezone.utc).isoformat(),"目的":"按一页匿名在售列表构建价格可比样本，不把挂牌价当成交价","样本":[]}
    allowed,reason=check_robots()
    out["robots"]=reason
    if allowed:
        driver=None
        try:
            opts=webdriver.ChromeOptions()
            opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--window-size=1440,1000")
            opts.page_load_strategy="eager"
            driver=webdriver.Chrome(options=opts)
            driver.set_page_load_timeout(20)
            driver.get(URL)
            from time import sleep
            sleep(4)
            cur=urlparse(driver.current_url)
            if cur.scheme!="https" or cur.hostname!=HOST:
                out["状态"]="跳转到其他域名，停止"
            else:
                page=driver.find_element(By.TAG_NAME,"body").text
                if re.search(r"安全验证|验证码|访问过于频繁|滑块验证|captcha",page,re.I):
                    out["状态"]="出现平台验证，停止"
                else:
                    anchors=driver.find_elements(By.CSS_SELECTOR,"a[href*='goodsDetails']")
                    ids=set()
                    for a in anchors:
                        href=a.get_attribute("href") or ""
                        found=re.search(r"/goodsDetails/([A-Za-z0-9]{4,12})/6",href)
                        if not found or found.group(1) in ids:continue
                        ids.add(found.group(1))
                        piece=""
                        element=a
                        for _ in range(5):
                            try:
                                txt=element.text
                                if "皮肤数量" in txt and ("¥" in txt or "￥" in txt) and len(txt)<2000:
                                    piece=txt
                                    break
                                element=element.find_element(By.XPATH,"..")
                            except Exception:break
                        if not piece:
                            piece=a.text
                        values=extract(piece)
                        out["样本"].append({"编号":found.group(1),"链接":href.split("?")[0],
                            **values,"原始简要文本":piece[:340]})
                        if len(out["样本"])>=80:break
                    out["状态"]="完成单页采样"
                    out["页面详情链接数"]=len(anchors)
                    out["样本数"]=len(out["样本"])
                    out["页面文本预览"]=page[:1400] if len(out["样本"])<2 else ""
        except Exception as e:out["状态"]=f"访问异常 {type(e).__name__}"
        finally:
            if driver:driver.quit()
    else:out["状态"]="平台访问规则未允许，未访问"
    path=Path("output/pzds_market_sample.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf8")
    print("市场样本摘要:",json.dumps({k:v for k,v in out.items() if k not in ("样本","页面文本预览")},ensure_ascii=False))
    print("页面预览:",out.get("页面文本预览","")[:600])
    for row in out["样本"][:80]:
        print(json.dumps({k:v for k,v in row.items() if k!="原始简要文本"},ensure_ascii=False))
if __name__=="__main__":main()
