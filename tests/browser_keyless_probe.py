# -*- coding: utf-8 -*-
"""真实浏览器安全验收：从 Pages 同类来源直接访问 Tavily keyless 公共搜索接口。"""
import json
from selenium import webdriver

opt=webdriver.ChromeOptions()
opt.add_argument("--headless=new")
opt.add_argument("--no-sandbox")
opt.add_argument("--disable-dev-shm-usage")
opt.add_argument("--window-size=1200,800")
browser=webdriver.Chrome(options=opt)
browser.set_script_timeout(35)
try:
    browser.get("http://127.0.0.1:8765/")
    script=r"""
const done=arguments[arguments.length-1];
const ctrl=new AbortController();
const timer=setTimeout(()=>ctrl.abort(),26000);
fetch("https://api.tavily.com/search",{
  method:"POST",
  headers:{"Content-Type":"application/json","X-Tavily-Access-Mode":"keyless"},
  body:JSON.stringify({query:"2026 游戏耳机 横评 麦克风",max_results:2,search_depth:"basic"}),
  signal:ctrl.signal
}).then(async response=>{
  const text=await response.text();
  let json={};
  try{json=JSON.parse(text)}catch{}
  done({status:response.status,
        results:Array.isArray(json.results)?json.results.map(z=>({title:String(z.title||"").slice(0,120),url:String(z.url||"").slice(0,300)})):[],
        error:json.error?.code||json.detail?.error||"",
        corsVisible:true});
}).catch(e=>done({status:0,error:String(e.name||"")+" "+String(e.message||"").slice(0,140),corsVisible:false}))
.finally(()=>clearTimeout(timer));
"""
    outcome=browser.execute_async_script(script)
    print("浏览器跨域请求状态："+str(outcome.get("status")))
    print("公开搜索候选链接数："+str(len(outcome.get("results",[]))))
    print("错误类型："+str(outcome.get("error","")))
    assert outcome.get("status")==200, json.dumps(outcome,ensure_ascii=False)
    assert len(outcome["results"])>0
    safe=[x for x in outcome["results"] if x.get("url","").startswith("https://")]
    print("安全HTTPS来源数："+str(len(safe)))
    print("返回链接协议："+",".join(x.get("url","").split(":",1)[0] for x in outcome["results"]))
    assert len(safe)>0,"外部搜索返回来源，但没有可安全展示的HTTPS链接"
    print("通过：真实Chrome无需API密钥，网页可直接跨域查询公开评测搜索；不安全链接已隔离")
finally:
    browser.quit()
