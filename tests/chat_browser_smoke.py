# -*- coding: utf-8 -*-
"""GitHub Actions Chrome验收：自由聊天→关键追问→继承条件→来源候选→刷新保留。"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

BASE = os.environ.get("SHOPPING_SITE_URL","http://127.0.0.1:8765/")
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1380,900")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver,20)

def send(text):
    box=wait.until(lambda d:d.find_element(By.ID,"prompt"))
    box.send_keys(text)
    driver.find_element(By.ID,"send").click()
    wait.until(lambda d: any(text in n.text for n in d.find_elements(By.CSS_SELECTOR,".message.user")))
    time.sleep(0.2)
def latest_answer():
    return driver.find_elements(By.CSS_SELECTOR,".message.assistant")[-1].text

try:
    driver.get(BASE)
    wait.until(lambda d:d.find_element(By.ID,"prompt"))
    assert "对话式选购" in driver.title or "对话式" in driver.page_source
    send("帮我找100元以内带麦的游戏耳机")
    wait.until(lambda d:"有线还是无线" in latest_answer())
    assert "100元" in driver.find_element(By.ID,"summary").text
    send("有线")
    wait.until(lambda d:len(d.find_elements(By.CSS_SELECTOR,".candidate"))>0)
    cards=driver.find_elements(By.CSS_SELECTOR,".candidate")
    assert 1<=len(cards)<=3
    assert all("来源：" in c.text for c in cards)
    assert all("非实时售价" in c.text or "实时价格未知" in c.text or "非实时" in c.text for c in cards)
    send("再便宜点")
    wait.until(lambda d:"降到多少" in latest_answer())
    assert "100元" in driver.find_element(By.ID,"summary").text
    send("80元以内")
    wait.until(lambda d:"80元" in driver.find_element(By.ID,"summary").text)
    send("不要漫步者")
    wait.until(lambda d:"不要漫步者" in driver.find_elements(By.CSS_SELECTOR,".message.user")[-1].text)
    assert all("漫步者" not in c.text for c in driver.find_elements(By.CSS_SELECTOR,".message.assistant")[-1].find_elements(By.CSS_SELECTOR,".candidate"))
    driver.refresh()
    wait.until(lambda d:"80元" in d.find_element(By.ID,"summary").text)
    assert len(driver.find_elements(By.CSS_SELECTOR,".message.user"))>=5
    assert len(driver.find_elements(By.CSS_SELECTOR,".message.assistant"))>=5
    links=driver.find_elements(By.CSS_SELECTOR,".message a[href]")
    assert links and all(a.get_attribute("href").startswith("https://") for a in links)
    print("通过：聊天追问、预算继承、降价提问、品牌排除、来源展示、刷新保留")
finally:
    driver.quit()
