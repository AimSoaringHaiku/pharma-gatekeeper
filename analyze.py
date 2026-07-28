import re
import os

def get_east_asian_width_count(text):
    """日本語（全角）混じりの文字列でも綺麗に文字幅を揃えて出力するための補助関数"""
    count = 0
    for c in text:
        if ord(c) <= 0x7F:
            count += 1
        else:
            count += 2
    return count

def pad_text(text, target_width):
    """指定した文字幅になるように後ろにスペースを埋める"""
    current_width = get_east_asian_width_count(text)
    padding = max(0, target_width - current_width)
    return text + (" " * padding)

def main():
    file_path = "pharma_dictionary_compiled.html"
    
    # 1. ファイルの存在チェック
    if not os.path.exists(file_path):
        print(f"エラー: {file_path} が見つかりません。")
        return

    print(f"ファイルを読み込んでいます: {file_path}")
    with open(file_path, encoding="utf-8") as f:
        html = f.read()

    # 2. <h2>タグで分割
    sections = re.split(r'(?=<h2>)', html)
    
    TARGET_INGREDIENTS = ["エフェドリン","コデイン","ジヒドロコデイン","ブロモバレリル尿素",
                           "プソイドエフェドリン","メチルエフェドリン","デキストロメトルファン","ジフェンヒドラミン"]
    CATEGORIES = ["妊婦","授乳","運転","禁忌","相互作用","濫用","MOH","ドーピング","半減期"]

    # ヘッダーの出力（見出し幅は35文字分確保）
    header_title = pad_text("見出し", 35)
    print(f"{header_title} {'文字数':>6} {'成分言及':>8} {'カテゴリ言及':>10}")
    print("-" * 70)

    # 3. 各セクションの解析
    for sec in sections:
        m = re.match(r'<h2>(.*?)</h2>', sec, re.DOTALL)
        if not m:
            continue
            
        # タグの除去とトリミング
        title = re.sub(r'<.*?>', '', m.group(1)).strip()
        title = title[:15] + "..." if len(title) > 15 else title  # 長すぎる見出しは省略
        
        body = re.sub(r'<.*?>', '', sec)
        body = re.sub(r'\s+', '', body)  # 改行や不要な空白を除去して正確な文字数をカウント
        
        length = len(body)
        ing_hits = [i for i in TARGET_INGREDIENTS if i in body]
        cat_hits = [c for c in CATEGORIES if c in body]
        
        # 綺麗にフォーマットして表示
        formatted_title = pad_text(title, 35)
        print(f"{formatted_title} {length:>6} {len(ing_hits):>8} {len(cat_hits):>10}")

if __name__ == "__main__":
    main()
