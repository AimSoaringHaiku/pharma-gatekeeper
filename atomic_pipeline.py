import os
import json
import re
import time
from google import genai
from google.genai import types

def atomic_chunking(text):
    """メモを意味の最小単位（アトム）に簡易分割する関数"""
    raw_chunks = re.split(r'\n\s*\n|###|=+', text)
    chunks = [c.strip() for c in raw_chunks if len(c.strip()) > 10]
    return chunks

def process_chunk_with_llm(client, chunk_text):
    """【LLMの役割】: 柔軟なテキスト書き換えと、意味に基づくタグの抽出"""
    
    prompt = f"""
以下のテキストは、薬学・医療に関する断片的なメモ、またはドキュメントの一部です。
このテキストを解析し、以下の2つの処理を行い、必ず指定された【JSONフォーマット】のみで出力してください。

1. 【自己完結化(completed_text)】: 
   テキスト内に「同薬」「それ」「前述の」などの代名詞がある場合、文脈を補完して、このテキスト1塊だけで意味が100%通じる客観的な文章に書き換えてください。主語が抜けている場合は補完してください。
2. 【メタデータタグ化(tags)】:
   テキストに関連する「成分名」「カテゴリ（妊婦、乱用、禁忌、法規制など）」「重要度（高、中、低）」を抽出し、タグ化してください。

---
対象テキスト:
{chunk_text}
---

【JSONフォーマット】
{{
  "completed_text": "補完された自己完結文をここに記述",
  "tags": {{
    "ingredients": ["成分名1", "成分名2"],
    "categories": ["カテゴリ1", "カテゴリ2"],
    "priority": "高"
  }}
}}
"""
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"APIエラーまたはJSONパースエラー: {e}")
        return None

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("エラー: Codespaces Secretsに 'GEMINI_API_KEY' が設定されていないか、環境変数が読み込まれていません。")
        return

    client = genai.Client(api_key=api_key)
    
    memo_dir = "my_memos"
    output_db_file = "structured_knowledge_db.json"
    
    if not os.path.exists(memo_dir):
        print(f"フォルダ '{memo_dir}' を作成しました。ここにメモ（.txt）を入れてください。")
        os.makedirs(memo_dir, exist_ok=True)

    files = [f for f in os.listdir(memo_dir) if f.endswith('.txt')]
    if not files:
        print(f"'{memo_dir}' フォルダの中に解析対象の .txt ファイルがありません。サンプルを作成します。")
        with open(os.path.join(memo_dir, "sample_memo.txt"), "w", encoding="utf-8") as f:
            f.write("メジコンODの主犯について。\n大量摂取により、シグマ受容体だけでなくNMDA受容体拮抗作用が発現する。\nこれにより、解離性幻覚、錯乱、激しい興奮などを引き起こす。2026年5月の法改正で指定乱用医薬品に追加された。")
        files = [f for f in os.listdir(memo_dir) if f.endswith('.txt')]

    database = []

    print(f"最新SDK稼働・安全回避型パイプラインを開始します... 対象ファイル数: {len(files)}")
    for file_name in files:
        file_path = os.path.join(memo_dir, file_name)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        chunks = atomic_chunking(content)
        
        for idx, chunk in enumerate(chunks):
            print(f" -> {file_name} の チャンク [{idx+1}/{len(chunks)}] を処理中...")
            structured_data = process_chunk_with_llm(client, chunk)
            
            if structured_data:
                structured_data["source_file"] = file_name
                if "tags" not in structured_data or not isinstance(structured_data["tags"], dict):
                    structured_data["tags"] = {}
                structured_data["tags"]["verified"] = False
                structured_data["tags"]["source_type"] = "LLM生成（未検証）"
                database.append(structured_data)

            if idx < len(chunks) - 1 or file_name != files[-1]: 
                print("    ...レートリミット回避のため4.5秒待機します...")
                time.sleep(4.5)

    with open(output_db_file, "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)
    
    print(f"\nすべてのメモの構造化が安全に完了しました！")
    print(f"成果物ファイル: {output_db_file}")

if __name__ == "__main__":
    main()
