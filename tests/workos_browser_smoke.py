# -*- coding: utf-8 -*-
"""WorkOS independent browser smoke: local and published GitHub Pages."""
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

base = os.environ.get("SHOPPING_SITE_URL", "http://127.0.0.1:8765/")
url = base.rstrip("/") + "/workos/"
opts = webdriver.ChromeOptions()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1366,900")
driver = webdriver.Chrome(options=opts)

try:
    wait = WebDriverWait(driver, 25)
    driver.get(url)
    wait.until(lambda d: d.find_element(By.ID, "t-title"))
    assert "WorkOS" in driver.title, driver.title
    assert "在线中文工作台" in driver.page_source

    driver.find_element(By.CSS_SELECTOR, '[data-tab="tasks"]').click()
    driver.find_element(By.ID, "t-title").send_keys("模拟费用任务")
    driver.find_element(By.ID, "t-goal").send_keys("核对模拟的1至3月费用并输出差异")
    driver.find_element(By.XPATH, '//button[contains(text(),"生成执行提示词")]').click()
    assert "模拟费用任务" in driver.find_element(By.ID, "prompt").get_attribute("value")
    driver.find_element(By.XPATH, '//button[contains(text(),"生成独立质检词")]').click()
    assert "独立质检员" in driver.find_element(By.ID, "prompt").get_attribute("value")
    driver.find_element(By.XPATH, '//button[text()="保存任务"]').click()
    assert "模拟费用任务" in driver.find_element(By.ID, "task-list").text

    driver.find_element(By.CSS_SELECTOR, '[data-tab="quality"]').click()
    driver.find_element(By.XPATH, '//button[text()="开始核对"]').click()
    assert "10.00" in driver.find_element(By.ID, "money-result").text

    driver.find_element(By.ID, "money").clear()
    driver.find_element(By.ID, "money").send_keys("1月,100,100\n1月,120,120")
    driver.find_element(By.XPATH, '//button[text()="开始核对"]').click()
    assert "月份重复" in driver.find_element(By.ID, "money-result").text

    driver.find_element(By.CSS_SELECTOR, '[data-tab="reviews"]').click()
    steps = driver.find_element(By.ID, "r-steps")
    steps.clear()
    steps.send_keys("21")
    assert "应进行双向审视" in driver.find_element(By.ID, "r-hint").text
    print("WorkOS PASS:", url, "中文页面、提示词、任务、差额、重复月份、三步审视")
finally:
    driver.quit()
