import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';

const root=readFileSync(new URL('../index.html',import.meta.url),'utf8');
const classic=readFileSync(new URL('../classic/index.html',import.meta.url),'utf8');
const engine=readFileSync(new URL('../chat/recommendation.mjs',import.meta.url),'utf8');

test('中文聊天首页不要求商品资料表',()=>{
 assert.match(root,/<html lang="zh-CN">/);
 for(const token of ['id="prompt"','id="messages"','id="summary"','id="send"'])assert.ok(root.includes(token),token);
 assert.ok(!root.includes('id="candidate-form"'));
});
test('旧版人工核验台仍完整保留',()=>{
 assert.ok(classic.includes('id="candidate-form"'));
 for(const brand of ['京东','淘宝','拼多多','闲鱼','1688','盼之代售'])assert.ok(classic.includes(brand),brand);
});
test('六平台、真实来源和使用边界均可找到',()=>{
 for(const p of ['京东','淘宝','拼多多','闲鱼','1688','盼之代售','不编造价格'])assert.ok(root.includes(p),p);
 for(const n of ['RTINGS','smzdm.com','researchCandidates','nextQuestion'])assert.ok(engine.includes(n),n);
});
test('嵌入脚本与推荐模块都可通过Node语法检查',()=>{
 for(const html of [root,classic]){
   const x=[...html.matchAll(/<script type="module">([\s\S]*?)<\/script>/g)];
   assert.equal(x.length,1);
   const run=spawnSync(process.execPath,['--input-type=module','--check'],{input:x[0][1],encoding:'utf8'});
   assert.equal(run.status,0,run.stderr);
 }
 const script=spawnSync(process.execPath,['--check',new URL('../chat/recommendation.mjs',import.meta.url).pathname],{encoding:'utf8'});
 assert.equal(script.status,0,script.stderr);
});
