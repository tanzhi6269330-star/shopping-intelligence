# -*- coding: utf-8 -*-
"""单页匿名真实浏览器探测：仅对没有出现安全验证的公开网页试验。
不登录、不输入验证码、不翻页、不无限重试、不输出未核实价格。
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from public_probe import PLATFORMS, robots_check, host_allowed, analyze_html

TARGETS = ("闲鱼","盼之代售")  # 1688 在HTTP探测已出现风控，禁止自动重试。

def inspect(driver, name, config):
    result = {"平台":name,"入口":config["entry"],
              "采集时间_UTC":datetime.now(timezone.utc).isoformat(),
              "结果":"未开始","可推荐":False,"到手价":None}
    robots, allowed = robots_check(config["entry"],config["hosts"])
    result["robots检查"]=robots
    if not allowed:
        result["结果"]="robots或网络限制，未启动页面访问"
        return result
    try:
        driver.get(config["entry"])
        # 只读取一次动态加载后的公开页面；不尝试登录、验证码或继续翻页。
        WebDriverWait(driver,8).until(lambda d: d.execute_script("return document.readyState") in ("interactive","complete"))
        driver.implicitly_wait(2)
        result["最终地址"]=driver.current_url[:500]
        p=urlparse(driver.current_url)
        if p.scheme!="https" or not host_allowed(p.hostname,config["hosts"]):
            result["结果"]="页面跳转到非授权域名，终止"
            return result
        info=analyze_html(driver.page_source.encode("utf-8")[:250000],driver.current_url,config)
        result.update(info)
        if info["检测到风控文案"]:
            result["结果"]="遇到安全验证，停止"
        elif info["发现详情链接数"]:
            result["结果"]="浏览器发现详情链接（未经价格核验）"
        else:
            result["结果"]="浏览器无可用详情链接（可能需要登录或动态接口）"
    except Exception as e:
        result["结果"]="浏览器访问失败"
        result["异常类型"]=type(e).__name__
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="output/公开浏览器补充实验.json")
    args=parser.parse_args()
    options=webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,850")
    options.page_load_strategy="eager"
    results=[]
    browser=webdriver.Chrome(options=options)
    browser.set_page_load_timeout(15)
    try:
        for name in TARGETS:
            result=inspect(browser,name,PLATFORMS[name])
            results.append(result)
            print(f"{name}｜{result['结果']}｜详情链接 {result.get('发现详情链接数',0)}")
    finally:
        browser.quit()
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({
        "说明":"真实匿名浏览器单页实测，禁止将候选链接当成已核实商品或最低价",
        "实验时间_UTC":datetime.now(timezone.utc).isoformat(),
        "结果":results,
    },ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"结果保存至 {path}")
if __name__=="__main__":
    main()
