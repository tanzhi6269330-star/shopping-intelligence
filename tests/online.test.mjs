import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
test('完整中文单文件入口',()=>{assert.match(html,/<html lang="zh-CN">/);assert.match(html,/<style>[\s\S]+<\/style>/);assert.match(html,/<script type="module">[\s\S]+<\/script>/);});
test('六个平台在网页内可见',()=>{for(const name of ['京东','淘宝','拼多多','闲鱼','1688','盼之代售'])assert.ok(html.includes(name),name);});
test('核验风险与数据保存提示存在',()=>{for(const name of ['localStorage','人工核验','交易风险','核验'])assert.ok(html.includes(name),name);});
test('嵌入的 JS 模块可通过语法检查',()=>{const scripts=[...html.matchAll(/<script type="module">([\s\S]*?)<\/script>/g)];assert.equal(scripts.length,1);const run=spawnSync(process.execPath,['--input-type=module','--check'],{input:scripts[0][1],encoding:'utf8'});assert.equal(run.status,0,run.stderr);});
