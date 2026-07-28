import pandas as pd
import json
import math
import re
from datetime import datetime, timezone, timedelta

def clean_val(val):
    """NaNやfloatの非数を安全に空文字に変換し、無効な記号（-やなし等）を完全に消し去る"""
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if val_str in ["-", "ー", "－", "ー", "なし", "N/A", "null", "該当なし", "--"]:
        return ""
    return val_str

def remove_cite_noise(text):
    """不要な引用タグを削除し、さらに無効文字がないか最終チェックする"""
    if not text:
        return ""
    text = re.sub(r'\|［cite:\s*\d+(?:,\s*\d+)*］', '', str(text))
    res = text.strip()
    if res in ["-", "ー", "－", "ー", "なし", "N/A", "null", "該当なし", "--"]:
        return ""
    return res

def main():
    print("🚀 data_updated.csv を読み込んでHTMLを生成します...")
    
    # 1. CSV読み込み
    df = pd.read_csv("data_updated.csv")
    
    known_brands = [
        "ベンザブロック", "ベンザ", 
        "パイロンPL", "パイロン", 
        "コルゲンコーワ", "コルゲン", 
        "パブロン", "ルル", "プレコール", "改源", "コンタック", "エスタック", 
        "ストナ", "アネトン", "ブロン", "メジコン", "ペラック", "アレグラ", 
        "クラリチン", "タリオン", "ムコダイン",
        "ロキソプロフェン", "ロキソニン", 
        "リングルアイビー", "エキセドリン", "カロナール", "タイレノール", 
        "ノーシン", "セデス", "バファリン", "イブ", "ナロン", "サリドン", 
        "エルペイン",
        "トラベルミン", "ハルンケア", "レスタミン", "セルベール", "ガスター", 
        "太田胃散", "サクロン", "正露丸", "ストッパ", "アネロン", "ムヒ", 
        "ドリエル", "ウット", "コリホグス", "葛根湯", "命の母"
    ]

    series_common_notes = {}
    
    # ① まず全データから【シリーズ内位置づけ】の長文を収集して記憶
    for idx, row in df.iterrows():
        prod_name = clean_val(row.get("製品名"))
        overview_text = remove_cite_noise(clean_val(row.get("製品の特長")))
        note_text = remove_cite_noise(clean_val(row.get("注釈･補足等", row.get("注釈・補足等", ""))))
        
        combined_text = f"{overview_text}\n\n{note_text}".strip()
        
        if "【シリーズ内位置づけ】" in combined_text:
            pos_idx = combined_text.find("【シリーズ内位置づけ】")
            series_part = combined_text[pos_idx:].strip()
            
            matched = False
            for brand in known_brands:
                if brand in prod_name:
                    series_common_notes[brand] = series_part
                    matched = True
                    break
            
            if not matched and len(prod_name) >= 3:
                prefix_match = re.match(r'^([ァ-ンヴー・ア-ンa-zA-Z一-龠]{3,6})', prod_name)
                if prefix_match:
                    series_common_notes[prefix_match.group(1)] = series_part
                else:
                    series_common_notes[prod_name[:4]] = series_part

    medicine_master = {}
    
    for idx, row in df.iterrows():
        key = clean_val(row.get("製品名"))
        if not key:
            continue
            
        try:
            daily_dose = int(float(row.get("dailyDose", 1)))
        except:
            daily_dose = 1
            
        matrix_json_str = clean_val(row.get("マトリックス_JSON"))
        
        try:
            _fukainfo = json.loads(clean_val(row.get("付加情報_JSON", "{}")))
            cat_limit = int(_fukainfo.get("category_limit", 7))
            if cat_limit not in [5, 7]:
                cat_limit = 7
        except:
            cat_limit = 7        

        overview_str = remove_cite_noise(clean_val(row.get("製品の特長")))
        note_str = remove_cite_noise(clean_val(row.get("注釈･補足等", row.get("注釈・補足等", ""))))
        
        # ★ 賢い仕分け①：もし特長やL列の中に「【シリーズ内位置づけ】」があったら、そこを分離して後半（隠す用）に回す！
        series_part = ""
        if "【シリーズ内位置づけ】" in overview_str:
            pos = overview_str.find("【シリーズ内位置づけ】")
            series_part = overview_str[pos:].strip()
            overview_str = overview_str[:pos].strip() # 表側はスッキリ短い特徴だけに残す
        elif "【シリーズ内位置づけ】" in note_str:
            pos = note_str.find("【シリーズ内位置づけ】")
            series_part = note_str[pos:].strip()
            note_str = note_str[:pos].strip()

        # ★ 賢い仕分け②：自分のセルにシリーズ解説がなければ、代表薬からシェアしてもらう
        if not series_part:
            for brand_key, common_part in series_common_notes.items():
                if brand_key in key:
                    series_part = common_part
                    break
        
        # ★ 賢い仕分け③：リボンの中に隠す文章として「L列の個別の注意事項」と「シリーズ詳しい知識」を綺麗に合体！
        hidden_ribbon_text = ""
        if note_str and series_part:
            if series_part in note_str:
                hidden_ribbon_text = note_str
            else:
                hidden_ribbon_text = f"{note_str}\n\n{series_part}".strip()
        elif note_str:
            hidden_ribbon_text = note_str
        elif series_part:
            hidden_ribbon_text = series_part

    # ★ kubunの正規化：CSVの表記ゆれ（対象外/×等）を統一
        _kubun_raw = clean_val(row.get("指定濫用(＊：同ﾌﾞﾗﾝﾄﾞ内に対象含む)", "〇"))
        _kubun_normalized = "×" if _kubun_raw in ["対象外", "×", "x", "X", "対象外(*)", "対象外（*）"] else "〇"

        medicine_master[key] = {
            "name": key,
            "dailyDose": daily_dose,
            "categoryLimit": cat_limit,
            "kubun": _kubun_normalized,
            "overview": overview_str,        # ← ★ 表で普段見える場所：スッキリと製品の特長のみ！
            "note": hidden_ribbon_text,      # ← ★ リボンの中に隠す場所：L列注意事項＋シリーズ詳しい知識！
            "alternative": remove_cite_noise(clean_val(row.get("現場_代替薬提案"))),
            "dosage_real": f"成人1日最大服用量: {daily_dose}",
            "現場_運転目安補足": remove_cite_noise(clean_val(row.get("現場_運転目安補足"))),
            "妊婦・授乳婦_専門家エビデンス": remove_cite_noise(clean_val(row.get("妊婦・授乳婦_専門家エビデンス"))),
            "マトリックス_JSON": matrix_json_str,
            "half_life": clean_val(row.get("半減期_h")),
            "driving_guide": clean_val(row.get("運転目安_h")),
            "driving_basis": remove_cite_noise(clean_val(row.get("運転目安_根拠"))),
            "kegg_url": clean_val(row.get("KEGG_URL", row.get("KEGG_ﾘﾝｸ", "")))
        }
    
    # 2. JSオブジェクト文字列化
    js_data_str = f"window.medicineMaster = {json.dumps(medicine_master, ensure_ascii=False, indent=2)};"
    
    # 3. テンプレートHTMLの読み込みと置換
    with open("template.html", "r", encoding="utf-8") as f:
        html_content = f.read()
        
    final_html = html_content.replace("/* __DATA_PLACEHOLDER__ */", js_data_str)
    
    jst = timezone(timedelta(hours=9))
    build_date = datetime.now(jst).strftime("%Y/%m/%d %H:%M")
    final_html = final_html.replace("__BUILD_DATE__", build_date)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print(f"🎯 完了！ 全 {len(medicine_master)} 品目を搭載した 'index.html' (更新日時: {build_date}) を生成しました。")

if __name__ == "__main__":
    main()