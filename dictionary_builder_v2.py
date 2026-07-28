import markdown
import re
import os

# =========================================================
# 1. 現場実務 & 薬理に完全対応したキーワード定義
# =========================================================
INDEX_KEYWORDS = {
    # 【成分：あ行】
    "アセトアミノフェン": "あ行（成分）",
    "アリルイソプロピルアセチル尿素": "あ行（成分）",
    "アンナカ": "あ行（成分）",
    "エフェドリン": "あ行（成分）",
    # 【成分：か行～さ行】
    "カフェイン": "か行（成分）",
    "クロルフェニラミン": "か行（成分）",
    "コデイン": "か行（成分）",
    "ジヒドロコデイン": "さ行（成分）",
    "ジフェンヒドラミン": "さ行（成分）",
    # 【成分：た行～は行】
    "デキストロメトルファン": "た行（成分）",
    "トラベルミン": "た行（成分）",
    "プソイドエフェドリン": "は行（成分）",
    "プロメタジン": "は行（成分）",
    "ブロモバレリル尿素": "は行（成分）",
    # 【成分：ま行～ら行】
    "メチルエフェドリン": "ま行（成分）",
    "ラメルテオン": "ら行（成分）",
    "ロゼレム": "ら行（成分）",
    # 【ブランド・商品名】
    "パブロン": "ブランド・商品名",
    "ブロン": "ブランド・商品名",
    "ベンザブロック": "ブランド・商品名",
    "パイロン": "ブランド・商品名",
    "ドリエル": "ブランド・商品名",
    "メジコン": "ブランド・商品名",
    "ウット": "ブランド・商品名",
    "葛根湯": "ブランド・商品名",
    # 【法令・運用・概念ルール】
    "18歳未満": "法令・現場ルール",
    "大容量": "法令・現場ルール",
    "複数個": "法令・現場ルール",
    "身分証明書": "法令・現場ルール",
    "購入理由": "法令・現場ルール",
    "抗コリン": "薬理・安全性コンセプト",
    "ドーピング": "薬理・安全性コンセプト",
    "海外旅行": "薬理・安全性コンセプト",
    "零売": "薬理・安全性コンセプト",
    "帯状疱疹": "薬理・安全性コンセプト",
    "ステロイド外用": "薬理・安全性コンセプト",
    "アズノール": "薬理・安全性コンセプト",
}

