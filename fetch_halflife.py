import asyncio
import json
import re
import pandas as pd
from playwright.async_api import async_playwright

# 1. 取得ターゲットの主要成分と、「現実的な運転目安(practical_hours)」を定義
# 添付文書の警告強度（「運転禁止」vs「注意」）に基づき、現場で使えるリアルな時間を設定
KNOWN_HALFLIFE = {
    # 【🔴 添付文書：運転禁止レベル（当日NG〜翌日まで）】
    "クロルフェニラミンマレイン酸塩": {"t1_2": 20.0, "restrict": True, "practical_hours": "24時間（翌日まで）", "source": "添付文書:禁止(半減期長)"},
    "ジフェンヒドラミン塩酸塩": {"t1_2": 9.0, "restrict": True, "practical_hours": "12時間（当日NG）", "source": "添付文書:禁止"},
    "プロメタジンメチレンジサリチル酸塩": {"t1_2": 12.0, "restrict": True, "practical_hours": "12時間〜24時間", "source": "添付文書:禁止"},
    "コデインリン酸塩水和物": {"t1_2": 3.0, "restrict": True, "practical_hours": "12時間（当日NG）", "source": "添付文書:禁止"},
    "ジヒドロコデインリン酸塩": {"t1_2": 4.0, "restrict": True, "practical_hours": "12時間（当日NG）", "source": "添付文書:禁止"},
    "ブロモバレリル尿素": {"t1_2": 15.0, "restrict": True, "practical_hours": "24時間（翌日まで）", "source": "中枢抑制:鎮静"},

    # 【🟡 添付文書：運転回避（作用消失まで／当日NGレベル）】
    "デキストロメトルファン臭化水素酸塩水和物": {
        "t1_2": 3.5, 
        "restrict": True, 
        "practical_hours": "約6〜8時間（作用消失まで／当日NG）", 
        "source": "添付文書:運転回避(半減期約3.5h)"
    },
    "dl-メチルエフェドリン塩酸塩": {
        "t1_2": 6.0, 
        "restrict": True, 
        "practical_hours": "約8〜12時間（当日NG）", 
        "source": "添付文書:運転注意・回避"
    },

    # 【🟢 運転制限が不要な成分（臨床上、通常の服用で運転可能なもの）】
    "アセトアミノフェン": {"t1_2": 2.5, "restrict": False, "practical_hours": "制限なし", "source": "臨床上影響なし"},
    "ロキソプロフェンナトリウム水和物": {"t1_2": 1.3, "restrict": False, "practical_hours": "制限なし", "source": "臨床上影響なし"},
    "イブプロフェン": {"t1_2": 2.0, "restrict": False, "practical_hours": "制限なし", "source": "臨床上影響なし"},
    "サリチルアミド": {"t1_2": 1.0, "restrict": False, "practical_hours": "制限なし", "source": "臨床上影響なし"},
    "フェキソフェナジン塩酸塩": {"t1_2": 11.0, "restrict": False, "practical_hours": "制限なし", "source": "FAA認可・非鎮静性"},
    "無水カフェイン": {"t1_2": 5.0, "restrict": False, "practical_hours": "制限なし", "source": "通常量では覚醒作用"},
    "グアイフェネシン": {"t1_2": 1.0, "restrict": False, "practical_hours": "制限なし", "source": "去痰薬（影響なし）"},
    "ブロムヘキシン塩酸塩": {"t1_2": 1.0, "restrict": False, "practical_hours": "制限なし", "source": "去痰薬（影響なし）"},
    "カルボシステイン": {"t1_2": 2.0, "restrict": False, "practical_hours": "制限なし", "source": "去痰薬（影響なし）"},
    "リボフラビン": {"t1_2": 1.0, "restrict": False, "practical_hours": "制限なし", "source": "ビタミン類（影響なし）"}
}

# 2. WEB検索すらスキップする除外キーワード（ブラックリスト）
IGNORE_KEYWORDS = [
    "妊婦", "授乳婦", "禁忌", "受診勧奨", "濫用", "MOH", "ドーピング", "毒性",
    "アルコール", "ジュース", "制酸剤", "薬", "剤", "阻害", "ステロイド", "NSAIDs",
    "カッコン", "マオウ", "タイソウ", "ケイヒ", "シャクヤク", "カンゾウ", "エキス", "エリスロマイシン",
    "シメチジン", "リチウム", "ワルファリン", "メトトレキサート"
]

def should_ignore(target_name):
    """関係ない単語や見出し、相互作用相手かどうかを判定する関数"""
    if not target_name or len(target_name) <= 1:
        return True
    for kw in IGNORE_KEYWORDS:
        if kw in target_name:
            return True
    return False

