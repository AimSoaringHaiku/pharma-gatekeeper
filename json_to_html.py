import json
import os

def create_html_viewer():
    db_file = "structured_knowledge_db.json"
    html_file = "viewer.html"
    
    if not os.path.exists(db_file):
        print(f"❌ エラー: '{db_file}' が見つかりません。")
        return

    # JSONデータの読み込み
    with open(db_file, "r", encoding="utf-8") as f:
        try:
            database = json.load(f)
        except json.JSONDecodeError:
            print("❌ エラー: JSONファイルの形式が不正です。")
            return

    # HTMLのヘッダーとCSSスタイル設定
    html_content = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>アトミック化メモ ビュワー</title>
        <style>
            body { font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif; background-color: #f4f7f6; color: #333; padding: 20px; max-width: 1000px; margin: 0 auto; }
            h1 { text-align: center; color: #2c3e50; }
            .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid #3498db; }
            .meta { font-size: 0.85em; color: #7f8c8d; margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 8px; }
            .text-content { font-size: 1.1em; line-height: 1.6; margin-bottom: 15px; }
            .tags { margin-top: 10px; }
            .tag { display: inline-block; background: #e8f4f8; color: #2980b9; padding: 4px 10px; border-radius: 15px; font-size: 0.85em; margin-right: 6px; margin-bottom: 6px; border: 1px solid #bce0ee; }
            .tag-category { font-weight: bold; margin-right: 3px; color: #16a085; }
        </style>
    </head>
    <body>
        <h1>📚 構造化ナレッジベース ({count}件)</h1>
    """
    
    # 件数をヘッダーに埋め込むための置換
    html_content = html_content.replace("{count}", str(len(database)))

    # 各チャンクのデータをHTMLカードに変換
    for item in database:
        text = item.get("completed_text", "（テキストなし）")
        source = item.get("source_file", "不明なソース")
        
        routing_info = item.get("routing", {})
        decision = routing_info.get("decision", "unknown")
        target_id = routing_info.get("target_parent_id", "")
        new_id = routing_info.get("new_section_id", "")
        
        # ルーティング情報の表示整理
        routing_display = f"新規作成 [{new_id}]" if decision == "create_new" else f"既存追加 [{target_id}]"

        # タグの処理
        tags_html = ""
        tags_dict = item.get("tags", {})
        for category, tag_values in tags_dict.items():
            if isinstance(tag_values, list):
                for tag in tag_values:
                    if tag: # 空文字をスキップ
                        tags_html += f'<span class="tag"><span class="tag-category">{category}:</span>{tag}</span>'
            elif isinstance(tag_values, str) and tag_values:
                tags_html += f'<span class="tag"><span class="tag-category">{category}:</span>{tag_values}</span>'

        # カードHTMLの追加
        html_content += f"""
        <div class="card">
            <div class="meta">
                📄 <b>{source}</b> | 🔄 ルーティング: {routing_display}
            </div>
            <div class="text-content">
                {text}
            </div>
            <div class="tags">
                {tags_html}
            </div>
        </div>
        """

    # HTMLのフッター
    html_content += """
    </body>
    </html>
    """

    # ファイルに書き出し
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"✨ 成功: '{html_file}' を作成しました！")
    print("ブラウザでこのファイルをダブルクリックして開いてみてください。")

if __name__ == "__main__":
    create_html_viewer()