// 公开评测搜索：用户网页直接调用Tavily的keyless公共接口（非大模型/电商核价）。
// 仅发送用品类、预算、用途、连接方式拼成的非敏感检索词；不传递聊天全文/账号数据/用户订单。
import {screenResults} from "./source-screening.mjs";
const endpoint="https://api.tavily.com/search";
const names={headphones:"耳机 耳麦",keyboard:"键盘 鼠标",phone:"手机",appliance:"家电",general:"商品",game:"游戏账号"};
const usage={gaming:"游戏 电竞",music:"听歌 音质",commute:"通勤",voice:"语音 麦克风"};
export const SEARCH_LIMIT=4; // 单个浏览器页面会话最多四轮自动查询，保护公共共享额度。
export function reviewQuery(s){
 if(!s||!s.category||s.category==="game")return null;
 const pieces=[String(new Date().getFullYear()),names[s.category]||"商品",s.usage?String(s.usage).replace(/[^\p{Script=Han}a-zA-Z0-9]/gu,"").slice(0,15):""];
 if(s.category==="general"){
  // 只发送规范化后的短商品名；不上传整个聊天、游戏账号或用户隐私。
  const candidate=String(s.query||"").replace(/[^\p{Script=Han}a-zA-Z0-9\s]/gu," ").replace(/\s+/g," ").trim().slice(0,24);
  if(!candidate)return null;
  pieces[1]=candidate;
 }
 if(s.brand)pieces.push(String(s.brand).slice(0,30));
 if(s.connection==="有线")pieces.push("有线");
 if(s.connection==="无线")pieces.push("无线");
 if(Number.isFinite(s.budget)&&s.budget>0)pieces.push(String(s.budget)+"元以内");
 pieces.push("横向评测", "缺点", "真实体验");
 return pieces.filter(Boolean).join(" ").slice(0,160);
}
export async function fetchReviews(query,{signal}={}){
 if(!query||typeof query!=="string"||query.length>180)throw Error("检索词不符合要求");
 const control=new AbortController();
 const onAbort=()=>control.abort();
 signal?.addEventListener("abort",onAbort,{once:true});
 const timer=setTimeout(()=>control.abort(),18000);
 try{
  const response=await fetch(endpoint,{method:"POST",headers:{"Content-Type":"application/json","X-Tavily-Access-Mode":"keyless"},
    body:JSON.stringify({query,search_depth:"basic",max_results:6}),
    signal:control.signal});
  const raw=await response.json().catch(()=>({}));
  if(response.status===429)return {ok:false,state:"rate_limited",message:"公开搜索共享额度已达到限制。请稍后重试，也可以点击下方外部评测检索入口。",results:[]};
  if(!response.ok)return {ok:false,state:"error",message:"搜索接口返回错误："+response.status+"。可改用外部搜索入口。",results:[]};
  const items=Array.isArray(raw.results)?raw.results.slice(0,10).map(x=>({title:String(x.title||"").slice(0,180),
    url:String(x.url||"").slice(0,1500),content:String(x.content||"").replace(/\s+/g," ").slice(0,320)})):[];
  const screened=screenResults(items);
  const byURL=new Map(items.map(x=>[x.url,x]));
  const cleaned=screened.map(x=>({...x,excerpt:byURL.get(x.url)?.content?.slice(0,220)||""})).slice(0,6);
  return {ok:true,state:cleaned.length?"found":"empty",
    message:cleaned.length?("公开搜索找到"+cleaned.length+"条安全链接。标题和摘要只作线索，不能直接证明推荐客观或价格最优。"):"搜索已响应，但没有可安全展示的HTTPS评测链接。",
    results:cleaned};
 }catch(error){
  if(error?.name==="AbortError")return {ok:false,state:"timeout",message:"搜索超时。请稍后重试，或使用外部检索入口。",results:[]};
  return {ok:false,state:"unavailable",message:"当前网络无法连接免费搜索服务；请使用外部评测检索入口。",results:[]};
 }finally{
  clearTimeout(timer);
  signal?.removeEventListener("abort",onAbort);
 }
}