async def fetch_kegg_halflife(page, ingredient_name):
    """Playwrightを使ってKEGG MEDICUSから「成分名」で半減期を拾う関数"""
    try:
        search_url = f"https://www.kegg.jp/medicus-bin/search_medicus?query={ingredient_name}&search_target=otc"
        await page.goto(search_url, timeout=15000)
        
        detail_link = page.locator("a", has_text="[D").first
        if await detail_link.count() > 0:
            href = await detail_link.get_attribute("href")
            await page.goto(f"https://www.kegg.jp{href}", timeout=15000)
            
            content = await page.content()
            match = re.search(r'(?:半減期|t1/2).*?([0-9]+(?:\.[0-9]+)?)\s*時間', content, re.IGNORECASE)
            if match:
                return float(match.group(1)), "KEGGスクレイピング自動取得"
    except Exception as e:
        print(f"⚠️ 取得エラー ({ingredient_name}): {e}")
    
    return None, "情報なし"

async def main():
    csv_filename = "data.csv"
    df = pd.read_csv(csv_filename)
    
    # 型エラー(TypeError)防止: 数値も文字も安全に入るよう None & object型 で初期化
    for col in ["半減期_h", "運転目安_h", "運転目安_根拠"]:
        if col not in df.columns:
            df[col] = None
        df[col] = df[col].astype(object)

    print("🚀 【現実的・一般論歩み寄り版】運転目安時間の自動付与を開始します...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for idx, row in df.iterrows():
            prod_name = row.get("製品名", f"Row_{idx}")
            matrix_str = str(row.get("マトリックス_JSON", ""))
            
            max_t12 = 0.0
            best_source = ""
            best_practical = ""
            has_restricted_ingredient = False  # 🔴 運転制限が必要な成分が含まれているかのフラグ
            is_known = False                   # 既知マスタからの採用かどうかのフラグ
            
            # ① マトリックスJSONから成分を抽出してチェック
            if "成分マトリックス" in matrix_str:
                try:
                    matrix_data = json.loads(matrix_str)
                    for item in matrix_data.get("成分マトリックス", []):
                        ing_name = item.get("成分名", "").strip()
                        
                        if not ing_name or should_ignore(ing_name):
                            continue
                            
                        # [A] 既知マスタ（KNOWN_HALFLIFE）に存在する場合
                        if ing_name in KNOWN_HALFLIFE:
                            info = KNOWN_HALFLIFE[ing_name]
                            if info["restrict"]:
                                has_restricted_ingredient = True
                                # 制限成分の中で最も安全側に倒す（一番長い半減期のものを優先保持）
                                if info["t1_2"] > max_t12:
                                    max_t12 = info["t1_2"]
                                    best_source = f"{ing_name} ({info['source']})"
                                    best_practical = info["practical_hours"]
                                    is_known = True
                        
                        # [B] 未知の成分の場合、表マトリックスの「運転」評価が ✕ か △ ならWEB検索する
                        else:
                            driving_eval = item.get("運転・操作", {}).get("判定", "")
                            if driving_eval in ["✕", "△"]:
                                has_restricted_ingredient = True
                                print(f"🔍 [未登録の制限成分] 「{ing_name}」をKEGGで確認中...")
                                scraped_val, source_text = await fetch_kegg_halflife(page, ing_name)
                                if scraped_val and scraped_val > max_t12:
                                    max_t12 = scraped_val
                                    best_source = f"{ing_name} ({source_text})"
                                    is_known = False  # WEBから拾った未知成分
                                    
                except Exception as e:
                    print(f"⚠️ JSON解析エラー ({prod_name}): {e}")
            
            # ② 最終判定とデータ書き込み（ハイブリッドロジックの発動！）
            if has_restricted_ingredient and max_t12 > 0:
                df.at[idx, "半減期_h"] = max_t12
                
                # ★ 既知成分は人間が設計した実務時間(practical_hours)、未知成分は「×1.5倍(効果消失)」を採用
                if is_known:
                    df.at[idx, "運転目安_h"] = best_practical
                else:
                    practical_calc = round(max_t12 * 1.5, 1)
                    df.at[idx, "運転目安_h"] = f"約{practical_calc}時間後（目安）"
                    
                df.at[idx, "運転目安_根拠"] = best_source
                print(f"🔴 【制限あり】{prod_name}: 基準➡{best_source} ｜ 目安: {df.at[idx, '運転目安_h']}")
            
            elif has_restricted_ingredient and max_t12 == 0:
                # 制限成分はあるが半減期が拾えなかった場合
                df.at[idx, "半減期_h"] = None
                df.at[idx, "運転目安_h"] = "服用中の運転回避"
                df.at[idx, "運転目安_根拠"] = "制限成分含有（半減期要文献確認）"
                print(f"🟡 【注意】{prod_name}: 制限成分あり（時間計算要確認）")
                
            else:
                # アレグラやロキソニンなど、運転制限成分が一切含まれていない場合
                df.at[idx, "半減期_h"] = None
                df.at[idx, "運転目安_h"] = "制限なし"
                df.at[idx, "運転目安_根拠"] = "非鎮静性・運転制限成分の非含有"
                print(f"🟢 【制限なし】{prod_name}: 運転に影響する成分なし")
                
        await browser.close()
        
    df.to_csv("data_updated.csv", index=False)
    print("\n🎯 すべての処理が完了しました！ 'data_updated.csv' に現実的で完璧なデータが保存されました。")

if __name__ == "__main__":
    asyncio.run(main())