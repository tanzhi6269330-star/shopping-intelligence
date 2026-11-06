# -*- coding: utf-8 -*-
"""真实Chrome界面测试：模拟第三方公开搜索结果，不消耗Tavily查询额度。"""
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

opt=webdriver.ChromeOptions()
opt.add_argument("--headless=new")
opt.add_argument("--no-sandbox")
opt.add_argument("--disable-dev-shm-usage")
opt.add_argument("--window-size=1360,900")
driver=webdriver.Chrome(options=opt)
wait=WebDriverWait(driver,18)
try:
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",{"source":r"""
(()=>{
 const original=window.fetch.bind(window);
 window.fetch=(url,options)=>{
  if(!String(url).includes("api.tavily.com/search"))return original(url,options);
  window.__callCount=(window.__callCount||0)+1;
  window.__searchTerm=JSON.parse(options.body).query;
  return Promise.resolve(new Response(JSON.stringify({results:[
    {title:"【无广实测】2026游戏耳机横评",url:"https://www.bilibili.com/video/BV12345",content:"公开摘要：具体型号仍应核对。"},
    {title:"某品牌闭眼入 品质优选",url:"https://m.jiemian.com/article/12345",content:"文章可能有营销倾向，需要独立验证。"},
    {title:"不应展示的不安全来源",url:"http://invalid.example.com/promo",content:"should not render"}
  ]}),{status:200,headers:{"Content-Type":"application/json"}}));
 };
})();
"""})
    driver.get(os.environ.get("SHOPPING_SITE_URL","http://127.0.0.1:8765/"))
    wait.until(lambda d:d.find_element(By.ID,"chat-input"))
    for message in ["帮我找100元以内带麦的游戏耳机","游戏语音","有线"]:
        box=driver.find_element(By.ID,"chat-input")
        box.send_keys(message)
        driver.find_element(By.CSS_SELECTOR,"#chat-form button[type=submit]").click()
    wait.until(lambda d:len(d.find_elements(By.CSS_SELECTOR,".live-item"))==2)
    content=driver.find_element(By.CSS_SELECTOR,".live-research").text
    assert "自称无推广" in content
    assert "营销" in content or "推广" in content
    assert "不应展示的不安全来源" not in content
    assert driver.execute_script("return window.__callCount")==1
    term=driver.execute_script("return window.__searchTerm")
    assert "耳机" in term and "100元以内" in term
    assert "帮我找" not in term
    assert all(x.get_attribute("href").startswith("https://") for x in driver.find_elements(By.CSS_SELECTOR,".live-item a"))
    print("通过：对话自动检索、真实Chrome渲染、来源营销风险标签、HTTPS过滤、隐私最小化")
finally:
    driver.quit()
