// 第35步：真实用户提问形态的跨品类基准；缺证据时必须拒绝编造。
import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,reply} from '../chat/recommendation.mjs';

const cases=[
 {id:"游戏耳机",turns:["帮我找100元以内带麦克风的游戏耳机","有线"],category:"headset",budget:100,sourcedExpected:true},
 {id:"无线鼠标",turns:["帮我找300元以内高性价比无线鼠标","主要打游戏"],category:"mouse",budget:300,sourcedExpected:false},
 {id:"手机",turns:["1000元以内的手机，主要打游戏"],category:"phone",budget:1000,sourcedExpected:false},
 {id:"家电",turns:["想买200元以内的电动牙刷"],category:"appliance",budget:200,sourcedExpected:false},
 {id:"游戏账号",turns:["帮我找王者荣耀账号","预算500元以内","安卓QQ"],category:"account",budget:500,sourcedExpected:false},
 {id:"未收录品类",turns:["帮我找500元以内路由器"],category:"generic",budget:500,sourcedExpected:false}
];

function execute(tc){
 let state=initialState(),out=null;
 for(const message of tc.turns){const r=reply(state,message);state=r.state;out=r.output;}
 return {state,output:out};
}

test('六类购物需求均保留明确预算与品类',()=>{
 for(const c of cases){
  const r=execute(c);
  assert.equal(r.state.category,c.category,c.id+"品类");
  assert.equal(r.state.budget,c.budget,c.id+"预算");
  assert.ok(r.output.links.length>=3,c.id+"外部检索入口");
 }
});
test('无评测证据时绝不凭空填充型号推荐',()=>{
 for(const c of cases){
  const r=execute(c);
  if(c.sourcedExpected){assert.ok(r.output.cards.length>0,c.id);}
  else assert.equal(r.output.cards.length,0,c.id+"必须无购买型号结论");
 }
});
test('返回型号研究候选需明确来源URL与非实时价格限制',()=>{
 const c=execute(cases[0]);
 for(const card of c.output.cards){
  assert.ok(card.refs.length>0);
  assert.ok(card.refs.every(x=>x.url.startsWith('https://')));
  assert.ok(card.cautions.some(x=>x.includes('到手价')));
  assert.ok(card.priceReference.includes('非实时')||card.priceReference.includes('实时价格未知'));
 }
});
test('预算缩小只更新预算与追问，不自动假造折扣',()=>{
 let s=execute(cases[0]).state;
 let r=reply(s,'再便宜点');
 assert.equal(r.state.budget,100);
 assert.match(r.output.message,/降到多少/);
 r=reply(r.state,'80元以内');
 assert.equal(r.state.budget,80);
 assert.ok(r.output.cards.every(x=>x.priceReference.includes('非实时')||x.priceReference.includes('未知')));
});
test('不购买特定品牌时必须立即从推荐中排除',()=>{
 let s=execute(cases[0]).state;
 const r=reply(s,'不要漫步者');
 assert.ok(r.state.exclude.includes('漫步者'));
 assert.ok(r.output.cards.every(x=>x.brand!=='漫步者'));
});
test('覆盖率基线须明确呈现，不伪装为全品类已完成',()=>{
 const available=cases.filter(c=>execute(c).output.cards.length>0).length;
 const rate=Number((available/cases.length*100).toFixed(1));
 console.log('当前有来源型号研究覆盖：'+available+'/'+cases.length+'类场景（'+rate+'%）；非实时商品搜索成功率');
 assert.equal(available,1,'覆盖率发生变化时应重新人工核验推荐来源和品类');
});
