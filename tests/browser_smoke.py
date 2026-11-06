# -*- coding: utf-8 -*-
"""在 GitHub Actions 中执行的中文网页浏览器冒烟验收。"""
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

BASE = os.environ.get("SHOPPING_SITE_URL", "http://127.0.0.1:8765/")
opts = webdriver.ChromeOptions()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1366,900")

driver = webdriver.Chrome(options=opts)
try:
    wait = WebDriverWait(driver, 20)
    driver.get(BASE)
    wait.until(lambda d: d.find_element(By.ID, "term"))
    assert "智能购物决策系统" in driver.title, driver.title
    for label in ("京东", "淘宝", "拼多多", "闲鱼", "1688", "盼之代售"):
        assert label in driver.page_source, f"缺少平台：{label}"

    driver.find_element(By.ID, "term").send_keys("百元带麦游戏耳机")
    driver.find_element(By.ID, "budget").send_keys("100")
    driver.find_element(By.ID, "toggle-form").click()
    wait.until(lambda d: d.find_element(By.ID, "candidate-form").is_displayed())

    selector = Select(driver.find_element(By.ID, "f-platform"))
    selector.select_by_value("wholesale")
    assert driver.find_element(By.ID, "wholesale-fields").is_displayed(), "1688 专项字段未显示"
    selector.select_by_value("pzds")
    assert driver.find_element(By.ID, "account-fields").is_displayed(), "盼之专用字段未显示"
    selector.select_by_value("jd")

    form = driver.find_element(By.ID, "candidate-form")
    fields = {"title": "测试耳机A", "url": "https://item.jd.com/123456.html", "price": "88",
              "shipping": "0", "fees": "0", "discount": "0"}
    for name, val in fields.items():
        form.find_element(By.CSS_SELECTOR, f'[name="{name}"]').send_keys(val)
    for name in ("skuChecked", "priceChecked", "costChecked"):
        form.find_element(By.CSS_SELECTOR, f'[name="{name}"]').click()
    form.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    wait.until(lambda d: "测试耳机A" in d.find_element(By.ID, "candidates-list").text)
    assert "测试耳机A" in driver.find_element(By.ID, "candidates-list").text
    driver.refresh()
    wait.until(lambda d: "测试耳机A" in d.find_element(By.ID, "candidates-list").text)
    print("通过：中文页面、六平台、1688/盼之专项字段、商品录入和刷新后保留")
finally:
    driver.quit()
