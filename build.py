import pandas as pd
import json
import glob
import os

# 数値変換エラー（空欄など）を安全に回避する関数
def safe_float(val, default=1.0):
    try:
        import math
        f = float(val)
        return default if math.isnan(f) else f
    except:
        return default

def safe_int(val, default=5):
    try:
        import math
        i = float(val)
        return default if math.isnan(i) else int(i)
    except:
        return default

def clean_val(val):
    if pd.isna(val) or val == '-' or str(val).lower() == 'nan':
        return ""
    return str(val).strip()

def main():
    csv_files = glob.glob("*.csv")
    if not csv_files:
        print("❌ エラー: CSVファイルが見つかりません。")
        return
    
    target_csv = next((f for f in csv_files if f == "data.csv"), 
             next((f for f in csv_files if "共有用_OTC" in f), csv_files[0]))

    print(f"📂 読み取り中: {target_csv}")
    
    df = pd.read_csv(target_csv)
    medicine_dict = {}
    
    for idx, row in df.iterrows():
        name = clean_val(row.get('製品名'))
        if not name:
            continue
            
        item = {
            "name": name,
            "group": clean_val(row.get('薬効')) or "一般用医薬品",
            "dailyDose": safe_float(row.get('dailyDose'), 1.0),
            "categoryLimit": safe_int(row.get('categoryLimit'), 5),
            "kubun": clean_val(row.get('指定濫用(＊：同ﾌﾞﾗﾝﾄﾞ内に対象含む)')),
            "note": clean_val(row.get('注釈･補足等')),
            "alternative": clean_val(row.get('現場_代替薬提案')),
            "matrix_json": clean_val(row.get('マトリックス_JSON')),
            "info": {
                "overview": (clean_val(row.get('製品の特長')) + 
                             ("\n\n【シリーズ内位置づけ】\n" + clean_val(row.get('注釈･補足等')) 
                              if clean_val(row.get('注釈･補足等')) else "")),
                "dosage_real": f"成人1日最大服用量: {row.get('dailyDose', '--')} (服用制限: {row.get('服用禁止', 'なし')})",
                "maternity": clean_val(row.get('妊婦・授乳婦_専門家エビデンス')) or clean_val(row.get('妊婦・授乳婦注意')),
                "doping_driving": clean_val(row.get('現場_運転目安補足')),
                "professional_info": clean_val(row.get('現場_運転目安補足'))
            }
        }
        medicine_dict[name] = item

    template_path = "template.html"
    if not os.path.exists(template_path):
        print("❌ エラー: template.html が見つかりません。")
        return
        
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    json_data_str = json.dumps(medicine_dict, ensure_ascii=False, indent=2)
    final_html = html_content.replace("/* __DATA_PLACEHOLDER__ */", f"const medicineMaster = {json_data_str};")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print(f"✅ 成功! {len(medicine_dict)} 品目のデータを組み込んだ index.html を生成しました！")

if __name__ == "__main__":
    main()