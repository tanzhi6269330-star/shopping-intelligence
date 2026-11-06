import test from 'node:test';
import assert from 'node:assert/strict';
import {reviewQuery,fetchReviews} from '../chat/live-search.mjs';

test('购物查询只包含必要品类、预算、用途，不上传全文',()=>{
 const q=reviewQuery({category:'headphones',query:'耳机',budget:100,usage:'游戏语音',connection:'有线',brand:''});
 assert.match(q,/耳机/);
 assert.match(q,/100元以内/);
 assert.match(q,/有线/);
 assert.ok(!q.includes('身份证')&&!q.includes('帮我'));
});
test('游戏账号不自动向第三方发送筛选偏好',()=>{
 assert.equal(reviewQuery({category:'game',query:'王者荣耀账号',budget:500,server:'安卓QQ'}),null);
});
test('正常搜索保留HTTPS来源并标记营销风险',async()=>{
 const prior=globalThis.fetch;
 globalThis.fetch=async()=>(new Response(JSON.stringify({results:[
  {title:'【无广实测】耳机横评',url:'https://www.bilibili.com/video/BV100',content:'来源摘要'},
  {title:'品牌闭眼入 品质优选',url:'https://m.jiemian.com/article/123',content:'推广风险'},
  {title:'禁止不安全URL',url:'http://example.com/',content:'不要展示'}
 ]}),{status:200,headers:{"Content-Type":"application/json"}}));
 try{
  const r=await fetchReviews('耳机 游戏 横评');
  assert.equal(r.ok,true);
  assert.equal(r.results.length,2);
  assert.ok(r.results[0].flags.some(x=>x.includes('自称无推广')));
  assert.ok(r.results[1].flags.some(x=>x.includes('营销')));
  assert.ok(r.results.every(x=>x.url.startsWith('https://')));
  assert.ok(r.results.every(x=>x.priceVerified===false));
 }finally{globalThis.fetch=prior;}
});
test('搜索额度耗尽清晰降级，不做自动重复请求',async()=>{
 const prior=globalThis.fetch;
 globalThis.fetch=async()=>(new Response(JSON.stringify({error:{code:'hourly_cap_reached'}}),{status:429}));
 try{const r=await fetchReviews('耳机 横评');assert.equal(r.ok,false);assert.equal(r.state,'rate_limited');}
 finally{globalThis.fetch=prior;}
});
