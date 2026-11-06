# -*- coding: utf-8 -*-
"""对话式购物系统：真实 Chrome 浏览器测试。"""
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

base = os.environ.get("SHOPPING_SITE_URL", "http://127.0.0.1:8765/")
opts = webdriver.ChromeOptions()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1350,900")
driver = webdriver.Chrome(options=opts)
try:
    wait = WebDriverWait(driver, 25)
    driver.get(base)
    box = wait.until(lambda d: d.find_element(By.ID,"chat-input"))
    assert "购物研究助手" in driver.title
    def send(t):
        field = driver.find_element(By.ID,"chat-input")
        field.send_keys(t)
        driver.find_element(By.CSS_SELECTOR, "#chat-form button[type='submit']").click()
    send("帮我挑100元以内的耳机")
    wait.until(lambda d: "100元" in d.find_element(By.ID,"conditions").text)
    assert "耳机" in driver.find_element(By.ID,"conditions").text
    send("再便宜点")
    wait.until(lambda d: "70元" in d.find_element(By.ID,"conditions").text)
    assert "耳机" in driver.find_element(By.ID,"conditions").text
    send("闲鱼二手也可以")
    wait.until(lambda d: "接受二手" in d.find_element(By.ID,"conditions").text)
    send("游戏语音")
    send("无线")
    wait.until(lambda d: "专业评测与横评" in d.find_element(By.ID,"messages").text)
    assert "真实用户" not in driver.find_element(By.ID,"conditions").text
    assert driver.find_elements(By.CSS_SELECTOR,"#messages a[href*='bing.com/search']")
    driver.refresh()
    wait.until(lambda d: "70元" in d.find_element(By.ID,"conditions").text)
    assert "接受二手" in driver.find_element(By.ID,"conditions").text
    assert driver.find_element(By.CSS_SELECTOR,"a[href='./legacy.html']")
    print("通过：对话式首页、多轮预算继承、二手偏好、循证研究入口和刷新后保留。")
finally:
    driver.quit()
