import pandas as pd
import json
import glob
import os

def clean_val(val):
    if pd.isna(val) or val == '-' or str(val).lower() == 'nan':
        return ""
    return str(val).strip()

def main():
    # CSVファイルを自動検知（ファイル名が変わっても対応可能に）
    csv_files = glob.glob("*.csv")
    if not csv_files:
        print("❌ エラー: CSVファイルが見つかりません。")
        return
    
    # 対象のCSVを読み込み（優先的に『共有用_OTC』を含むものを選択）
    target_csv = next((f for f in csv_files if "共有用_OTC" in f), csv_files[0])
    print(f"📂 読み取り中: {target_csv}")
    
    df = pd.read_csv(target_csv)
    data_list = []
    
    for idx, row in df.iterrows():
        # JSON文字列の安全なパース
        ing_info, dos_info, add_info = {}, {}, {}
        try: ing_info = json.loads(clean_val(row.get('成分情報_JSON', '{}')))
        except: pass
        try: dos_info = json.loads(clean_val(row.get('用法用量_JSON', '{}')))
        except: pass
        try: add_info = json.loads(clean_val(row.get('付加情報_JSON', '{}')))
        except: pass

        # エビデンス・補足文章の自動組み立て
        item = {
            "name": clean_val(row.get('製品名')),
            "group": clean_val(row.get('薬効')) or "一般用医薬品",
            "dailyDose": float(row.get('dailyDose', 1) or 1),
            "categoryLimit": int(row.get('categoryLimit', 5) or 5),
            "kubun": clean_val(row.get('指定濫用(＊：同ﾌﾞﾗﾝﾄﾞ内に対象含む)')),
            "note": clean_val(row.get('注釈･補足等')),
            
            # CSVの新列「現場_代替薬提案」をセット
            "alternative": clean_val(row.get('現場_代替薬提案')),
            
            "info": {
                "overview": clean_val(row.get('製品の特長')),
                "dosage_real": f"成人1日最大服用量: {row.get('dailyDose', '--')} (服用制限: {row.get('服用禁止', 'なし')})",
                "maternity": clean_val(row.get('妊婦・授乳婦_専門家エビデンス')) or clean_val(row.get('妊婦・授乳婦注意')),
                "doping_driving": clean_val(row.get('現場_運転目安補足')),
                
                # エビデンス全般や注意情報をまとめ
                "professional_info": clean_val(row.get('現場_運転目安補足'))
            }
        }
        data_list.append(item)

    # テンプレートHTMLの読み込み
    template_path = "template.html"
    if not os.path.exists(template_path):
        print("❌ エラー: template.html が見つかりません。")
        return
        
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # ★修正ポイント：HTML側の変数名に合わせるため const medicineMaster = に変更！
    json_data_str = json.dumps(data_list, ensure_ascii=False, indent=2)
    final_html = html_content.replace("/* __DATA_PLACEHOLDER__ */", f"const medicineMaster = {json_data_str};")

    # index.html の出力
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print(f"✅ 成功! {len(data_list)} 品目のデータを組み込んだ index.html を生成しました！")

if __name__ == "__main__":
    main()