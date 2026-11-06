# -*- coding: utf-8 -*-
"""无密钥网页搜索实验：只搜索公开通用商品评测资料，不抓电商商品列表。"""
import json
import signal
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

QUERIES=[
    "2026 百元游戏耳机 有线 麦克风 横向评测",
    "2026 无线鼠标 性价比 横评 真实用户缺点",
]
def timeout_handler(*_):
    raise TimeoutError("公共接口在35秒内未返回")
def run():
    report={"实验用途":"检验公开搜索来源是否可通过免费无密钥SDK获取；不是实时商品价格证据",
            "执行时间_UTC":datetime.now(timezone.utc).isoformat(),"服务":"Tavily SDK keyless（第三方服务有额度及可用性限制）","结果":[]}
    try:
        from tavily import TavilyClient
        client=TavilyClient()
        for q in QUERIES:
            row={"查询":q,"状态":"未运行","可用来源数":0,"来源":[]}
            try:
                signal.signal(signal.SIGALRM,timeout_handler)
                signal.alarm(35)
                result=client.search(q,search_depth="basic",max_results=5)
                urls=set()
                for z in result.get("results",[]):
                    url=str(z.get("url",""))[:900]
                    p=urlparse(url)
                    if p.scheme not in ("https","http") or not p.hostname or url in urls:
                        continue
                    urls.add(url)
                    row["来源"].append({"标题":str(z.get("title",""))[:180],"链接":url})
                row["可用来源数"]=len(row["来源"])
                row["状态"]="搜索接口返回候选链接" if row["来源"] else "接口已响应但无合格来源"
            except Exception as exc:
                row["状态"]="接口异常/限额/网络不可用"
                row["错误类型"]=type(exc).__name__
            finally:
                signal.alarm(0)
            report["结果"].append(row)
    except Exception as exc:
        report["初始化"]="SDK加载或无密钥模式不可用"
        report["错误类型"]=type(exc).__name__
    out=Path("output/keyless_search_probe.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for r in report["结果"]:
        print(r["状态"]+"｜来源 "+str(r["可用来源数"])+"｜"+r["查询"])
    print("报告："+str(out))
if __name__=="__main__":
    run()
