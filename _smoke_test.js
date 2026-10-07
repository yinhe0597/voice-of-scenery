/* 冒烟测试：用 jsdom 加载页面，检查运行时错误与关键渲染结果 */
const path = require('path');
const { JSDOM } = require(path.join('C:/Users/40884/.workbuddy/binaries/node/workspace/node_modules/jsdom'));

const dir = 'F:/lvyou/导游词/web';
const errors = [];

const dom = new JSDOM(require('fs').readFileSync(path.join(dir, 'index.html'), 'utf8'), {
  url: 'file:///' + dir + '/index.html',
  runScripts: 'dangerously',
  resources: {
    fetch() { return null; }
  },
  beforeParse(win) {
    win.print = () => {};
    win.addEventListener('error', e => errors.push('window.error: ' + e.message));
  }
});

// jsdom 不自动加载本地 script src，手动注入
const win = dom.window;
win.eval(require('fs').readFileSync(path.join(dir, 'assets/data.js'), 'utf8'));
try {
  win.eval(require('fs').readFileSync(path.join(dir, 'assets/app.js'), 'utf8'));
} catch (e) {
  errors.push('app.js 执行异常: ' + e.message + '\n' + e.stack.split('\n').slice(0, 4).join('\n'));
}

const doc = win.document;
function q(sel) { return doc.querySelectorAll(sel); }
function report(name, ok, extra) {
  console.log((ok ? '  ✓ ' : '  ✗ ') + name + (extra ? '  → ' + extra : ''));
  if (!ok) errors.push(name + ' 失败');
}

console.log('\n=== 首页 ===');
report('统计数字已填充', doc.getElementById('m5').textContent === '360', 'm5=' + doc.getElementById('m5').textContent);
report('地域卡片 7 个', q('.region-card').length === 7, q('.region-card').length + ' 个');
report('类型 chip 已渲染', q('.chip[data-type]').length > 15, q('.chip[data-type]').length + ' 个');
report('侧栏省份 32 个', q('.nav-item[data-prov]').length === 32, q('.nav-item[data-prov]').length + ' 个');
report('地域分组 7 个', q('.nav-region').length === 7, q('.nav-region').length + ' 个');

console.log('\n=== 切换到「按类型」 ===');
doc.querySelector('.tab[data-view="type"]').dispatchEvent(new win.MouseEvent('click', { bubbles: true }));
report('类型导航已渲染', q('.nav-item[data-type]').length > 15, q('.nav-item[data-type]').length + ' 个');

console.log('\n=== 点击某省（江苏省 26 家 5A）===');
doc.querySelector('.tab[data-view="region"]').dispatchEvent(new win.MouseEvent('click', { bubbles: true }));
doc.querySelector('.nav-item[data-prov="10"]').dispatchEvent(new win.MouseEvent('click', { bubbles: true }));
report('5A 卡片 26 张', q('.card[data-spot]').length === 26, q('.card[data-spot]').length + ' 张');
report('4A 表格已渲染', q('.tbl-wrap table tbody tr').length > 200, q('.tbl-wrap table tbody tr').length + ' 行');
report('面包屑正确', doc.getElementById('crumb').textContent.includes('江苏省'));

console.log('\n=== 打开词条详情 ===');
doc.querySelector('.card[data-spot]').dispatchEvent(new win.MouseEvent('click', { bubbles: true }));
const dTitle = doc.getElementById('dTitle').textContent;
const dBody = doc.getElementById('dBody');
report('抽屉已打开', doc.getElementById('drawer').classList.contains('show'));
report('标题非空', dTitle.length > 0, dTitle);
report('含「景区简介」区块', dBody.textContent.includes('景区简介'));
report('含「导游词核心稿」区块', dBody.textContent.includes('导游词核心稿'));
report('含「讲解要点提示」区块', dBody.textContent.includes('讲解要点提示'));
report('讲解要点含四个子类',
  dBody.textContent.includes('必讲') && dBody.textContent.includes('数据锚点') &&
  dBody.textContent.includes('常见误区') && dBody.textContent.includes('互动'));
report('导游词正文 > 300 字', dBody.textContent.length > 300, dBody.textContent.length + ' 字');

console.log('\n=== 关闭抽屉 ===');
doc.getElementById('btnClose').dispatchEvent(new win.MouseEvent('click', { bubbles: true }));
report('抽屉已关闭', !doc.getElementById('drawer').classList.contains('show'));

console.log('\n=== 搜索「石窟」 ===');
const qi = doc.getElementById('q');
qi.value = '石窟';
qi.dispatchEvent(new win.Event('input', { bubbles: true }));

setTimeout(() => {
  const cards = q('.card[data-spot]').length;
  report('搜索有结果', cards > 0, cards + ' 条 5A 命中');
  report('搜索结果含高亮', q('mark').length > 0, q('mark').length + ' 处高亮');

  console.log('\n=== 等级筛选：仅 4A ===');
  const r4 = doc.querySelector('input[name="lv"][value="4A"]');
  r4.checked = true;
  r4.dispatchEvent(new win.Event('change', { bubbles: true }));
  report('仅 4A 时不显示 5A 卡片', q('.card[data-spot]').length === 0);

  console.log('\n' + (errors.length ? '❌ 存在问题:\n' + errors.join('\n') : '✅ 全部冒烟检查通过'));
  process.exit(errors.length ? 1 : 0);
}, 400);
