import csv
import json
import os

csv_file_path = 'data.csv'
template_html_path = 'test_7.html'
output_html_path = 'index.html'

def build_html():
    master_data = {}
    
    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                product_name = row.get('製品名', '').strip()
                if not product_name:
                    continue
                
                key = f"med_{i}"
                category_limit = 5 if "せき止め" in product_name else 7 
                
                # 1. 用法・用量（実態）
                position_text = row.get('「包装規格と容量区分（実態）」希望する文言列', '').strip()
                if not position_text:
                    position_text = row.get('「包装規格と容量区分（実態）」現在の文言列', '').strip()
                if not position_text:
                    position_text = "パッケージの現物総量を確認し、計算結果に従って判定してください。"

                # 2. 妊婦・授乳婦
                maternity_raw = row.get('妊婦・授乳婦注意', '').strip()
                maternity_text = f"【OTC添付文書】{maternity_raw}" if maternity_raw else "添付文書の確認をおすすめします。"

                # 3. ドーピング判定
                ingredients = row.get('成分情報_JSON', '')
                doping_text = "【規定】禁止物質非該当です。"
                if any(x in ingredients for x in ["メチルエフェドリン", "プソイドエフェドリン", "エフェドリン", "マオウ", "麻黄"]):
                    doping_text = "【規定】エフェドリン系・マオウ等を含有するため、スポーツ競技大会時は使用禁止です。"

                # 4. 運転判定
                add_info = row.get('付加情報_JSON', '')
                driving_text = "【規定】服用後の乗物・機械類の運転操作は禁止されています。"
                if "対象外" in row.get('指定濫用(＊：同ﾌﾞﾗﾝﾄﾞ内に対象含む)', ''):
                    if "運転禁止" not in add_info:
                        driving_text = "添付文書の「運転操作」に関する注意書きをご確認ください。"
                if "運転禁止" in add_info:
                    driving_text = "【規定】服用後の乗物・機械類の運転操作は禁止されています。"

                # 5. 代替薬
                alt_text = row.get('製品の特長', '').strip()
                if not alt_text:
                    alt_text = "代替案・特長のマスタ登録がありません。"

                # 6. 【新設】専門家向け情報（Dify等の出力先）
                pro_info = row.get('専門家情報', '').strip()
                # 現在のCSVに「専門家情報」列がない場合は空文字になるため、HTML側でデフォルト文言が出ます

                master_data[key] = {
                    "name": product_name,
                    "defaultAmount": int(row.get('max_package_amount', 0) or 0),
                    "categoryLimit": category_limit,
                    "dailyDose": float(row.get('dailyDose', 0) or 0),
                    "kubun": row.get('指定濫用(＊：同ﾌﾞﾗﾝﾄﾞ内に対象含む)', '〇'),
                    "group": "対象医薬品リスト",
                    "note": row.get('注釈･補足等', ''),
                    "alternative": alt_text,
                    "info": {
                        "position": position_text,
                        "maternity": maternity_text,
                        "doping": doping_text,
                        "driving": driving_text,
                        "professional_info": pro_info
                    }
                }
    except Exception as e:
        print(f"❌ CSVの読み込みエラー: {e}")
        return

    json_str = json.dumps(master_data, ensure_ascii=False, indent=4)
    json_inner = json_str[1:-1] 

    try:
        with open(template_html_path, mode='r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"❌ テンプレートHTMLの読み込みエラー: {e}")
        return

    new_html_content = html_content.replace('// --- INSERT_DATA_HERE ---', json_inner)

    try:
        with open(output_html_path, mode='w', encoding='utf-8') as f:
            f.write(new_html_content)
        print(f"✅ 成功！ {len(master_data)} 品目のデータを挿入し、{output_html_path} を作成しました。")
    except Exception as e:
        print(f"❌ HTMLの保存エラー: {e}")

if __name__ == "__main__":
    if not os.path.exists(csv_file_path):
        print(f"❌ {csv_file_path} が見つかりません。アップロードしてください。")
    else:
        build_html()