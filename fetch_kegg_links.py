import asyncio
import pandas as pd
from playwright.async_api import async_playwright

async def fetch_kegg_url(page, product_name):
    """製品名でKEGG OTCデータベースを検索し、添付文書のURLを取得する"""
    try:
        # KEGG MEDICUSのOTC検索ページへアクセス
        search_url = f"https://www.kegg.jp/medicus-bin/search_medicus?query={product_name}&search_target=otc"
        await page.goto(search_url, timeout=15000)
        
        # 検索結果の最初の詳細リンク（[D から始まるリンクなど）を取得
        detail_link = page.locator("a", has_text="[D").first
        if await detail_link.count() > 0:
            href = await detail_link.get_attribute("href")
            return f"https://www.kegg.jp{href}"
    except Exception as e:
        print(f"⚠️ 取得エラー ({product_name}): {e}")
    
    return ""

async def main():
    csv_filename = "data_updated.csv"
    df = pd.read_csv(csv_filename)
    
    # 新しい列「KEGG_URL」を準備
    if "KEGG_URL" not in df.columns:
        df["KEGG_URL"] = None
    df["KEGG_URL"] = df["KEGG_URL"].astype(object)

    print("🚀 Playwright を起動し、KEGG公式リンクの自動収集を開始します...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for idx, row in df.iterrows():
            prod_name = row.get("製品名")
            
            # すでにURLがある場合はスキップ
            if pd.notna(row.get("KEGG_URL")) and str(row.get("KEGG_URL")).startswith("http"):
                continue
                
            if prod_name:
                print(f"🔍 検索中: {prod_name}...")
                kegg_url = await fetch_kegg_url(page, prod_name)
                
                if kegg_url:
                    df.at[idx, "KEGG_URL"] = kegg_url
                    print(f"  ✅ 取得成功: {kegg_url}")
                else:
                    print(f"  ❌ 見つかりませんでした")
                    
        await browser.close()
        
    # 上書き保存
    df.to_csv("data_updated.csv", index=False)
    print("🎯 すべてのリンク取得が完了しました！ 'data_updated.csv' を更新しました。")

if __name__ == "__main__":
    asyncio.run(main())