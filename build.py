import csv
import json
import os

# 1. 読み込むファイルと出力するファイルの名前
csv_file_path = 'data.csv'
template_html_path = 'template.html'
output_html_path = 'index.html'

def build_html():
    master_data = {}
    
    # 2. CSVファイルを開いて1行ずつ読み込む
    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                product_name = row.get('製品名', '').strip()
                if not product_name:
                    continue # 製品名が空の行はスキップ
                
                # キー用の一意なIDを作成（例: med_0, med_1...）
                key = f"med_{i}"
                
                # せき止めか風邪薬かによって基準日数を簡易判定（必要に応じてスプシの列に追加して調整可能）
                # 今回は安全のため、指定がなければ一旦7日とする
                category_limit = 5 if "せき止め" in product_name else 7 
                
                # 3. CSVの各列を、JavaScriptオブジェクトの項目に当てはめる
                master_data[key] = {
                    "name": product_name,
                    "defaultAmount": int(row.get('max_package_amount', 0) or 0),
                    "categoryLimit": category_limit,
                    "dailyDose": float(row.get('dailyDose', 0) or 0),
                    "kubun": row.get('指定濫用(＊：同ﾌﾞﾗﾝﾄﾞ内に対象含む)', '〇'),
                    "group": "対象医薬品リスト", # 絞り込みやカテゴリ列があればここへ
                    "note": row.get('注釈･補足等', ''),
                    "alternative": row.get('製品の特長', 'データなし'), # 代替案の列があればそちらに変更
                    "info": {
                        "position": row.get('「包装規格と容量区分（実態）」希望する文言列', ''),
                        "maternity": row.get('妊婦・授乳婦注意', ''),
                        "doping": "データなし（後日追加予定）",
                        "driving": "データなし（後日追加予定）"
                    }
                }
    except Exception as e:
        print(f"❌ CSVの読み込みエラー: {e}")
        return

    # 4. データをJavaScriptの形式の文字列に変換
    json_str = json.dumps(master_data, ensure_ascii=False, indent=4)
    # JSの構文に合わせるため、最初の { と最後の } の中身だけを抽出
    json_inner = json_str[1:-1] 

    # 5. template.html を読み込む
    try:
        with open(template_html_path, mode='r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"❌ テンプレートHTMLの読み込みエラー: {e}")
        return

    # 6. 目印（// --- INSERT_DATA_HERE ---）をデータに置き換える
    new_html_content = html_content.replace('// --- INSERT_DATA_HERE ---', json_inner)

    # 7. index.html として保存する
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