import os
import json
import re
import time
import hashlib
from google import genai
from google.genai import types

def atomic_chunking(text):
    """メモを意味の最小単位（アトム）に簡易分割する関数"""
    raw_chunks = re.split(r'\n\s*\n|###|=+', text)
    chunks = [c.strip() for c in raw_chunks if len(c.strip()) > 10]
    return chunks

def generate_chunk_id(file_name, chunk_text):
    """ファイル名とテキスト内容から一意のハッシュIDを生成（重複完全防止用）"""
    unique_str = f"{file_name}::{chunk_text}"
    return hashlib.md5(unique_str.encode('utf-8')).hexdigest()

def process_chunk_with_llm(client, chunk_text, max_retries=3):
    """【LLMの役割】: 柔軟なテキスト書き換えとタグ抽出（自動リトライ機能付き）"""
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
    # 💡 【改善点2】APIエラー時の自動指数バックオフ・リトライ機構
    for attempt in range(1, max_retries + 1):
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
            # 503や一瞬のネットワークのゆらぎに対応
            wait_time = attempt * 3  # 1回目3秒、2回目6秒、3回目9秒
            print(f"   ⚠️ APIエラー（試行 {attempt}/{max_retries}）: {e}")
            if attempt < max_retries:
                print(f"       ➔ {wait_time}秒後に再試行します...")
                time.sleep(wait_time)
            else:
                print("       ➔ 最大リトライ回数に達しました。")
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
        print(f"フォルダ '{memo_dir}' を作成しました。")
        os.makedirs(memo_dir, exist_ok=True)
        return

    # ファイル名をソートしてOSによる順序のブレを防止
    files = sorted([f for f in os.listdir(memo_dir) if f.endswith('.txt')])
    if not files:
        print(f"'{memo_dir}' フォルダの中に解析対象の .txt ファイルがありません。")
        return

    # 既存のデータベースがあれば読み込む
    database = []
    if os.path.exists(output_db_file):
        try:
            with open(output_db_file, "r", encoding="utf-8") as f:
                database = json.load(f)
            print(f"📦 既存のデータベースを読み込みました。現在の保存件数: {len(database)}件")
        except Exception:
            database = []

    # 💡 【改善点1】すでに処理済みの「ハッシュID」の集合(Set)を作成して高速判定
    processed_ids = {item.get("chunk_id") for item in database if "chunk_id" in item}

    print(f"\n🚀 高信頼性・途中保存型パイプラインを開始します...\n" + "-"*50)
    
    for file_name in files:
        file_path = os.path.join(memo_dir, file_name)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        chunks = atomic_chunking(content)
        total_chunks_in_file = len(chunks)
        
        for idx, chunk in enumerate(chunks, 1):
            # チャンク固有の一意なハッシュIDを生成
            c_id = generate_chunk_id(file_name, chunk)
            
            # 💡 【改善点1】件数ではなく「ハッシュID」で完全重複チェック（絶対にズレない）
            if c_id in processed_ids:
                continue
                
            # 💡 【改善点3】ファイル名とファイル内の正確な進捗ログ表示
            print(f"🔄 [{file_name}] チャンク [{idx}/{total_chunks_in_file}] を処理中...")
            structured_data = process_chunk_with_llm(client, chunk)
            
            if structured_data:
                # Python側での統治タグの強制上書きとID付与（防壁）
                structured_data["chunk_id"] = c_id
                structured_data["source_file"] = file_name
                if "tags" not in structured_data or not isinstance(structured_data["tags"], dict):
                    structured_data["tags"] = {}
                structured_data["tags"]["verified"] = False
                structured_data["tags"]["source_type"] = "LLM生成（未検証）"
                
                database.append(structured_data)
                processed_ids.add(c_id)
                
                # 1件成功するたびに、その場で即時書き出し保存
                with open(output_db_file, "w", encoding="utf-8") as f:
                    json.dump(database, f, ensure_ascii=False, indent=2)
                
                print(f"   ✨ 保存完了！ (現在のDB総件数: {len(database)}件)")
            else:
                print("\n❌ 連続してAPIエラー（または503大混雑）が発生したため、処理を一時安全に停止します。")
                print("   ここまで処理されたデータは完全に保存されています。しばらく時間を置いて再実行してください。")
                return

            # 無料枠リミット回避のウェイト
            time.sleep(4.5)

    print("\n" + "="*50)
    print(f"🎉 すべての処理が正常に完了しました！ 成果物ファイル: {output_db_file}")

if __name__ == "__main__":
    main()
