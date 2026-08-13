import os
import json
import re
import time
import hashlib
from google import genai
from google.genai import types

def atomic_chunking(text):
    """メモを意味の最小単位 (アトム) に簡易分割する関数"""
    # 見出しや空行などで分割（実際のテキストに合わせて調整してください）
    raw_chunks = re.split(r'\n\s*\n|###=+', text)
    chunks = [c.strip() for c in raw_chunks if len(c.strip()) > 10]
    return chunks

def generate_chunk_id(file_name, chunk_text):
    """ファイル名とテキスト内容から一意のハッシュIDを生成 (重複完全防止用)"""
    unique_str = f"{file_name}::{chunk_text}"
    return hashlib.md5(unique_str.encode('utf-8')).hexdigest()

def process_chunk_with_llm(client, chunk_text, toc_tree, max_retries=3):
    """LLMの役割: 柔軟なテキスト書き換えと動的ルーティング (自動リトライ機能付き)"""
    
    prompt = f"""
    以下のテキストは、薬学・医療・店舗オペレーションに関する断片的なドキュメントの一部です。
    このテキストを解析し、以下の3つの処理を行い、必ず指定された【JSONフォーマット】のみで出力してください。

    1. 【自己完結化】:
    テキスト内に「同薬」「それ」「前述の」などの代名詞がある場合、文脈を補完して、このテキスト1塊だけで意味が100%通じる客観的な文章に書き換えてください。

    2. 【メタデータタグ化】:
    テキストに関連する「成分名」「カテゴリ」を抽出し、タグ化してください。

    3. 【動的ルーティング】:
    以下の【現在の目次ツリー】を参照し、このテキストを配置する最適な場所を決定してください。
    - 既存の枠にピッタリ収まる場合は decision を "existing" とし、target_parent_id にそのセクションIDを指定してください。
    - 既存の枠に収まらない（独立した階層として際立たせるべき）と判断した場合は decision を "create_new" とし、新設する見出しのタイトルを提案してください。

    【現在の目次ツリー】
    {json.dumps(toc_tree, ensure_ascii=False, indent=2)}

    ---
    対象テキスト:
    {chunk_text}
    ---

    【JSONフォーマット】
    {{
      "completed_text": "補完された自己完結文をここに記述",
      "tags": {{
        "ingredients": ["成分名1", "成分名2"],
        "categories": ["カテゴリ1", "カテゴリ2"]
      }},
      "routing": {{
        "decision": "create_new または existing", 
        "target_parent_id": "existingの場合は、配置する既存のセクションID（例: sec-1）。create_newの場合は空文字",
        "new_section_id": "create_newの場合のみ、重複しない新しいIDを自作して記述（例: sec-4）。existingの場合は空文字",
        "new_section_title": "create_newの場合のみ、具体的な新しい見出しを記述。existingの場合は空文字",
        "reason_for_structure": "なぜその構造が最適と判断したか理由"
      }}
    }}
    """

    for attempt in range(1, max_retries + 1):
        try:
            # テスト時は 'gemini-2.5-flash' を推奨。本番清書時は 'gemini-2.5-pro'
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            raw_response = response.text.strip()
            
            # 【安全装置】LLM特有の ```json ～ ``` という余計なマークダウンを剥がす
            if raw_response.startswith("```json"):
                raw_response = raw_response[7:]
            if raw_response.startswith("```"):
                raw_response = raw_response[3:]
            if raw_response.endswith("```"):
                raw_response = raw_response[:-3]
                
            raw_response = raw_response.strip()

            return json.loads(raw_response)

        except Exception as e:
            wait_time = attempt * 3 # 1回目3秒、2回目6秒、3回目9秒
            print(f"  APIエラー (試行 {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                print(f"  -> {wait_time}秒後に再試行します...")
                time.sleep(wait_time)
            else:
                print("  -> 最大リトライ回数に達しました。")
                return None

def load_or_create_toc(toc_file_path):
    """目次ツリー(toc_tree.json)を読み込む。無ければ初期テンプレートを作成する"""
    if os.path.exists(toc_file_path):
        with open(toc_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # 初期ツリーの定義
        initial_toc = {
            "sec-1": {"title": "第1章: なぜルールが厳しくなったのか？（法改正の背景）", "children": []},
            "sec-2": {"title": "第2章: 販売ルールの基本（誰に・何を・いくつ売れるか）", "children": []},
            "sec-3": {"title": "第3章: 具体的なレジ対応と「お声がけ」スクリプト", "children": []}
        }
        with open(toc_file_path, "w", encoding="utf-8") as f:
            json.dump(initial_toc, f, ensure_ascii=False, indent=2)
        return initial_toc

def main():
    # 💡 【完全版】 Vertex AI（Google Cloud）の無制限レーンを使用
    print("🚀 Vertex AI (Google Cloud) 経由でGeminiクライアントを初期化します...")
    client = genai.Client(
        vertexai=True,
        project="project-efa0947e-f31b-4065-a5e",
        location="us-central1"
    )

    memo_dir = "my_memos"
    output_db_file = "structured_knowledge_db.json"
    toc_file_path = "toc_tree.json"

    if not os.path.exists(memo_dir):
        print(f"フォルダ '{memo_dir}' を作成しました。対象のテキストファイルを配置してください。")
        os.makedirs(memo_dir, exist_ok=True)
        return

    files = sorted([f for f in os.listdir(memo_dir) if f.endswith('.txt')])
    if not files:
        print(f"'{memo_dir}' フォルダの中に解析対象の .txt ファイルがありません。")
        return

    # 外部の目次ツリーを読み込む
    toc_tree = load_or_create_toc(toc_file_path)

    # 既存DBの読み込みとハッシュIDの集合作成
    database = []
    if os.path.exists(output_db_file):
        try:
            with open(output_db_file, "r", encoding="utf-8") as f:
                database = json.load(f)
            print(f"📦 既存のデータベースを読み込みました。現在の保存件数: {len(database)}件")
        except Exception:
            database = []

    processed_ids = {item.get("chunk_id") for item in database if "chunk_id" in item}

    print(f"\n🚀 動的ルーティング型パイプラインを開始します...\n" + "-"*50)

    for file_name in files:
        file_path = os.path.join(memo_dir, file_name)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = atomic_chunking(content)
        total_chunks_in_file = len(chunks)

        for idx, chunk in enumerate(chunks, 1):
            c_id = generate_chunk_id(file_name, chunk)

            if c_id in processed_ids:
                continue

            print(f"🔄 [{file_name}] チャンク [{idx}/{total_chunks_in_file}] を処理中...")
            
            # AIに目次ツリーを渡してルーティングを委ねる
            structured_data = process_chunk_with_llm(client, chunk, toc_tree)

            if structured_data:
                structured_data["chunk_id"] = c_id
                structured_data["source_file"] = file_name
                
                if "tags" not in structured_data or not isinstance(structured_data["tags"], dict):
                    structured_data["tags"] = {}
                
                structured_data["tags"]["verified"] = False
                structured_data["tags"]["source_type"] = "LLM生成(未検証)"

# 💡 【完全版】 LLMの判定を目次ツリーにガッチャンコする処理
                routing_info = structured_data.get("routing", {})
                decision = routing_info.get("decision", "unknown")
                target_id = routing_info.get("target_parent_id") # 既存セクションのIDを取得
                
                if decision == "create_new":
                    new_sec_id = routing_info.get("new_section_id")
                    new_sec_title = routing_info.get("new_section_title")
                    
                    if new_sec_id and new_sec_title:
                        # 辞書型で初期構造を作成し、最初の子要素としてこのデータIDを格納
                        toc_tree[new_sec_id] = {
                            "title": new_sec_title,
                            "children": [c_id]
                        }
                        print(f"   🌱 目次ツリーが自動拡張されました: [{new_sec_id}] {new_sec_title}")
                
                elif decision == "existing" and target_id:
                    # 💡 【重要追加】指定された既存の章の「children」にデータIDを追記
                    if target_id in toc_tree:
                        toc_tree[target_id]["children"].append(c_id)
                        print(f"   📌 既存セクション [{target_id}] の配下にマッピングしました")
                    else:
                        # 万が一LLMが存在しない謎のIDを返してきた場合の救済措置（セーフティ）
                        toc_tree["sec-1"]["children"].append(c_id)
                        print(f"   ⚠️ 指定ID [{target_id}] が見つからないため、第1章に救済配置しました")
                
                database.append(structured_data)
                processed_ids.add(c_id)

                # 💡 【完全版】 本体と目次ツリーの「ダブル即時保存」
                with open(output_db_file, "w", encoding="utf-8") as f:
                    json.dump(database, f, ensure_ascii=False, indent=2)
                
                with open(toc_file_path, "w", encoding="utf-8") as f:
                    json.dump(toc_tree, f, ensure_ascii=False, indent=2)
                
                print(f"   ✨ ルーティング [{decision}] で保存完了！ (現在のDB総件数: {len(database)}件)")
            else:
                print("\n❌ 連続してAPIエラーが発生したため、処理を安全に停止します。")
                return

            # 💡 【完全版】 Vertex AIの高速レーン用のウェイト（4.5秒 → 0.5秒）
            time.sleep(0.5)

    print("\n" + "="*50)
    print(f"🎉 すべての処理が正常に完了しました！ 成果物ファイル: {output_db_file}")

if __name__ == "__main__":
    main()