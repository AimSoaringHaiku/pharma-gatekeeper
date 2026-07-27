const { chromium } = require('playwright');

(async () => {
  console.log("GoogleフォームをDOM直接解析中...");
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // 作成いただいた専用フォームのURL
  const formUrl = 'https://docs.google.com/forms/d/e/1FAIpQLSf7A1Hz3jx1FpkuV-3V7X69qNcNLJao2o-G0K6HbnbrYFlOqA/viewform';
  await page.goto(formUrl, { waitUntil: 'networkidle' });

  // 実際の入力タグ (input, textarea) の name 属性と、その質問タイトルを正確にペアにする
  const entries = await page.evaluate(() => {
    const results = {};
    
    // ページ内にある「entry.XXXXX」という名前の付いた全ての入力枠を取得
    const formElements = document.querySelectorAll('input[name^="entry."], textarea[name^="entry."], select[name^="entry."]');
    
    formElements.forEach(el => {
      const name = el.getAttribute('name');
      // 親コンテナをたどって、質問のタイトルテキストを見つける
      const parent = el.closest('div[role="listitem"]') || el.closest('div.geS5n') || el.closest('div[data-params]');
      if (parent) {
        const heading = parent.querySelector('[role="heading"]');
        const title = heading ? heading.innerText.trim() : parent.innerText.split('\n')[0];
        results[title] = name;
      } else {
        results[`入力欄_${name}`] = name;
      }
    });

    // ラジオボタン等で input から漏れた項目をデータ構造から補完する
    document.querySelectorAll('div[data-params]').forEach(div => {
      const params = div.getAttribute('data-params');
      try {
        // "[[123456789,"質問タイトル"" の構造を狙い撃つ
        const match = params.match(/\[\[(\d{8,11}),\s*"([^"]+)"/);
        if (match) {
          const id = `entry.${match[1]}`;
          const title = match[2];
          if (!Object.values(results).includes(id)) {
            results[title] = id;
          }
        }
      } catch (e) {}
    });

    return results;
  });

  console.log("\n▼ 【完全版】抽出された Entry ID リスト:");
  console.log(JSON.stringify(entries, null, 2));

  await browser.close();
})();