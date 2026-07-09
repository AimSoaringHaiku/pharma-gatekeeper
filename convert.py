import csv
import json

# === 【注意】実際のファイル名に合わせてここを書き換えてください ===
input_csv = 'Dify連携.csv' 
output_csv = '提出用_指定濫用マスタ.csv'

# 提出形式のヘッダー完全指定
headers = [
    'MEMBER_ID', 'SHOP_ID', 'GOODS_ID', '★区分', '★容量', 
    'GOODS_NAME', 'GOODS_NAME_KANA', 'UNIT_PRICE', 'TAX_KIND', 
    'DEPARTMENT_ID', 'TAX_RATE_NO', 'ALL_FLG', 'DEL_FLG', 'UPDATE_DAY', 
    'SPECIAL_PRICE1', 'SPECIAL_PRICE2', 'ABUSE_KIND', 'ABUSE_SIZE', 
    '18歳未満（未成年）への販売', '18歳以上（成人）への販売', '成分', '年齢確認フラグ', '備考'
]

def build_export_csv():
    output_rows = []
    
    with open(input_csv, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            product_name = row.get('製品名', '').strip()
            if not product_name: 
                continue
            
            # --- 1. ★区分 の判定 (空欄エラー対策・表記揺れ対応付き) ---
            # 元の値を文字列として取得し、前後の空白を削除
            kubun_val = str(row.get('指定濫用(＊：同ﾌﾞﾗﾝﾄﾞ内に対象含む)', '')).strip()
            
            # 「対象外」という文字が含まれている、または「△」「×」「一般用検査薬」の場合は対象外とする
            if '対象外' in kubun_val or kubun_val in ['△', '×', '一般用検査薬']:
                kubun_text = '対象外'
            else:
                # 上記以外（「〇」「＊〇」、空欄など）は一律「対象」として扱う
                kubun_text = '対象'

            # --- 2. ★容量 の自動判定 (正解ルート: JSON解析) ---
            capacity_text = '小容量' # デフォルト
            
            # メジコン等、補足欄や注釈から混在が明らかな場合の先行判定
            note_text = row.get('注釈･補足等', '') or ''
            if '混在' in note_text or 'メジコン' in product_name:
                capacity_text = '小容量/大容量 混在'
            elif kubun_text == '対象外':
                capacity_text = '小容量' # 対象外は一律小容量(制限なし)扱い
            else:
                # 付加情報_JSON列のパースを試みる
                extra_json_str = row.get('付加情報_JSON', '').strip()
                if extra_json_str:
                    try:
                        extra_data = json.loads(extra_json_str)
                        # JSON内の packages リストを確認
                        packages = extra_data.get('packages', [])
                        
                        if packages:
                            # パッケージ内に1つでも「大容量」の判定があれば大容量とする
                            has_large = any(pkg.get('capacity_judgment') == '大容量' for pkg in packages)
                            has_small = any(pkg.get('capacity_judgment') == '小容量' for pkg in packages)
                            
                            if has_large and has_small:
                                capacity_text = '小容量/大容量 混在'
                            elif has_large:
                                capacity_text = '大容量'
                            else:
                                capacity_text = '小容量'
                    except json.JSONDecodeError:
                        # JSONが壊れている、またはパースできない場合は「大小分岐」列でバックアップ
                        backup_val = row.get('大小分岐', '').strip()
                        if backup_val:
                            capacity_text = backup_val

            # --- 3. 販売ルール文言の自動生成 ---
            if kubun_text == '対象外':
                u18_sales = '通常通り販売可能（ネット購入も可）'
                o18_sales = '通常通り販売可能（ネット購入も可）'
                age_flag = '不要'
            elif capacity_text == '大容量':
                u18_sales = '法律で販売禁止'
                o18_sales = '購入理由の確認必須、ネット販売はビデオ通話が必須'
                age_flag = '販売禁止アラート'
            elif capacity_text == '小容量/大容量 混在':
                u18_sales = '容量により異なる（大容量は不可/小容量は1個のみ可）'
                o18_sales = '容量により異なる（大容量はビデオ通話必須/小容量は他店確認）'
                age_flag = '要容量確認'
            else: # 小容量
                u18_sales = '1個のみ可（対面で年齢・氏名・他店状況確認必須）'
                o18_sales = '1個のみ可（他店状況確認必須）'
                age_flag = '要確認'

            # --- 4. 出力行のマッピング ---
            out_row = {
                'MEMBER_ID': '', 
                'SHOP_ID': '', 
                'GOODS_ID': '', 
                '★区分': kubun_text,
                '★容量': capacity_text,
                'GOODS_NAME': f"☆{product_name}",
                'GOODS_NAME_KANA': '', 
                'UNIT_PRICE': '', 
                'TAX_KIND': '', 
                'DEPARTMENT_ID': '', 
                'TAX_RATE_NO': '', 
                'ALL_FLG': '', 
                'DEL_FLG': '', 
                'UPDATE_DAY': row.get('更新日', ''),
                'SPECIAL_PRICE1': '', 
                'SPECIAL_PRICE2': '', 
                'ABUSE_KIND': '', 
                'ABUSE_SIZE': '',
                '18歳未満（未成年）への販売': u18_sales,
                '18歳以上（成人）への販売': o18_sales,
                '成分': row.get('対象成分含有フラグ', ''),
                '年齢確認フラグ': age_flag,
                '備考': row.get('注釈･補足等', '')
            }
            output_rows.append(out_row)

    # 書き出し
    with open(output_csv, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"✅ 提出用マスタ {output_csv} を作成しました。")

if __name__ == "__main__":
    build_export_csv()
