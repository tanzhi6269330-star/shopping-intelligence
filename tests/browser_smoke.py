# -*- coding: utf-8 -*-
"""购物对话页面基础冒烟测试；详细追问由 chat_browser_smoke.py 检验。"""
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
opts=webdriver.ChromeOptions()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
driver=webdriver.Chrome(options=opts)
try:
    driver.get(os.environ.get("SHOPPING_SITE_URL","http://127.0.0.1:8765/"))
    wait=WebDriverWait(driver,20)
    wait.until(lambda d:d.find_element(By.ID,"prompt"))
    assert "对话式选购" in driver.title
    driver.find_element(By.ID,"prompt").send_keys("帮我买100元以内带麦的游戏耳机")
    driver.find_element(By.ID,"send").click()
    wait.until(lambda d: "100元" in d.find_element(By.ID,"summary").text)
    assert len(driver.find_elements(By.CSS_SELECTOR,".message.user"))==1
    assert len(driver.find_elements(By.CSS_SELECTOR,".message.assistant"))==1
    driver.refresh()
    wait.until(lambda d: "100元" in d.find_element(By.ID,"summary").text)
    assert driver.find_elements(By.CSS_SELECTOR,".message.user")
    print("通过：在线中文聊天入口、条件显示、消息记录持久化")
finally:
    driver.quit()
