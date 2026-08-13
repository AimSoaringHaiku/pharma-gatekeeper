import json
import os

def create_tree_html_viewer():
    db_file = "structured_knowledge_db.json"
    toc_file = "toc_tree.json"
    html_file = "tree_viewer.html"
    
    # 1. ファイルの存在確認
    if not os.path.exists(db_file) or not os.path.exists(toc_file):
        print("❌ エラー: DBファイルまたは目次ファイルが見つかりません。")
        return

    # 2. データの読み込み
    with open(db_file, "r", encoding="utf-8") as f:
        database = json.load(f)
    with open(toc_file, "r", encoding="utf-8") as f:
        toc_tree = json.load(f)

    # 3. 検索を爆速にするため、IDをキーにした辞書（マップ）を作成
    chunk_map = {item.get("chunk_id"): item for item in database if "chunk_id" in item}

    # 4. HTML・CSSのベース
    html_content = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>📚 統合ナレッジマスター</title>
        <style>
            body { font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #f8f9fa; color: #333; margin: 0; display: flex; }
            
            /* 左側の目次サイドバー */
            .sidebar { width: 300px; height: 100vh; background-color: #2c3e50; color: white; position: fixed; overflow-y: auto; padding: 20px; box-sizing: border-box; }
            .sidebar h2 { margin-top: 0; font-size: 1.2em; border-bottom: 2px solid #34495e; padding-bottom: 10px; }
            .sidebar ul { list-style: none; padding: 0; margin: 0; }
            .sidebar li { margin-bottom: 10px; }
            .sidebar a { color: #ecf0f1; text-decoration: none; font-size: 0.95em; display: block; padding: 5px; border-radius: 4px; transition: background 0.2s; }
            .sidebar a:hover { background-color: #34495e; }
            
            /* 右側のメインコンテンツ */
            .main-content { margin-left: 300px; padding: 40px; width: calc(100% - 300px); box-sizing: border-box; max-width: 1000px; }
            .section-block { margin-bottom: 60px; }
            .section-title { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-bottom: 25px; }
            .empty-text { color: #7f8c8d; font-style: italic; }
            
            /* カードデザイン */
            .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #3498db; }
            .text-content { font-size: 1.05em; line-height: 1.7; margin-bottom: 15px; }
            .tags { margin-top: 10px; }
            .tag { display: inline-block; background: #e8f4f8; color: #2980b9; padding: 4px 10px; border-radius: 15px; font-size: 0.8em; margin-right: 6px; margin-bottom: 6px; border: 1px solid #bce0ee; }
            .tag-category { font-weight: bold; margin-right: 3px; color: #16a085; }
        </style>
    </head>
    <body>
    """

    # 5. サイドバー（目次）の生成
    sidebar_html = "<div class='sidebar'><h2>📑 全体目次</h2><ul>"
    for sec_id, sec_data in toc_tree.items():
        title = sec_data.get("title", f"名称未設定 ({sec_id})")
        # 目次のリンクをクリックすると、右側の該当箇所へジャンプする仕組み
        sidebar_html += f"<li><a href='#{sec_id}'>{title}</a></li>"
    sidebar_html += "</ul></div>"

    # 6. メインコンテンツ（記事本体）の生成
    main_html = "<div class='main-content'>"
    for sec_id, sec_data in toc_tree.items():
        title = sec_data.get("title", f"名称未設定 ({sec_id})")
        children = sec_data.get("children", [])
        
        main_html += f"<div class='section-block' id='{sec_id}'>"
        main_html += f"<h1 class='section-title'>{title}</h1>"
        
        if not children:
            main_html += "<p class='empty-text'>※この章にはまだテキストが紐づいていません。</p>"
        else:
            for c_id in children:
                chunk = chunk_map.get(c_id)
                if chunk:
                    text = chunk.get("completed_text", "")
                    
                    # タグの生成
                    tags_html = ""
                    for category, tag_values in chunk.get("tags", {}).items():
                        if isinstance(tag_values, list):
                            for tag in tag_values:
                                if tag:
                                    tags_html += f'<span class="tag"><span class="tag-category">{category}:</span>{tag}</span>'
                        elif isinstance(tag_values, str) and tag_values:
                            tags_html += f'<span class="tag"><span class="tag-category">{category}:</span>{tag_values}</span>'

                    # カードの組み立て
                    main_html += f"""
                    <div class="card">
                        <div class="text-content">{text}</div>
                        <div class="tags">{tags_html}</div>
                    </div>
                    """
        main_html += "</div>" # セクション終了
    
    main_html += "</div>" # メインコンテンツ終了

    # 7. 結合して書き出し
    html_content += sidebar_html + main_html + "</body></html>"
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"✨ 成功: ツリー連動型ビュワー '{html_file}' を作成しました！")

if __name__ == "__main__":
    create_tree_html_viewer()