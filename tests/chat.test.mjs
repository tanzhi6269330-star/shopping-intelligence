import test from 'node:test';
import assert from 'node:assert/strict';
import { initialState, updateState, nextQuestion, researchCandidates, reply, discoveryLinks, sources } from '../chat/recommendation.mjs';

test('新需求识别品类、预算、用途',()=>{
  const s=updateState(initialState(),'帮我找100元以内带麦的游戏耳机');
  assert.equal(s.category,'headset');
  assert.equal(s.budget,100);
  assert.equal(s.usage,'gaming');
});
test('关键追问无需复杂表单',()=>{
  const s=updateState(initialState(),'想要游戏耳机');
  assert.match(nextQuestion(s).text,/预算/);
  const s2=updateState(s,'200元以内');
  assert.match(nextQuestion(s2).text,/有线还是无线/);
});
test('只修改预算，保留之前用途和品类',()=>{
  let s=updateState(initialState(),'帮我找100元以内的游戏耳机');
  s=updateState(s,'80元以内');
  assert.equal(s.budget,80);
  assert.equal(s.category,'headset');
  assert.equal(s.usage,'gaming');
});
test('更便宜不能凭空猜具体预算',()=>{
  let s=updateState(initialState(),'100元以内的游戏耳机');
  s=updateState(s,'再便宜点');
  assert.equal(s.budget,100);
  assert.match(nextQuestion(s).text,/降到多少/);
});
test('明确新预算后停止重复问预算',()=>{
  let s=updateState(initialState(),'100元以内游戏耳机');
  s=updateState(s,'再便宜点');
  s=updateState(s,'60元以内');
  assert.equal(s.budget,60);
  assert.equal(s.lowerPending,false);
});
test('预算不限不陷入重复追问',()=>{
  let s=updateState(initialState(),'我要买游戏耳机');
  s=updateState(s,'预算不限');
  assert.equal(s.budgetOpen,true);
  assert.doesNotMatch(nextQuestion(s).text,/预算/);
});
test('品牌偏好与排除单独处理',()=>{
  let s=updateState(initialState(),'帮我找300元以内有线游戏耳机');
  s=updateState(s,'不要漫步者');
  assert.ok(s.exclude.includes('漫步者'));
  assert.ok(!researchCandidates(s).some(x=>x.brand==='漫步者'));
});
test('指定品牌不增加其他品牌',()=>{
  const s=updateState(initialState(),'想买200元以内雷柏游戏耳机');
  assert.equal(s.brand,'雷柏');
  assert.ok(researchCandidates(s).every(x=>x.brand==='雷柏'));
});
test('来源必须可核查，不允许伪造实时价',()=>{
  const r=reply(initialState(),'帮我买300元以内有线游戏耳机');
  assert.equal(r.output.status.includes('未接通'),true);
  const r2=reply(r.state,'有线');
  for(const c of r2.output.cards){
    assert.ok(c.refs.length>0);
    assert.ok(c.refs.every(x=>x.url.startsWith('https://')));
    assert.ok(c.cautions.some(x=>/到手价/.test(x)));
  }
  assert.equal(sources.length>=3,true);
});
test('在没有来源支持的品类中不创造型号',()=>{
  const r=reply(initialState(),'想买500元以内游戏鼠标');
  const result=reply(r.state,'游戏');
  assert.equal(result.output.cards.length,0);
  assert.match(result.output.message,/没有足够证据/);
});
test('游戏账号保留游戏、区服，不自动认定安全',()=>{
  let s=updateState(initialState(),'帮我找王者荣耀账号');
  s=updateState(s,'预算500元');
  s=updateState(s,'安卓QQ');
  assert.equal(s.game,'王者荣耀');
  assert.equal(s.server,'安卓QQ');
  assert.equal(nextQuestion(s),null);
  assert.equal(researchCandidates(s).length,0);
});
test('未知品类还能继续搜索',()=>{
  const s=updateState(initialState(),'帮我找性价比高的路由器');
  assert.equal(s.category,'generic');
  assert.match(decodeURIComponent(discoveryLinks(s)[0].url),/路由器/);
});
test('外部链接有HTTPS，不能冒充即时商品列表',()=>{
  const s=updateState(initialState(),'耳机 300元以内 游戏 有线');
  for(const link of discoveryLinks(s)) assert.ok(link.url.startsWith('https://'));
});
