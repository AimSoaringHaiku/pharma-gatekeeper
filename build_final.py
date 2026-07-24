import pandas as pd
import json
import math
from datetime import datetime, timezone, timedelta

def clean_val(val):
    """NaNやfloatの非数を安全に空文字や文字列に変換する"""
    if pd.isna(val) or val is None:
        return ""
    return str(val).strip()

def main():
    print("🚀 data_updated.csv を読み込んでHTMLを生成します...")
    
    # 1. CSV読み込み
    df = pd.read_csv("data_updated.csv")
    
    medicine_master = {}
    
    for idx, row in df.iterrows():
        key = clean_val(row.get("製品名"))
        if not key:
            continue
            
        # 1日最大服用量の安全な取得
        try:
            daily_dose = int(float(row.get("dailyDose", 1)))
        except:
            daily_dose = 1
            
        # JSON文字列を安全に保持
        matrix_json_str = clean_val(row.get("マトリックス_JSON"))
        
        # categoryLimitの取得（付加情報_JSONから取得）
        try:
            _fukainfo = json.loads(clean_val(row.get("付加情報_JSON", "{}")))
            cat_limit = int(_fukainfo.get("category_limit", 7))
            if cat_limit not in [5, 7]:
                cat_limit = 7
        except:
            cat_limit = 7        

        medicine_master[key] = {
            "name": key,
            "dailyDose": daily_dose,
            "categoryLimit": cat_limit,
            "kubun": clean_val(row.get("指定濫用(＊：同ﾌﾞﾗﾝﾄﾞ内に対象含む)", "〇")),
            "overview": clean_val(row.get("製品の特長")),
            "note": clean_val(row.get("注釈･補足等")),
            "alternative": clean_val(row.get("現場_代替薬提案")),
            "dosage_real": f"成人1日最大服用量: {daily_dose}",
            "現場_運転目安補足": clean_val(row.get("現場_運転目安補足")),
            "妊婦・授乳婦_専門家エビデンス": clean_val(row.get("妊婦・授乳婦_専門家エビデンス")),
            "マトリックス_JSON": matrix_json_str,
            # ★ 新規追加：運転目安時間のデータ連携
            "half_life": clean_val(row.get("半減期_h")),
            "driving_guide": clean_val(row.get("運転目安_h")),
            "driving_basis": clean_val(row.get("運転目安_根拠")),
            # ★ 変更：KEGG_URLがない場合、KEGG_ﾘﾝｸを取得するように差し替え
            "kegg_url": clean_val(row.get("KEGG_URL", row.get("KEGG_ﾘﾝｸ", "")))
        }
    
    # 2. JSオブジェクト文字列化
    js_data_str = f"window.medicineMaster = {json.dumps(medicine_master, ensure_ascii=False, indent=2)};"
    
    # 3. テンプレートHTMLの読み込みと置換
    with open("template.html", "r", encoding="utf-8") as f:
        html_content = f.read()
        
    final_html = html_content.replace("/* __DATA_PLACEHOLDER__ */", js_data_str)
    
    # ★ 追加：ビルド日時を生成して __BUILD_DATE__ を置換
    jst = timezone(timedelta(hours=9))
    build_date = datetime.now(jst).strftime("%Y/%m/%d %H:%M")
    final_html = final_html.replace("__BUILD_DATE__", build_date)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print(f"🎯 完了！ 全 {len(medicine_master)} 品目を搭載した 'index.html' を生成しました。")

if __name__ == "__main__":
    main()