def convert_txt_to_dictionary(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"⚠️ エラー: 入力ファイル {input_path} が見つかりません。")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    toc_lines = []
    body_lines = []
    index_map = {kw: [] for kw in INDEX_KEYWORDS.keys()}
    
    # ★ 変更点1-A: 各セクションの文字数カウント用辞書を追加
    section_char_count = {}
    
    current_section_title = "冒頭"
    current_anchor = "top"
    in_table = False
    table_col_count = 0
    
    # 章カウンタ (堅牢なID生成用)
    sec_count = 0
    sub_count = 0
    skip_header_toc = True

    for raw_line in lines:
        line = raw_line.strip()
        
        # 空行処理とテーブル終了判定
        if not line:
            if in_table:
                body_lines.append("\n")
                in_table = False
                table_col_count = 0
            body_lines.append("\n")
            continue

        # 冒頭の目次をスキップし、「第1章」からコンパイル開始
        if ("第1章:" in line or "■第1章:" in line or "第1章：" in line) and skip_header_toc:
            skip_header_toc = False

        if skip_header_toc:
            continue

        # 1. 区切り線の正規化 (水平線へ)
        if re.match(r'^[=_\-]{8,}$', line):
            if in_table:
                in_table = False
                table_col_count = 0
            body_lines.append("\n---\n")
            continue

        # 2. 大見出し (##) の検出: 第○章、付録、作業報告等
        h2_match = re.match(r'^(?:\s*)?(第[0-9]+章:.*|第[0-9]+章：.*|【付録】.*|【エクセル作業報告】.*|【法改正の重要ポイントまとめ】.*|【未実施】.*|【重要:過量服薬における.*|【拡張案】.*)', line)
        if h2_match:
            if in_table:
                in_table = False
                table_col_count = 0
            sec_count += 1
            title = h2_match.group(1).replace("■", "").strip()
            anchor = f"sec-{sec_count}"
            current_section_title = title
            current_anchor = anchor
            
            # ★ 変更点2-A: 文字列でなくタプル(種別, タイトル, アンカー)で保持
            toc_lines.append(("h2", title, anchor))
            body_lines.append(f'\n---\n<a id="{anchor}"></a>\n## {title}\n')
            continue

        # 3. 中見出し (###) の検出: 節番号、お声がけ例、重要テーマ等
        h3_match = re.match(r'^([0-9]+-[0-9]+\.\s+.*|[0-9]+\.\s+[^: ]{2,}|[▲■★☆💡]?\s*【[^】]+】|[👑🚨💡]\s*.*)$', line)
        if h3_match and len(line) < 60: # 長すぎる文の誤認を防止
            if in_table:
                in_table = False
                table_col_count = 0
            sub_count += 1
            title = line.strip()
            anchor = f"sub-{sub_count}"
            current_section_title = title
            current_anchor = anchor
            
            # ★ 変更点2-B: インデント有無を判定してタプルで保持
            indent = "h3-indent" if (re.match(r'^[0-9]+-[0-9]+\.', title) or title.startswith("(") or title.startswith("（")) else "h3"
            toc_lines.append((indent, title, anchor))
                
            body_lines.append(f'\n<a id="{anchor}"></a>\n### {title}\n')
            continue

        # --- ここに来た行は「本文」または「表データ」なので文字数をカウントする ---
        section_char_count[current_anchor] = section_char_count.get(current_anchor, 0) + len(line)

        # 4. タブ区切りデータ (表・マトリクス) のスマートパース
        if '\t' in raw_line:
            cells = [c.strip() for c in raw_line.split('\t') if c.strip() != ""]
            # 1セルしかない行は表とみなさず通常出力
            if len(cells) <= 1:
                body_lines.append(line + "\n")
                continue
                
            row_str = "| " + " | ".join(cells) + " |"
            if not in_table or len(cells) != table_col_count:
                table_col_count = len(cells)
                body_lines.append("\n" + row_str)
                separator = "|" + "|".join(["---"] * table_col_count) + "|"
                body_lines.append(separator)
                in_table = True
            else:
                body_lines.append(row_str)
            continue
        else:
            if in_table:
                body_lines.append("\n")
                in_table = False
                table_col_count = 0

        # 5. 本文スキャンによる索引 (インデックス) の収集
        for kw in INDEX_KEYWORDS.keys():
            if kw in line and current_section_title not in [item[0] for item in index_map[kw]]:
                index_map[kw].append((current_section_title, current_anchor))

        # 通常テキストの出力 (箇条書き記号などの微調整)
        if line.startswith("・") or line.startswith("* "):
            clean_line = re.sub(r'^[\*・]\s*', '- ', line)
            body_lines.append(clean_line + "\n")
        else:
            body_lines.append(line + "\n")

    # =========================================================
    # 巻末: キーワード逆引き索引 (インデックス) の構築
    # =========================================================
    index_lines = ["\n---\n<a id=\"index-top\"></a>\n## 📖 【巻末索引】キーワード逆引き辞書\n"]
    sorted_kws = sorted(INDEX_KEYWORDS.items(), key=lambda x: (x[1], x[0]))
    current_cat = ""
    
    for kw, cat in sorted_kws:
        if cat != current_cat:
            current_cat = cat
            index_lines.append(f"\n### ■ {current_cat}\n")
            
        locs = index_map[kw]
        if locs:
            links_str = " / ".join([f"[{sec}](#{anc})" for sec, anc in locs[:6]])
            index_lines.append(f"- **{kw}** : {links_str}")
        else:
            index_lines.append(f"- **{kw}** : *(本文内該当なし)*")

    # =========================================================
    # ★ 変更点2-C: 目次(toc)の文字列化（文字数と薄いフラグの付与）
    # =========================================================
    toc_str_lines = []
    for kind, title, anchor in toc_lines:
        cnt = section_char_count.get(anchor, 0)
        flag = " ⚠️薄い" if cnt < 150 else ""
        if kind == "h2":
            toc_str_lines.append(f"- **[{title}](#{anchor})** `{cnt}字`{flag}")
        elif kind == "h3-indent":
            toc_str_lines.append(f"  - [{title}](#{anchor}) `{cnt}字`{flag}")
        else:
            toc_str_lines.append(f"- [{title}](#{anchor}) `{cnt}字`{flag}")

    # =========================================================
    # 最終Markdownの合成と保存
    # =========================================================
    final_output = (
        "# 📘 指定濫用防止医薬品 販売対応・薬理電子辞書\n\n"
        + "> **【利用ガイド】** 本書は現場の薬剤師・登録販売者が店頭でのアセスメントや受診勧奨、トリアージに用いる電子辞書です。 "
        + "目次や巻末索引のリンクをクリックすることで、必要なエビデンスや対応スクリプトへ瞬時にジャンプできます。\n\n"
        + "## 🔍 【全体構造・目次】\n"
        + "\n".join(toc_str_lines) + "\n\n"
        + "- **[⬇️ 巻末キーワード逆引き索引へジャンプ](#index-top)**\n\n"
        + "---\n"
        + "".join(body_lines)
        + "".join(index_lines)
    )

    # 1. Markdownファイルを保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_output)

    # 2. Markdownを美しいスタイルのHTMLファイルに自動変換して保存
    html_content = markdown.markdown(final_output, extensions=['tables', 'fenced_code'])

    final_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>指定濫用防止医薬品 販売対応・薬理電子辞書</title>
    <style>
        body {{ font-family: sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; background-color: #FAFAFA; }}
        h1, h2, h3 {{ color: #217346; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; background: #FFF; }}
        th, td {{ border: 1px solid #ccc; padding: 8px 12px; text-align: left; }}
        th {{ background: #F3F2F1; }}
        blockquote {{ background: #F9F9F9; border-left: 4px solid #217346; margin: 0; padding: 10px 15px; }}
        a {{ color: #2B579A; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

    html_output_path = output_path.replace(".md", ".html")
    with open(html_output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"★ コンパイル成功: Markdown ({output_path}) および HTML ({html_output_path}) が正常に生成されました！")

if __name__ == "__main__":
    convert_txt_to_dictionary("濫用防止.txt", "pharma_dictionary_compiled.md")