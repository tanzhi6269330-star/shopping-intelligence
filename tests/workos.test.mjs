import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const html = fs.readFileSync(new URL('../workos/index.html', import.meta.url), 'utf8');
test('WorkOS Chinese offline-capable single-file web page', () => {
  assert.match(html, /<html lang="zh-CN">/);
  assert.match(html, /工作任务/);
  assert.match(html, /独立质检/);
  assert.doesNotMatch(html, /<script\s+src=/i);
  assert.doesNotMatch(html, /<link\s+[^>]*stylesheet/i);
});
test('WorkOS provides task, knowledge, reconciliation, review and backup', () => {
  for (const fn of ['addTask','makePrompt','addKnowledge','reconcile','addReview','exportData','importData']) {
    assert.ok(html.includes('function ' + fn + '('), fn);
  }
  assert.match(html, /localStorage/);
  assert.match(html, /每 3 步双向审视/);
});
test('WorkOS JS parses and does not send local records to a backend', () => {
  const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
  assert.ok(script);
  assert.doesNotMatch(script, /\bfetch\s*\(/);
  assert.doesNotMatch(script, /XMLHttpRequest/);
  assert.doesNotMatch(script, /\.sendBeacon\s*\(/);
  new Function(script);
});
test('Reconciliation validates input and checks duplicate months', () => {
  assert.match(html, /月份重复/);
  assert.match(html, /月份、计划金额、台账金额/);
  assert.match(html, /function parseNumber/);
});
