import test from 'node:test';
import assert from 'node:assert/strict';
import {domainOf,screenSource,screenResults} from '../chat/source-screening.mjs';
test('非法或伪装网址不采纳',()=>{
 for(const link of ['http://www.rtings.com/reviews','https://127.0.0.1/admin','https://rtings.com.evil.test/x','javascript:alert(1)']){
  const d=domainOf(link);
  if(link.includes('evil.test'))assert.equal(d,'rtings.com.evil.test');
  else assert.equal(d,null);
 }
});
test('专业网站只有待核标签，不能直接证明独立推荐',()=>{
 const r=screenSource({title:'Headset review measurements',url:'https://www.rtings.com/headphones/reviews'});
 assert.equal(r.classification,'专业测试机构待核');
 assert.equal(r.independentVerified,false);
 assert.equal(r.brandRecommended,false);
});
test('自称无推广不等于独立无广告',()=>{
 const r=screenSource({title:'【无广实测】2026耳机横评',url:'https://www.bilibili.com/video/abc'});
 assert.ok(r.flags.some(x=>x.includes('自称无推广')));
 assert.equal(r.independentVerified,false);
});
test('媒体软推广的闭眼入标题要单独标风险',()=>{
 const r=screenSource({title:'2026年XX品牌闭眼入，品质优选',url:'https://m.jiemian.com/article/123'});
 assert.equal(r.reviewPriority,'需特别警惕推广');
});
test('完整链接去重，同平台多篇文章不算来源独立验证',()=>{
 const items=[{标题:'A实测',链接:'https://www.bilibili.com/video/abc?utm_source=foo'},
 {标题:'A实测',链接:'https://www.bilibili.com/video/abc?utm_source=bar'},
 {标题:'B横评',链接:'https://www.bilibili.com/video/other'}];
 const result=screenResults(items);
 assert.equal(result.length,2);
 assert.ok(result.every(x=>x.independentVerified===false));
});
test('失效链接排除、不接收实时价与购买结论',()=>{
 const result=screenResults([{标题:'test',链接:'http://invalid.com'},{标题:'无线鼠标横评',链接:'https://www.zhihu.com/p/123'}]);
 assert.equal(result.length,1);
 assert.equal(result[0].priceVerified,false);
 assert.equal(result[0].brandRecommended,false);
});
