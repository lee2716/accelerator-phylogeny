// Appended to the page by tests only (see tests/test_legibility.py): measures what a reader actually gets.
// For every text class: rendered size in screen pixels and contrast ratio against the surface behind it.
(function () {
  const lum = c => { const v = c.map(x => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); }); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
  const parse = s => { const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,/]+/).map(Number); return { rgb: p.slice(0, 3), a: p.length > 3 ? p[3] : 1 }; };
  const over = (top, bottom) => top.rgb.map((v, i) => v * top.a + bottom[i] * (1 - top.a));
  function surfaceBehind(node) {          // nearest ancestor with an opaque-ish fill; SVG text sits on the stage panel unless inside a card
    const card = node.closest && node.closest(".pcard"); if (card) { const c = parse(getComputedStyle(card.querySelector(".cbox")).fill); if (c) return c.rgb; }
    let rgb = parse(getComputedStyle(document.body).backgroundColor).rgb;
    const chain = []; for (let n = node; n; n = n.parentElement) chain.unshift(n);     // the element's own background counts (buttons, tags)
    for (const n of chain) { const c = parse(getComputedStyle(n).backgroundColor); if (c && c.a > 0) rgb = over(c, rgb); }
    return rgb;
  }
  const rows = {};
  const groups = { ".cname": "card name", ".cmeta": "card venue/year", ".cmark": "card marks", ".more": "+N papers tag", ".lane-label": "branch name", ".lane-n": "branch count",
    ".year": "year heading", ".plabel": "name on the tree", ".prodname": "industry name", ".meta": "small grey text", ".narr": "tour narration", ".q": "explanatory text",
    ".tag": "tag", ".legend": "legend", "h2": "section heading", "h3": "small heading", ".item button.link": "paper title in list", ".stat span": "stat caption", ".chip-btn": "button" };
  for (const [selector, name] of Object.entries(groups)) {
    const nodes = [...document.querySelectorAll(selector)].filter(n => n.getBoundingClientRect().width > 0 && !n.closest('.off, .dim, [disabled]') && !n.matches('.off, [disabled]')).slice(0, 60); if (!nodes.length) continue;   // deliberately dimmed or disabled items are judged separately
    let minPx = 1e9, minContrast = 1e9;
    for (const n of nodes) {
      const st = getComputedStyle(n), svgText = n instanceof SVGElement;
      let px = parseFloat(st.fontSize);
      if (svgText) { const svg = n.ownerSVGElement, vb = svg.viewBox.baseVal; px *= svg.getBoundingClientRect().width / vb.width; }
      const colour = parse(svgText ? st.fill : st.color); if (!colour) continue;
      let opacity = 1; for (let m = n; m && m.nodeType === 1; m = m.parentElement) opacity *= parseFloat(getComputedStyle(m).opacity);
      const bg = surfaceBehind(n), fg = over({ rgb: colour.rgb, a: colour.a * opacity }, bg);
      const l1 = lum(fg), l2 = lum(bg), contrast = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
      minPx = Math.min(minPx, px); minContrast = Math.min(minContrast, contrast);
    }
    rows[name] = { n: nodes.length, px: Math.round(minPx * 10) / 10, contrast: Math.round(minContrast * 100) / 100 };
  }
  document.body.append(Object.assign(document.createElement("pre"), { id: "legibility", textContent: JSON.stringify(rows) }));
})();
