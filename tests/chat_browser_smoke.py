# -*- coding: utf-8 -*-
"""对话购物首页真实浏览器验收，不依赖真实电商商品抓取。"""
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

URL=os.environ.get("SHOPPING_SITE_URL","http://127.0.0.1:8765/")
options=webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1320,950")
driver=webdriver.Chrome(options=options)
wait=WebDriverWait(driver,16)

def send(text):
    field=driver.find_element(By.ID,"message")
    field.send_keys(text)
    driver.find_element(By.CSS_SELECTOR,'#chat-form button[type="submit"]').click()
    wait.until(lambda d: text in d.find_element(By.ID,"history").text)
    return driver.find_element(By.ID,"constraints").text

try:
    driver.get(URL)
    wait.until(lambda d:d.find_element(By.ID,"chat-form").is_displayed())
    title=driver.title
    assert "购物" in title,title

    a=send("帮我找100元以内带麦克风的游戏耳机")
    assert "¥100" in a,a
    assert "需要" in a,a
    assert "游戏" in a,a
    assert "HyperX" in driver.find_element(By.ID,"picks").text
    assert "RTINGS" in driver.find_element(By.ID,"picks").text
    assert "国内" in driver.find_element(By.ID,"picks").text

    b=send("再便宜点")
    assert "¥80" in b,b
    c=send("不要二手")
    assert "排除" in c,c
    assert "¥80" in c,c
    assert "耳机" in c,c

    d=send("只要无线")
    assert "无线" in d,d
    assert "没有符合" in driver.find_element(By.ID,"picks").text

    driver.refresh()
    wait.until(lambda d:"¥80" in d.find_element(By.ID,"constraints").text)
    assert "排除" in driver.find_element(By.ID,"constraints").text
    assert "只要无线" in driver.find_element(By.ID,"history").text
    assert len(driver.find_elements(By.CSS_SELECTOR,"#links a"))>=1
    print("PASS: 中文对话、来源推荐、预算继承、二手排除、无线过滤、刷新持久化")
finally:
    driver.quit()
