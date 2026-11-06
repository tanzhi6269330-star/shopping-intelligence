export const PLATFORM_NAMES={jd:"京东",taobao:"淘宝/天猫",pdd:"拼多多",xianyu:"闲鱼",wholesale:"1688",pzds:"盼之代售"};
export const CATEGORIES=[
 {key:"headphones",name:"耳机",find:/耳机|耳麦|耳塞|头戴/,questions:[{key:"usage",ask:"主要是打游戏语音、听歌通勤，还是两者兼顾？",options:["游戏语音","听歌通勤","都需要"]},{key:"connection",ask:"优先有线还是无线？如果没有偏好我会同时比较。",options:["有线","无线","都可以"]}],brands:["漫步者","QCY","雷柏","绿联"]},
 {key:"keyboard",name:"键盘/鼠标",find:/键盘|鼠标|机械键盘/,questions:[{key:"usage",ask:"主要办公、游戏，还是都要兼顾？",options:["办公","游戏","兼顾"]},{key:"connection",ask:"是否必须无线？",options:["无线","有线","都可以"]}],brands:["雷柏","达尔优","京东京造","罗技"]},
 {key:"phone",name:"手机",find:/手机|智能机/,questions:[{key:"usage",ask:"更重视拍照、游戏性能还是续航？",options:["拍照","游戏性能","续航"]}],brands:["红米","一加","荣耀","iQOO"]},
 {key:"appliance",name:"家电",find:/冰箱|洗衣机|空调|空气炸锅|洗碗机|吸尘器/,questions:[{key:"usage",ask:"更重视性能、节能还是静音？",options:["性能","节能","静音"]}],brands:["美的","海尔","格力","小米"]},
 {key:"game",name:"游戏账号",find:/王者荣耀账号|游戏账号|买号|王者号|账号交易/,questions:[{key:"game",ask:"需要哪个游戏？例如王者荣耀。",options:["王者荣耀","和平精英","其他游戏"]},{key:"server",ask:"需要什么区服？",options:["安卓QQ","苹果QQ","安卓微信","苹果微信"]}],brands:[]},
 {key:"general",name:"商品",find:/./,questions:[{key:"usage",ask:"主要使用场景是什么？",options:["日常使用","专业用途","送人"]}],brands:[]}
];
export const BASE={category:"",query:"",budget:null,brand:"",condition:"new",usage:"",connection:"",game:"",server:"",history:[]};
export function getCategory(t){return CATEGORIES.find(x=>x.key!=="general"&&x.find.test(t))||CATEGORIES[CATEGORIES.length-1]}
export function makeState(){return {...BASE,history:[]}}
export function update(state,text){
 const t=String(text||"").trim().slice(0,500);
 const s={...state,history:[...state.history.slice(-24),{role:"user",text:t}]};
 if(!t)return s;
 const m=t.match(/(?:不超过|低于|最多|预算|大约|控制在|降到|便宜到|调整到|只要|至多|小于|再便宜点到)\s*(\d{1,7})(?:\s*元)?/);
 const range=t.match(/(\d{1,7})\s*[-—~到至]\s*(\d{1,7})\s*元/);
 if(m)s.budget=Number(m[1]);
 else if(/\d{1,7}\s*元?\s*(?:以内|以下)/.test(t))s.budget=Number(t.match(/(\d{1,7})\s*元?\s*(?:以内|以下)/)[1]);
 else if(range)s.budget=Number(range[2]);
 else if(/预算不限|不设预算|不限价|预算灵活|预算可以灵活/.test(t))s.budget=-1;
 else if(/再便宜点|便宜一点|更便宜/.test(t)&&s.budget)s.budget=Math.max(1,Math.floor(s.budget*.7));
 const explicitBrand=t.match(/(?:指定|只要|仅看|限定|就买|必须是)\s*([\p{Script=Han}A-Za-z0-9]{2,14})(?:牌|品牌|的)?/u);
 const noBrand=t.match(/不要([\p{Script=Han}A-Za-z0-9]{2,12})/u);
 if(/不限品牌|没有品牌要求|不指定品牌/.test(t))s.brand="";
 else if(explicitBrand)s.brand=explicitBrand[1];
 if(noBrand)s.excludeBrand=noBrand[1];
 if(/不考虑二手|排除二手|只看新品|不要二手/.test(t))s.condition="new";
 else if(/二手也可以|考虑闲鱼|接受二手|闲鱼也可以/.test(t))s.condition="both";
 else if(/只看二手/.test(t))s.condition="used";
 if(/有线/.test(t)&&!/无线/.test(t))s.connection="有线";
 else if(/无线/.test(t))s.connection="无线";
 if(/游戏语音|打游戏|电竞/.test(t))s.usage="游戏语音";
 else if(/听歌|通勤/.test(t))s.usage="听歌通勤";
 else if(/都需要|兼顾/.test(t))s.usage="兼顾";
 if(/安卓QQ|苹果QQ|安卓微信|苹果微信/.test(t))s.server=t.match(/安卓QQ|苹果QQ|安卓微信|苹果微信/)[0];
 if(/王者荣耀|和平精英/.test(t))s.game=t.match(/王者荣耀|和平精英/)[0];
 const cat=getCategory(t);
 const changesCategory=cat.key!=="general" && (!s.category || cat.key!==s.category);
 if(changesCategory){s.category=cat.key;s.query=cat.name;s.usage="";s.connection="";s.game=s.game||"";s.server=s.server||"";s.excludeBrand="";}
 else if(!s.category){s.category="general";s.query=t.slice(0,32)}
 else if(!s.query)s.query=cat.name;
 const d=CATEGORIES.find(x=>x.key===s.category)||CATEGORIES.at(-1);
 if(!s.brand && d.brands.length && /(?:牌子|品牌)/.test(t)&&s.query===d.name){} 
 // 只有明确指定的品牌才作为硬条件；品牌候选只是研究线索，不当作已核实推荐。
 return s;
}
export function nextQuestion(s){
 const cat=CATEGORIES.find(x=>x.key===s.category)||CATEGORIES.at(-1);
 if(s.budget==null)return {key:"budget",ask:"预算大概多少？不确定也可以说“预算灵活”。",options:["50元以内","100元以内","200元以内","预算灵活"]};
 for(const q of cat.questions){if(!s[q.key])return q;}
 return null;
}
export function researchPlan(s){
 const cat=CATEGORIES.find(x=>x.key===s.category)||CATEGORIES.at(-1);
 const subject=s.query||cat.name;
 const brandList=s.brand?[s.brand]:cat.brands.filter(b=>b!==s.excludeBrand);
 const terms=[subject,s.usage,s.connection,s.budget&&s.budget>0?"预算"+s.budget+"元":""].filter(Boolean).join(" ");
 const q=x=>"https://www.bing.com/search?q="+encodeURIComponent(x);
 const sources=[
  {name:"专业评测与横评",url:q(terms+" 2026 横向评测 性价比 缺点")},
  {name:"什么值得买选购经验",url:q("site:smzdm.com "+terms+" 值得买 测评")},
  {name:"B站真实测评",url:q("site:bilibili.com "+terms+" 测评 对比")},
  {name:"用户故障与口碑",url:q(terms+" 真实体验 故障 差评 论坛")}
 ];
 const products=[
  {name:"京东",url:"https://search.jd.com/Search?keyword="+encodeURIComponent(terms)},
  {name:"淘宝",url:"https://s.taobao.com/search?q="+encodeURIComponent(terms)},
  {name:"拼多多",url:"https://www.pinduoduo.com/"},
  {name:"1688",url:"https://www.1688.com/"},
  ...(s.condition!=="new"?[{name:"闲鱼",url:"https://www.goofish.com/search?q="+encodeURIComponent(terms)}]:[]),
  ...(cat.key==="game"?[{name:"盼之代售",url:"https://www.pzds.com/"}]:[])
 ];
 return {category:cat.name,brands:brandList,terms,sources,products};
}
