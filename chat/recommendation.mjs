// 中文购物对话状态与证据优先的候选推荐。纯JS，无API密钥，无伪造实时价。
export const platformEntries=[
{id:"京东",url:q=>"https://search.jd.com/Search?keyword="+encodeURIComponent(q)},
{id:"淘宝",url:q=>"https://s.taobao.com/search?q="+encodeURIComponent(q)},
{id:"拼多多",url:()=>"https://www.pinduoduo.com/"},
{id:"1688",url:()=>"https://www.1688.com/"},
{id:"闲鱼",url:q=>"https://www.goofish.com/search?q="+encodeURIComponent(q)},
{id:"盼之代售",url:()=>"https://www.pzds.com/"}
];
export const sources=[
{id:"rtings",label:"RTINGS：2026年入门游戏耳机实测",url:"https://www.rtings.com/headphones/reviews/best/gaming-headsets-under-50",kind:"专业实测",year:2026,weight:4},
{id:"smzdm1",label:"什么值得买：2026头戴式游戏耳机横评",url:"https://post.smzdm.com/p/a6z6g5ee/",kind:"社区横评",year:2026,weight:2},
{id:"smzdm2",label:"什么值得买：一季度百元级游戏耳机",url:"https://post.smzdm.com/p/ae605mrz/",kind:"社区文章",year:2026,weight:1},
{id:"smzdm3",label:"什么值得买：2026游戏耳机视频横评",url:"https://post.m.smzdm.com/zz/p/azzend2o/",kind:"视频转述",year:2026,weight:1},
{id:"smzdm4",label:"什么值得买：2026百元蓝牙耳机选择",url:"https://post.smzdm.com/p/a95ze4m0/",kind:"社区文章",year:2026,weight:1}
];
export const productEvidence=[
{id:"edifier-g2",category:"headset",brand:"漫步者",model:"HECATE G2 系列",uses:["gaming","voice"],connection:"unknown",priceReference:"文章讨论过约100—200元款，非实时售价",priorMin:100,priorMax:200,sourceIds:["smzdm2","smzdm3"],caveat:"G2有多个版本，需要逐一确认型号与连接方式。"},
{id:"rapoo",category:"headset",brand:"雷柏",model:"玄武",uses:["gaming","voice"],connection:"unknown",priceReference:"文章曾提约179元，非实时售价",priorMin:179,priorMax:179,sourceIds:["smzdm1"],caveat:"仅有社区资料作为线索，不能当作独立实验结论。"},
{id:"aula",category:"headset",brand:"狼蛛",model:"G7",uses:["gaming","voice"],connection:"unknown",priceReference:"文章曾提约99—169元，非实时售价",priorMin:99,priorMax:169,sourceIds:["smzdm2"],caveat:"具体SKU、麦克风与报价需要核实。"},
{id:"hyperx",category:"headset",brand:"HyperX",model:"Cloud III（有线款）",uses:["gaming","voice"],connection:"wired",priceReference:"国内实时价格未知",priorMin:null,priorMax:null,sourceIds:["rtings"],caveat:"专业测试不能代替国内价格和版本确认。"},
{id:"redmi",category:"headset",brand:"红米",model:"Buds 6",uses:["music","commute","voice"],connection:"wireless",priceReference:"社区资料约150元档，非实时售价",priorMin:150,priorMax:150,sourceIds:["smzdm4"],caveat:"面向日常听歌/通勤，不能直接当竞技游戏耳麦。"}
];
const cats=[
["account",/游戏账号|王者.*账号|盼之|代售|买号/],
["headset",/耳机|耳麦|头戴|降噪|蓝牙耳塞|tws|headset/i],
["mouse",/鼠标|mouse/i],
["keyboard",/键盘|keyboard/i],
["phone",/手机|iphone|安卓机/i],
["laptop",/笔记本|笔电|游戏本|轻薄本/i],
["monitor",/显示器|电竞屏/i],
["appliance",/洗衣机|冰箱|空调|扫地机器人|吹风机|空气净化|电动牙刷|家电/i]
];
const labels={generic:"其他商品",account:"游戏账号",headset:"耳机 / 耳麦",mouse:"鼠标",keyboard:"键盘",phone:"手机",laptop:"笔记本电脑",monitor:"显示器",appliance:"家电"};
const brands=["漫步者","雷柏","狼蛛","雷蛇","罗技","红米","小米","华为","荣耀","索尼","赛睿","HyperX","极度未知","海盗船","苹果","三星","OPPO","vivo"];
export function initialState(){return {category:null,term:"",budget:null,approx:null,budgetOpen:false,lowerPending:false,usage:null,connection:null,condition:"new",priceFirst:false,brand:null,exclude:[],game:null,server:null,turns:[]};}
function parseBudget(s){
let m=s.match(/(\d{2,6})\s*(?:到|至|-|~|—)\s*(\d{2,6})\s*(?:元|块)/);
if(m)return {max:Math.max(+m[1],+m[2]),approx:null};
m=s.match(/(\d{2,7})\s*(?:元|块)\s*(?:以内|以下|之内|不超过)/);
if(m)return {max:+m[1],approx:null};
m=s.match(/(?:预算|不超过|最高|最多|控制在|低于|¥|￥)\s*(\d{2,7})/);
if(m)return {max:+m[1],approx:null};
m=s.match(/(\d{2,7})\s*(?:元|块)\s*(?:左右|上下)/);
if(m)return {max:null,approx:+m[1]};
return null;
}
export function updateState(base,input){
const old=base||initialState(),s={...initialState(),...old,exclude:[...(old.exclude||[])],turns:[...(old.turns||[])]};
const t=String(input||"").trim().slice(0,700);if(!t)return s;
const detected=cats.find(c=>c[1].test(t));
if(detected&&detected[0]!==s.category){const prior=s.turns;s.category=detected[0];s.term=t;s.budget=null;s.approx=null;s.budgetOpen=false;s.lowerPending=false;s.usage=null;s.connection=null;s.brand=null;s.exclude=[];s.condition="new";s.priceFirst=false;s.game=null;s.server=null;s.turns=prior;}
if(!s.category && /买|找|推荐|挑|选购/.test(t))s.category="generic";
if(!s.term)s.term=t;
const b=parseBudget(t);if(b){s.budget=b.max;s.approx=b.approx;s.budgetOpen=false;s.lowerPending=false;}
if(/预算不限|不限预算|不设预算/.test(t)){s.budget=null;s.approx=null;s.budgetOpen=true;s.lowerPending=false;}
if(/仍按当前预算|不调整预算/.test(t))s.lowerPending=false;
if(/便宜点|便宜一点|更便宜|最低价|省钱|价格优先/.test(t)){s.priceFirst=true;if(!b && s.budget!==null)s.lowerPending=true;}
if(/游戏|电竞|fps|cs2|开黑|听声辨位/i.test(t))s.usage="gaming";
if(/音乐|听歌|音质/.test(t))s.usage="music";
if(/通勤|地铁|主动降噪/.test(t))s.usage="commute";
if(/语音|通话|开会|会议|麦克风|带麦/.test(t)&&!s.usage)s.usage="voice";
if(/无线|蓝牙|2[.]4g/.test(t)&&!/不要无线|不买无线/.test(t))s.connection="wireless";
if(/有线|插线|3[.]5mm/.test(t)&&!/不要有线/.test(t))s.connection="wired";
if(/不要无线/.test(t))s.connection="wired";
if(/不要有线/.test(t))s.connection="wireless";
if(/有线无线都行|有线和无线都行|连接方式不限/.test(t))s.connection="either";
if(/二手也行|接受二手|可以二手|闲鱼也可以/.test(t))s.condition="either";
if(/不要二手|只要全新|不考虑二手/.test(t))s.condition="new";
if(/只要二手|仅二手/.test(t))s.condition="used";
if(/区服不限|区服都行/.test(t))s.server="不限";
if(s.category==="account"){
for(const g of ["王者荣耀","原神","和平精英","崩坏：星穹铁道"]){if(t.includes(g))s.game=g;}
for(const zone of ["安卓QQ","安卓微信","苹果QQ","苹果微信"]){if(t.toLowerCase().includes(zone.toLowerCase()))s.server=zone;}
}
for(const bname of brands){if(t.toLowerCase().includes(bname.toLowerCase())){
const idx=t.toLowerCase().indexOf(bname.toLowerCase());
const before=t.slice(Math.max(0,idx-5),idx);
if(/不要|排除|不看|不考虑|避开/.test(before)){if(!s.exclude.includes(bname))s.exclude.push(bname);if(s.brand===bname)s.brand=null;}
else if(/指定|只看|就要|想买|买个|找|推荐/.test(t))s.brand=bname;
}}
s.turns.push({role:"user",text:t});s.turns=s.turns.slice(-30);return s;
}
export function nextQuestion(s){
if(!s.category)return {text:"你想买什么？直接说商品就行。",options:["游戏耳机","鼠标","手机","游戏账号"]};
if(s.category==="account"&&!s.game)return {text:"你想买哪个游戏的账号？",options:["王者荣耀","原神","和平精英"]};
if(s.lowerPending)return {text:"你想把价格上限降到多少？我会保留之前的用途和品牌条件。",options:s.budget?[(Math.floor(s.budget*0.8/10)*10)+"元以内",(Math.floor(s.budget*0.6/10)*10)+"元以内","仍按当前预算，只优先低价"]:["50元以内","100元以内"]};
if(s.budget==null&&s.approx==null&&!s.budgetOpen)return {text:"预算大概多少？也可以说不限预算。",options:["100元以内","300元以内","1000元以内","预算不限，优先性价比"]};
if(["headset","mouse","keyboard","phone","laptop","monitor"].includes(s.category)&&!s.usage)return {text:"主要用于什么？不同用途会改变值得考虑的品牌和型号。",options:s.category==="headset"?["打游戏语音","听音乐通勤","开会通话"]:["游戏","日常办公","专业创作"]};
if(s.category==="headset"&&s.usage==="gaming"&&!s.connection)return {text:"打游戏更倾向有线还是无线？百元档的连接方式会明显影响选择。",options:["有线","无线","有线无线都行"]};
if(s.category==="account"&&!s.server)return {text:"希望哪个区服？不知道可以先说“区服不限”。",options:["安卓QQ","安卓微信","苹果微信","区服不限"]};
return null;
}
export function researchCandidates(s){
return productEvidence.filter(p=>p.category===s.category&&(!s.brand||p.brand.toLowerCase()===s.brand.toLowerCase())&&!s.exclude.includes(p.brand)).map(p=>{
const refs=p.sourceIds.map(id=>sources.find(z=>z.id===id)).filter(Boolean);
const good=s.usage?p.uses.includes(s.usage):false;
const mismatch=s.connection&&s.connection!=="either"&&p.connection!=="unknown"&&s.connection!==p.connection;
const domains=new Set(refs.map(r=>new URL(r.url).hostname.replace(/^(post|post.m|www)\./,"")));
let score=Math.max(...refs.map(r=>r.weight))*12+domains.size*8+(good?24:0)-(mismatch?30:0);
let budgetNotice="现价未核验";
if(s.budget!==null){
 if(p.priorMin===null){score-=40;budgetNotice="缺少国内参考价，预算适配性未知";}
 else if(p.priorMin>s.budget){score-=40;budgetNotice="文章历史参考价高于预算，不建议直接按此推荐";}
 else if(p.priorMax>s.budget){score+=3;budgetNotice="文章历史参考区间部分超预算";}
 else {score+=20;budgetNotice="历史参考价未超预算，但当前价格未核验";}
 if(s.priceFirst&&p.priorMin!==null&&p.priorMin<=s.budget)score+=Math.max(0,Math.round(12-12*p.priorMin/Math.max(s.budget,1)));
}
return {...p,refs,score,budgetNotice,cautions:[p.caveat,budgetNotice,"不是已核实当前到手价",refs.every(x=>x.kind!=="专业实测")?"主要来源为社区内容；需交叉核验":"含专业测评来源"].filter(Boolean)};
}).sort((a,b)=>b.score-a.score).slice(0,3);
}
export function discoveryLinks(s){
let q=[s.brand||"",s.category==="account"?(s.game||"游戏账号"):(s.category==="generic"?s.term:(labels[s.category]||s.term||"商品")),s.usage==="gaming"?"游戏":"",s.connection==="wireless"?"无线":"",s.connection==="wired"?"有线":"",s.budget!=null?(String(s.budget)+"元以内"):""].filter(Boolean).join(" ");
const z=[
{label:"搜索专业评测及榜单",url:"https://www.bing.com/search?q="+encodeURIComponent(q+" 2026 横评 推荐"),kind:"外部评测搜索"},
{label:"搜索B站测评",url:"https://search.bilibili.com/all?keyword="+encodeURIComponent(q+" 评测"),kind:"外部视频搜索"},
{label:"查真实用户缺点",url:"https://www.bing.com/search?q="+encodeURIComponent(q+" 缺点 故障 真实用户"),kind:"外部口碑搜索"}
];
for(const p of platformEntries){if(s.condition==="new"&&p.id==="闲鱼")continue;z.push({label:p.id+"站内搜索",url:p.url(q),kind:"商家搜索入口"});}
return z;
}
export function reply(base,input){
const state=updateState(base,input),question=nextQuestion(state),cards=researchCandidates(state);
const tags=[labels[state.category]||"待确定品类",state.budget!=null?("≤"+state.budget+"元"):state.approx!=null?("约"+state.approx+"元"):"预算待确认",state.brand?("指定"+state.brand):"跨品牌比较",state.condition==="new"?"新品优先":state.condition==="used"?"仅二手":"可选二手",state.priceFirst?"价格优先":null].filter(Boolean);
let message="";
if(question)message="当前需求："+tags.join(" · ")+"。"+question.text+" 你也可以用一句话补充，完全不用填表。";
else if(cards.length)message="已保留："+tags.join(" · ")+"。先列出"+cards.length+"个有可查评测来源的型号研究候选。排序是资料相关程度，不代表已经完成全网比价或证明最划算。";
else message="已保留："+tags.join(" · ")+"。当前没有足够证据推荐具体型号，不会编造品牌排行。我整理了针对性的评测与平台搜索入口；实时自动搜索尚未接通。";
return {state,output:{message,question,options:question?question.options:["更便宜点","不要二手","优先性价比","换个品牌"],tags,cards:question?[]:cards,links:discoveryLinks(state),status:"有限来源研究 · 未接通全平台实时搜索"}};
}
