# -*- coding: utf-8 -*-
"""用真实Chrome和可控响应验证聊天自动搜索渲染；不消耗第三方公共搜索额度。"""
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

opts=webdriver.ChromeOptions()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--window-size=1380,900")
driver=webdriver.Chrome(options=opts)
driver.set_page_load_timeout(20)
try:
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source":r"""
(()=>{
 const orig=window.fetch.bind(window);
 window.fetch=(url,opts)=>{
  if(!String(url).includes("api.tavily.com/search"))return orig(url,opts);
  window.__testFetchCount=(window.__testFetchCount||0)+1;
  window.__testQuery=JSON.parse(opts.body).query;
  return Promise.resolve(new Response(JSON.stringify({results:[
   {title:"【无广实测】2026 游戏耳机横向对比",url:"https://www.bilibili.com/video/BV123456",content:"这只是一条公开搜索摘要，型号仍需核实。"},
   {title:"XX品牌闭眼入 品质优选",url:"https://m.jiemian.com/article/12345",content:"疑似营销导向，需要独立核验。"},
   {title:"不安全链接，禁止展示",url:"http://untrusted.example/123",content:"should not render"}]}),
   {status:200,headers:{"Content-Type":"application/json"}}));
 };
})();
"""})
    driver.get(os.environ.get("SHOPPING_SITE_URL","http://127.0.0.1:8765/"))
    wait=WebDriverWait(driver,16)
    prompt=wait.until(lambda d:d.find_element(By.ID,"prompt"))
    prompt.send_keys("帮我找100元以内带麦的游戏耳机")
    driver.find_element(By.ID,"send").click()
    wait.until(lambda d:"有线还是无线" in d.find_elements(By.CSS_SELECTOR,".message.assistant")[-1].text)
    prompt=driver.find_element(By.ID,"prompt")
    prompt.send_keys("有线")
    driver.find_element(By.ID,"send").click()
    wait.until(lambda d:len(d.find_elements(By.CSS_SELECTOR,".live-card"))==2)
    latest=driver.find_elements(By.CSS_SELECTOR,".message.assistant")[-1]
    assert "公开评测搜索" in latest.text
    assert "自称无推广" in latest.text
    assert "推广" in latest.text
    assert "不安全链接" not in latest.text
    assert driver.execute_script("return window.__testFetchCount")==1
    query=driver.execute_script("return window.__testQuery")
    assert "耳机" in query and "100元以内" in query
    assert "帮我找" not in query, "不应向第三方发送原始聊天全文"
    assert all(a.get_attribute("href").startswith("https://") for a in latest.find_elements(By.CSS_SELECTOR,".live-card a"))
    print("通过：满足需求后自动公开评测搜索、来源风险分类、HTTPS过滤、无原始对话泄漏、真实Chrome渲染")
finally:
    driver.quit()
