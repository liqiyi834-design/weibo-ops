/*
  Weibo visible-page capture helper.
  Run this in your own logged-in Edge page. It only reads visible page text
  and public DOM content; it does not read cookies, passwords, tokens, or
  private browser storage.
*/
(function () {
  const now = new Date();
  const stamp = now.toISOString().replace(/[:.]/g, "-");

  function clean(text) {
    return String(text || "")
      .replace(/\s+/g, " ")
      .replace(/\u200b/g, "")
      .trim();
  }

  function uniq(items) {
    return Array.from(new Set(items.filter(Boolean)));
  }

  function pickText(root, selectors) {
    for (const selector of selectors) {
      const node = root.querySelector(selector);
      const text = clean(node && node.innerText);
      if (text) return text;
    }
    return "";
  }

  function collectLinks(root) {
    return uniq(
      Array.from(root.querySelectorAll("a[href]"))
        .map((a) => a.href)
        .filter((href) => /weibo\.com|m\.weibo\.cn|s\.weibo\.com/.test(href))
    ).slice(0, 8);
  }

  const selectors = [
    "article",
    "[role='article']",
    ".card",
    ".vue-recycle-scroller__item-view",
    ".Feed_body_3R0rO",
    ".woo-box-flex",
    ".WB_cardwrap",
    ".m-auto-list",
  ];

  let cards = [];
  for (const selector of selectors) {
    cards = cards.concat(Array.from(document.querySelectorAll(selector)));
  }

  cards = uniq(cards)
    .filter((node) => {
      const text = clean(node.innerText);
      return text.length >= 40 && text.length <= 5000;
    })
    .slice(0, 80);

  const samples = cards.map((node, index) => {
    const text = clean(node.innerText);
    const links = collectLinks(node);
    const hashtags = uniq((text.match(/#[^#\s]{1,40}#/g) || []).map(clean));
    const metrics = clean(
      Array.from(node.querySelectorAll("button, a, span"))
        .map((el) => clean(el.innerText))
        .filter((t) => /转发|评论|赞|阅读|\d/.test(t))
        .slice(0, 30)
        .join(" | ")
    );

    return {
      index: index + 1,
      page_title: document.title,
      page_url: location.href,
      captured_at: now.toISOString(),
      body_text: text,
      hashtags,
      metrics,
      links,
      possible_author: pickText(node, [
        "a[title]",
        "[class*='name']",
        "[class*='Name']",
        "[class*='author']",
        "[class*='Author']",
      ]),
    };
  });

  const payload = {
    tool: "weibo_visible_capture",
    version: "1.0",
    captured_at: now.toISOString(),
    page_title: document.title,
    page_url: location.href,
    sample_count: samples.length,
    samples,
  };

  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `weibo_visible_samples_${stamp}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);

  console.log("Weibo visible samples captured:", payload);
  alert(`已导出 ${samples.length} 条可见样本。请把下载的 JSON 放到 D:\\微博\\samples\\inbox`);
})();
