// 对公开搜索链接做保守分级：只表示“值得优先人工复核”，不证明独立、客观或型号值得买。
// 不读取正文、不抓取页面、不承担品牌排名。
const reliableTests=new Set(["rtings.com","notebookcheck.net","soundguys.com","techpowerup.com"]);
const communityDomains=new Set(["bilibili.com","zhihu.com","smzdm.com","chiphell.com","reddit.com","v2ex.com"]);
const advertorialWords=/软文|推广|品牌推荐|官方推荐|闭眼入|无脑入|全网第一|第一名|品牌实力|赞助|商单|种草|推广文|企业博客|品质优选/i;
const studyWords=/实测|横评|测评|测试|拆解|录音|对比|耐久|故障|体验|复盘/i;
export function domainOf(raw){
 try{
  const url=new URL(String(raw||""));
  if(url.protocol!=="https:"||url.username||url.password||url.port||!url.hostname||url.hostname.endsWith("."))return null;
  const host=url.hostname.toLowerCase();
  if(["localhost","127.0.0.1","0.0.0.0"].includes(host)||/^\d+\.\d+\.\d+\.\d+$/.test(host))return null;
  return host.startsWith("www.")?host.slice(4):host;
 }catch{return null;}
}
function siteType(host){
 if(!host)return "无效来源";
 const matches=base=>host===base||host.endsWith("."+base);
 if([...reliableTests].some(matches))return "专业测试机构待核";
 if([...communityDomains].some(matches))return "用户社区/内容平台";
 if(matches("m.jiemian.com")||matches("jiemian.com")||matches("mydrivers.com"))return "媒体/商业信息";
 return "其他网站";
}
export function screenSource(item){
 const title=String(item?.title??item?.标题??"").slice(0,250);
 const url=String(item?.url??item?.链接??"").slice(0,1500);
 const host=domainOf(url);
 const classification=siteType(host);
 const promo=advertorialWords.test(title);
 const testHint=studyWords.test(title);
 const claimsNoAds=/无广|无广告|客观公正|无恰饭/.test(title);
 const flags=[];
 if(!host)flags.push("链接无效");
 if(promo)flags.push("标题含营销或强推荐用语");
 if(claimsNoAds)flags.push("自称无推广，仍需独立核实");
 if(!testHint)flags.push("标题未体现实测或横评");
 if(classification==="其他网站")flags.push("来源背景尚未核实");
 return {title,url,host,classification,flags,hasTestKeyword:testHint,
         reviewPriority:!host?"不纳入":promo?"需特别警惕推广":testHint?"值得进一步核实实测证据":"仅作候选发现",
         independentVerified:false,priceVerified:false,brandRecommended:false};
}
export function screenResults(items){
 const list=Array.isArray(items)?items.slice(0,30).map(screenSource):[];
 // 按页面完整链接去重，而非把同平台文章当成多个独立实验。
 const seen=new Set();
 return list.filter(x=>{if(!x.host)return false;let u;try{u=new URL(x.url);u.hash="";u.searchParams.forEach((_v,k)=>{if(/^(utm_|spm$|from$|share)/i.test(k))u.searchParams.delete(k)});}catch{return false}
   const key=u.toString();if(seen.has(key))return false;seen.add(key);return true;});
}
