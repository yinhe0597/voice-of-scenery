/* 全国 4A 及以上旅游景区导游词库 · 前端逻辑 */
(function () {
  'use strict';

  var D = window.SITE_DATA;
  if (!D) { document.body.innerHTML = '<p style="padding:40px">数据未加载：请确认 assets/data.js 存在。</p>'; return; }

  /* ---------- 工具 ---------- */
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
  function hl(s, q) {
    var t = esc(s);
    if (!q) return t;
    try {
      return t.replace(new RegExp('(' + q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi'),
        '<mark>$1</mark>');
    } catch (e) { return t; }
  }
  function $(id) { return document.getElementById(id); }
  function excerpt(arr, n) {
    if (!arr || !arr.length) return '';
    var s = arr.join(' ').replace(/\s+/g, ' ');
    return s.length > n ? s.slice(0, n) + '…' : s;
  }

  /* 类型配色 */
  var PALETTE = ['#1f6f5c', '#2c6e9b', '#8a5a2b', '#7a4a86', '#a8442f', '#2f7d55',
    '#9a6a1f', '#4a5f9e', '#8e3f5c', '#3c7a72', '#6b5a2e', '#5a6b2e',
    '#2e6b6b', '#7a3f3f', '#4f4f8e', '#6b3f7a', '#3f6b4f', '#8e6b2e'];
  function typeColor(code) {
    var i = parseInt(String(code).replace(/\D/g, ''), 10);
    return PALETTE[(isNaN(i) ? 0 : i) % PALETTE.length];
  }
  function tagHtml(typeStr) {
    if (!typeStr) return '';
    return typeStr.split(/[·、,，]/).map(function (x) {
      x = x.trim(); if (!x) return '';
      return '<span class="tag">' + esc(x) + '</span>';
    }).join('');
  }

  /* ---------- 预处理 ---------- */
  var ALL5 = [], ALL4 = [];
  D.provinces.forEach(function (p) {
    p.spots.forEach(function (s) { s.prov = p.name; s.pcode = p.code; s.region = p.region; ALL5.push(s); });
    p.a4.forEach(function (r) { r.prov = p.name; r.pcode = p.code; ALL4.push(r); });
  });

  var TYPE4COUNT = {};
  ALL4.forEach(function (r) { (r.types || []).forEach(function (c) { TYPE4COUNT[c] = (TYPE4COUNT[c] || 0) + 1; }); });
  var TYPE5COUNT = {};
  ALL5.forEach(function (s) { (s.types || []).forEach(function (c) { TYPE5COUNT[c] = (TYPE5COUNT[c] || 0) + 1; }); });

  var REGION_STAT = {};
  D.regions.forEach(function (rg) {
    var ps = D.provinces.filter(function (p) { return p.region === rg; });
    REGION_STAT[rg] = {
      provs: ps.length,
      n5: ps.reduce(function (a, p) { return a + p.n5; }, 0),
      n4: ps.reduce(function (a, p) { return a + p.n4; }, 0)
    };
  });
  var MAXREG = Math.max.apply(null, D.regions.map(function (r) { return REGION_STAT[r].n5; })) || 1;

  /* ---------- 状态 ---------- */
  var state = { view: 'region', level: 'all', sel: null, q: '', cur: null };

  /* ---------- 侧栏 ---------- */
  function renderNav() {
    var n = $('nav'), h = '';
    if (state.view === 'region') {
      h += '<button class="nav-item' + (state.sel === null ? ' active' : '') + '" data-all="1">' +
        '<span class="nm">全部景区</span><span class="ct">' + ALL5.length + ' / ' + ALL4.length + '</span></button>';
      D.regions.forEach(function (rg) {
        var st = REGION_STAT[rg];
        var ract = (state.sel && state.sel.kind === 'region' && state.sel.name === rg);
        h += '<div class="nav-group">' +
          '<button class="nav-item nav-region' + (ract ? ' active' : '') + '" data-region="' + esc(rg) + '">' +
          '<span class="nm">' + esc(rg) + '地区</span><span class="ct">' + st.n5 + '+' + st.n4 + '</span></button>';
        D.provinces.filter(function (p) { return p.region === rg; }).forEach(function (p) {
          var act = (state.sel && state.sel.kind === 'prov' && state.sel.code === p.code);
          h += '<button class="nav-item' + (act ? ' active' : '') + '" data-prov="' + p.code + '">' +
            '<span class="nm">' + esc(p.name) + '</span><span class="ct">' + p.n5 + '+' + p.n4 + '</span></button>';
        });
        h += '</div>';
      });
    } else {
      h += '<div class="nav-group-title">景区类型（5A + 4A）</div>';
      D.types.forEach(function (t) {
        var c5 = TYPE5COUNT[t.code] || 0, c4 = TYPE4COUNT[t.code] || 0;
        if (!c5 && !c4) return;
        var act = (state.sel && state.sel.kind === 'type' && state.sel.code === t.code);
        h += '<button class="nav-item' + (act ? ' active' : '') + '" data-type="' + t.code + '">' +
          '<span class="dot" style="background:' + typeColor(t.code) + '"></span>' +
          '<span class="nm">' + esc(t.name) + '</span><span class="ct">' + c5 + '+' + c4 + '</span></button>';
      });
    }
    n.innerHTML = h;
  }

  /* ---------- 主区 ---------- */
  function curDataset() {
    var q = state.q.trim();
    if (q) {
      var ql = q.toLowerCase();
      function hit5(s) {
        return (s.name + ' ' + s.prov + ' ' + s.place + ' ' + s.type + ' ' +
          s.intro.join(' ') + ' ' + s.script.join(' ')).toLowerCase().indexOf(ql) >= 0;
      }
      function hit4(r) {
        return (r.name + ' ' + r.prov + ' ' + r.county + ' ' + r.type).toLowerCase().indexOf(ql) >= 0;
      }
      var lv = state.level;
      return {
        spots: lv === '4A' ? [] : ALL5.filter(hit5),
        a4: lv === '5A' ? [] : ALL4.filter(hit4),
        provCol: true,
        title: '搜索结果',
        crumb: '搜索「' + q + '」'
      };
    }
    if (state.sel === null) return null; // 首页

    if (state.sel.kind === 'prov') {
      var p = D.provinces.filter(function (x) { return x.code === state.sel.code; })[0];
      return {
        spots: p.spots, a4: p.a4, provCol: false,
        title: p.name, note: p.note,
        crumb: p.region + ' / ' + p.name,
        pending: p.pending
      };
    }
    if (state.sel.kind === 'region') {
      var ps = D.provinces.filter(function (x) { return x.region === state.sel.name; });
      return {
        spots: ps.reduce(function (a, x) { return a.concat(x.spots); }, []),
        a4: ps.reduce(function (a, x) { return a.concat(x.a4); }, []),
        provCol: true, title: state.sel.name + '地区',
        crumb: '按地域 / ' + state.sel.name + '地区'
      };
    }
    if (state.sel.kind === 'type') {
      var t = D.types.filter(function (x) { return x.code === state.sel.code; })[0];
      var lv = state.level;
      var s5 = lv === '4A' ? [] : ALL5.filter(function (s) { return (s.types || []).indexOf(t.code) >= 0; });
      var s4 = lv === '5A' ? [] : ALL4.filter(function (r) { return (r.types || []).indexOf(t.code) >= 0; });
      return { spots: s5, a4: s4, provCol: true, title: t.name, crumb: '按类型 / ' + t.name };
    }
    return null;
  }

  function cardHtml(s) {
    return '<article class="card" data-spot="' + esc(s.pcode + '|' + s.name) + '">' +
      '<div class="card-top"><h3>' + hl(s.name, state.q.trim()) + '</h3>' +
      '<span class="yr">' + esc(s.year || '') + '</span></div>' +
      '<div class="loc"><b>' + esc(s.prov) + '</b><span>' + esc(s.place || '') + '</span></div>' +
      '<p class="desc">' + hl(excerpt(s.intro, 105), state.q.trim()) + '</p>' +
      '<div class="tags">' + tagHtml(s.type) + '</div></article>';
  }

  function tableHtml(rows, provCol) {
    if (!rows.length) return '';
    var h = '<div class="tbl-wrap"><div class="tbl-scroll"><table><thead><tr>' +
      '<th style="width:46px">#</th><th>景区名称</th>' +
      (provCol ? '<th>省区市</th>' : '') +
      '<th>所在区县</th><th>类型</th><th>词条状态</th></tr></thead><tbody>';
    var lastG = null;
    rows.forEach(function (r, i) {
      if (r.group && r.group !== lastG && !provCol) {
        lastG = r.group;
        h += '<tr><td colspan="5" class="tbl-group">' + esc(r.group) + '</td></tr>';
      }
      h += '<tr><td class="idx">' + (i + 1) + '</td>' +
        '<td><span class="nm">' + hl(r.name, state.q.trim()) + '</span></td>' +
        (provCol ? '<td>' + esc(r.prov) + '</td>' : '') +
        '<td>' + esc(r.county || '—') + '</td>' +
        '<td>' + tagHtml(r.type) + '</td>' +
        '<td>' + esc(r.status || '—') + '</td></tr>';
    });
    return h + '</tbody></table></div></div>';
  }

  function renderHome() {
    var h = '<div class="hero"><h2>全国 4A 及以上旅游景区导游词库</h2>' +
      '<p>面向导游、研学讲师与文旅从业者。5A 景区每家含公开简介、可直接讲解的导游词核心稿与讲解要点提示；4A 景区提供名录索引。按地域或按类型两种方式浏览，支持全文检索。</p>' +
      '<div class="hero-stats">' +
      '<div><b>' + D.meta.total5 + '</b><span>5A 精编词条</span></div>' +
      '<div><b>' + D.meta.unique + '</b><span>唯一 5A 景区</span></div>' +
      '<div><b>' + D.meta.total4 + '</b><span>4A 名录条目</span></div>' +
      '<div><b>' + D.meta.provinces + '</b><span>省级行政区</span></div>' +
      '<div><b>2026-10</b><span>数据核对时间</span></div>' +
      '</div></div>';

    h += '<div class="sect-title">按地域浏览</div><div class="region-grid">';
    D.regions.forEach(function (rg) {
      var st = REGION_STAT[rg];
      h += '<button class="region-card" data-region="' + esc(rg) + '">' +
        '<h3>' + esc(rg) + '地区</h3>' +
        '<div class="n">' + st.provs + ' 个省区市 · ' + st.n5 + ' 家 5A · ' + st.n4 + ' 条 4A</div>' +
        '<div class="bar"><i style="width:' + Math.round(st.n5 / MAXREG * 100) + '%"></i></div>' +
        '</button>';
    });
    h += '</div>';

    h += '<div class="sect-title">按类型浏览</div><div class="chips">';
    D.types.forEach(function (t) {
      var c5 = TYPE5COUNT[t.code] || 0, c4 = TYPE4COUNT[t.code] || 0;
      if (!c5 && !c4) return;
      h += '<button class="chip" data-type="' + t.code + '" style="border-color:' + typeColor(t.code) + '33">' +
        esc(t.name) + '<b>' + c5 + '+' + c4 + '</b></button>';
    });
    h += '</div>';

    h += '<div class="sect-title">使用提醒</div><div class="tips-box"><ul>' +
      '<li>导游词为通用讲解稿，出行前请核对最新门票、开放时间、预约与限流政策。</li>' +
      '<li>A 级景区名单动态变化（新增／复核／降级／摘牌），建议每年复核一次。</li>' +
      '<li>4A 名录为<strong>不完全收录</strong>（全国实际约 4,700–6,000 家），仅供检索。</li>' +
      '<li>黄河壶口瀑布旅游区为陕西延安与山西临汾共有，两省各收录一次；新疆江布拉克为兵地共建，新疆与兵团各收录一次——全库 360 条对应 358 家唯一景区。</li>' +
      '<li>点击任意 5A 卡片可打开详情，支持「复制导游词」与「打印」（打印时只输出导游词正文）。</li>' +
      '</ul></div>';
    return h;
  }

  function render() {
    var ds = curDataset();
    var q = state.q.trim();

    if (!ds) {
      $('crumb').innerHTML = '首页';
      $('toolbar').innerHTML = '';
      $('content').innerHTML = renderHome();
      return;
    }

    $('crumb').innerHTML = '<a data-home="1">首页</a><span class="sep">›</span><span class="cur">' +
      esc(ds.crumb) + '</span>';

    var show5 = state.level !== '4A', show4 = state.level !== '5A';
    var n5 = show5 ? ds.spots.length : 0, n4 = show4 ? ds.a4.length : 0;
    var tb = '<h2>' + esc(ds.title) + '</h2><span class="cnt">5A ' + n5 + ' 家 · 4A ' + n4 + ' 条</span>';
    if (ds.note) tb += '<div class="note">' + esc(ds.note) + '</div>';
    $('toolbar').innerHTML = tb;

    var c = '';
    if (show5) {
      if (n5) {
        c += '<div class="sect-title">5A 级景区 · 精编词条（点击查看详情）</div><div class="grid">' +
          ds.spots.map(cardHtml).join('') + '</div>';
      } else if (!n4) {
        c += '<div class="empty"><b>没有匹配的景区</b>换个关键词，或切换等级筛选试试</div>';
      }
    }
    if (show4 && n4) {
      c += '<div class="sect-title">4A 级景区 · 名录索引（' + n4 + ' 条，不完全收录）</div>' +
        tableHtml(ds.a4, ds.provCol);
    }
    if (!c) c = '<div class="empty"><b>当前筛选下没有内容</b>试试切换「等级」筛选</div>';

    if (ds.pending && ds.pending.length) {
      c += '<div class="sect-title">本省待核实与补充事项</div><div class="tips-box"><ul>' +
        ds.pending.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') + '</ul></div>';
    }
    $('content').innerHTML = c;
  }

  /* ---------- 抽屉 ---------- */
  function openSpot(key) {
    var parts = key.split('|'), code = parts[0], name = parts.slice(1).join('|');
    var p = D.provinces.filter(function (x) { return x.code === code; })[0];
    if (!p) return;
    var s = p.spots.filter(function (x) { return x.name === name; })[0];
    if (!s) return;
    state.cur = s;

    $('dTitle').textContent = s.name;
    $('dBadge').textContent = '5A';
    $('dBadge').className = 'badge';
    $('dMeta').textContent = [s.prov, s.place, '评定年份 ' + (s.year || '—')].filter(Boolean).join(' · ');

    var h = '<div class="blk"><div class="blk-t">基本信息</div><div class="kv">' +
      '<div><dt>等级</dt><dd>' + esc(s.grade || '5A') + '</dd></div>' +
      '<div><dt>所在地</dt><dd>' + esc(s.place || '—') + '</dd></div>' +
      '<div><dt>景区类型</dt><dd>' + esc(s.type || '—') + '</dd></div>' +
      '<div><dt>评定年份</dt><dd>' + esc(s.year || '—') + '</dd></div>' +
      '<div><dt>建议游览时长</dt><dd>' + esc(s.duration || '—') + '</dd></div>' +
      '</div></div>';

    if (s.intro && s.intro.length) {
      h += '<div class="blk"><div class="blk-t">景区简介</div>' +
        s.intro.map(function (t) { return '<p>' + esc(t) + '</p>'; }).join('') + '</div>';
    }
    if (s.script && s.script.length) {
      h += '<div class="blk script"><div class="blk-t">导游词核心稿</div>' +
        s.script.map(function (t) { return '<p>' + esc(t) + '</p>'; }).join('') + '</div>';
    }
    var t = s.tips || {}, any = t.must || t.data || t.myth || t.ask || (t.other && t.other.length);
    if (any) {
      h += '<div class="blk"><div class="blk-t">讲解要点提示</div><div class="tip-grid">';
      [['must', '必讲', 'must'], ['data', '数据锚点', 'data'],
       ['myth', '常见误区', 'myth'], ['ask', '互动 / 提问设计', 'ask']].forEach(function (x) {
        if (t[x[0]]) h += '<div class="tip ' + x[2] + '"><div class="tt">' + x[1] + '</div>' +
          '<div class="tc">' + esc(t[x[0]]) + '</div></div>';
      });
      if (t.other && t.other.length) {
        h += '<div class="tip"><div class="tt">其他提示</div><div class="tc">' +
          t.other.map(function (o) { return esc(o); }).join('<br>') + '</div></div>';
      }
      h += '</div></div>';
    }
    $('dBody').innerHTML = h;
    $('dBody').scrollTop = 0;
    $('drawer').classList.add('show');
    $('drawer').setAttribute('aria-hidden', 'false');
    $('mask').classList.add('show');
  }
  function closeDrawer() {
    $('drawer').classList.remove('show');
    $('drawer').setAttribute('aria-hidden', 'true');
    $('mask').classList.remove('show');
  }

  /* ---------- 事件 ---------- */
  $('nav').addEventListener('click', function (e) {
    var b = e.target.closest('.nav-item'); if (!b) return;
    if (b.dataset.all) state.sel = null;
    else if (b.dataset.region) state.sel = { kind: 'region', name: b.dataset.region };
    else if (b.dataset.prov) state.sel = { kind: 'prov', code: b.dataset.prov };
    else if (b.dataset.type) state.sel = { kind: 'type', code: b.dataset.type };
    state.q = ''; $('q').value = ''; $('clearQ').classList.remove('show');
    renderNav(); render(); window.scrollTo(0, 0);
  });

  document.querySelector('.tabs').addEventListener('click', function (e) {
    var b = e.target.closest('.tab'); if (!b) return;
    document.querySelectorAll('.tab').forEach(function (x) { x.classList.remove('active'); });
    b.classList.add('active');
    state.view = b.dataset.view; state.sel = null;
    renderNav(); render();
  });

  document.querySelector('.filters').addEventListener('change', function (e) {
    if (e.target.name === 'lv') { state.level = e.target.value; render(); }
  });

  $('content').addEventListener('click', function (e) {
    var card = e.target.closest('.card[data-spot]');
    if (card) { openSpot(card.dataset.spot); return; }
    var rc = e.target.closest('.region-card');
    if (rc) {
      state.view = 'region'; state.sel = { kind: 'region', name: rc.dataset.region };
      document.querySelectorAll('.tab').forEach(function (x) {
        x.classList.toggle('active', x.dataset.view === 'region');
      });
      renderNav(); render(); window.scrollTo(0, 0); return;
    }
    var ch = e.target.closest('.chip[data-type]');
    if (ch) {
      state.view = 'type'; state.sel = { kind: 'type', code: ch.dataset.type };
      document.querySelectorAll('.tab').forEach(function (x) {
        x.classList.toggle('active', x.dataset.view === 'type');
      });
      renderNav(); render(); window.scrollTo(0, 0);
    }
  });

  $('crumb').addEventListener('click', function (e) {
    if (e.target.dataset.home) {
      state.sel = null; state.q = ''; $('q').value = ''; $('clearQ').classList.remove('show');
      renderNav(); render(); window.scrollTo(0, 0);
    }
  });

  var timer;
  $('q').addEventListener('input', function (e) {
    var v = e.target.value;
    $('clearQ').classList.toggle('show', !!v);
    clearTimeout(timer);
    timer = setTimeout(function () { state.q = v; render(); }, 160);
  });
  $('clearQ').addEventListener('click', function () {
    $('q').value = ''; state.q = ''; this.classList.remove('show'); render(); $('q').focus();
  });

  $('btnClose').addEventListener('click', closeDrawer);
  $('mask').addEventListener('click', closeDrawer);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeDrawer();
    if (e.key === '/' && document.activeElement !== $('q')) { e.preventDefault(); $('q').focus(); }
  });

  $('btnCopy').addEventListener('click', function () {
    var s = state.cur; if (!s) return;
    var txt = s.name + '（' + s.prov + '）\n\n【景区简介】\n' + s.intro.join('\n\n') +
      '\n\n【导游词核心稿】\n' + s.script.join('\n\n') + '\n\n【讲解要点提示】\n';
    var t = s.tips || {};
    if (t.must) txt += '必讲：' + t.must + '\n';
    if (t.data) txt += '数据锚点：' + t.data + '\n';
    if (t.myth) txt += '常见误区：' + t.myth + '\n';
    if (t.ask) txt += '互动设计：' + t.ask + '\n';
    var btn = this, old = btn.textContent;
    function done() { btn.textContent = '已复制 ✓'; setTimeout(function () { btn.textContent = old; }, 1400); }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(txt).then(done, fallback);
    } else fallback();
    function fallback() {
      var ta = document.createElement('textarea');
      ta.value = txt; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); done(); } catch (e) { btn.textContent = '复制失败'; }
      document.body.removeChild(ta);
    }
  });
  $('btnPrint').addEventListener('click', function () { window.print(); });

  /* ---------- 启动 ---------- */
  $('m5').textContent = D.meta.total5;
  $('m4').textContent = D.meta.total4;
  $('mprov').textContent = D.meta.provinces;
  $('mdate').textContent = D.meta.updated;
  renderNav();
  render();
})();
