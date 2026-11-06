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
    driver.get(BASE.rstrip("/") + "/classic/")
    wait.until(lambda d: d.find_element(By.ID, "term"))
    assert "智能购物决策系统" in driver.title, driver.title
    for label in ("京东", "淘宝", "拼多多", "闲鱼", "1688", "盼之代售"):
        assert label in driver.page_source, f"缺少平台：{label}"

    driver.find_element(By.ID, "term").send_keys("百元带麦游戏耳机")
    driver.find_element(By.ID, "budget").send_keys("100")
    add_button = driver.find_element(By.ID, "toggle-form")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_button)
    time.sleep(0.3)
    add_button.click()
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
        check = form.find_element(By.CSS_SELECTOR, f'[name="{name}"]')
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", check)
        time.sleep(0.15)
        check.click()
    submit = form.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit)
    time.sleep(0.15)
    submit.click()
    wait.until(lambda d: "测试耳机A" in d.find_element(By.ID, "candidates-list").text)
    assert "测试耳机A" in driver.find_element(By.ID, "candidates-list").text
    driver.refresh()
    wait.until(lambda d: "测试耳机A" in d.find_element(By.ID, "candidates-list").text)
    print("通过：中文页面、六平台、1688/盼之专项字段、商品录入和刷新后保留")

    # 第28—29步：用户在商品页主动触发书签后，页面只预填字段、不自动确认价格。
    import json
    from urllib.parse import quote
    payload = quote(json.dumps({
        "platform": "xianyu",
        "title": "真实页面导入测试标题",
        "url": "https://www.goofish.com/item?id=123456789"
    }, ensure_ascii=False), safe="")
    driver.get(BASE.rstrip("/") + "/classic/#si-import=" + payload)
    form = wait.until(lambda d: d.find_element(By.ID, "candidate-form"))
    wait.until(lambda d: form.is_displayed())
    assert form.find_element(By.CSS_SELECTOR, '[name="title"]').get_attribute("value") == "真实页面导入测试标题"
    assert form.find_element(By.CSS_SELECTOR, '[name="url"]').get_attribute("value") == "https://www.goofish.com/item?id=123456789"
    assert Select(form.find_element(By.CSS_SELECTOR, '[name="platform"]')).first_selected_option.get_attribute("value") == "xianyu"
    assert form.find_element(By.CSS_SELECTOR, '[name="price"]').get_attribute("value") == "", "未知价格不能自动填入"
    assert "#si-import=" not in driver.current_url, "导入信息须从地址栏清除"
    link = driver.find_element(By.ID, "shopping-bookmarklet").get_attribute("href")
    assert link.startswith("javascript:"), "缺少可拖动书签"
    print("通过：书签商品导入只预填平台/标题/链接，未知价格为空且清除地址片段")
finally:
    driver.quit()
