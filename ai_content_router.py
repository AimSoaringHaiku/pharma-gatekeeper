import os
from google import genai
from google.genai import types

# =========================================================
# 1. 既存の辞書ツリー構造（マッピングのゴール）
# =========================================================
EXISTING_TREE_STRUCTURE = """
■第1章: 指定濫用防止医薬品の薬理・アセスメント
  ├── 1-1. エフェドリン類
  ├── 1-2. コデイン類
  ├── 1-3. 鎮静成分
  └── 1-4. 抗ヒスタミン成分
■第2章: 店頭トリアージと販売対応プロトコル
  ├── 2-1. 【法令・現場ルール】販売時の確認事項とトリアージ基準
  └── 2-2. 【お声がけスクリプト】状況別の適切な受診勧奨と断り方
■第3章: 主な対象ブランド・商品名一覧
"""

def route_and_compile_content(input_memo_path, output_md_path):
    # 1. 雑多な入力テキスト（メモやHTMLの切れ端など）の読み込み
    if not os.path.exists(input_memo_path):
        print(f"⚠️ エラー: 入力ファイル {input_memo_path} が見つかりません。")
        return

    with open(input_memo_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    print("🔄 Gemini API (Vertex AI) に接続し、テキストの解体と再配置を実行中...")

    # =========================================================
    # 2. Google Cloud Vertex AI クライアントの初期化
    # =========================================================
    # ※ご提示いただいたプロジェクトIDとリージョンを使用
    client = genai.Client(
        vertexai=True,
        project="project-efa0947e-f31b-4065-a5e",
        location="us-central1"
    )

    # =========================================================
    # 3. LLMへの指示（システムプロンプト）の構築
    # =========================================================
    system_instruction = f"""
あなたは医療・医薬品ドキュメントの専門編集者です。
提示する【新着テキスト・雑多なデータ】を、意味の連続した最小単位（アトミック・スニペット）に区切った上で、【既存の辞書ツリー構造】の最も適切な見出しの下へ自動で組み込んで（配置して）出力してください。

【実行プロトコル】
1. **最小スニペット化 (Atomic Chunking):**
   入力データを「薬理」「法令・現場ルール」「対応スクリプト」「注意事項」などの意味の最小単位に分割してください。その際、切り離しても意味が通じるように情報を補完しつつも、冗長になりすぎないよう「自然で読みやすい日本語」に整えてください。文脈から明らかな主語や単語（例：「18歳未満のお客様」「指定濫用防止医薬品」など）の不自然で過度な繰り返しは避けてください。
2. **自動マッピング (Routing):**
   分割した各スニペットの内容を吟味し、【既存の辞書ツリー構造】のどの見出しに配置するのが一番適切か判定してください。既存の枠に合わない場合は、最も適切な章の下に新しい中見出し（###）を自動生成して配置してください。
3. **出力:**
   配置済みの完成版マークダウンとして出力してください。Markdownの見出し構文（##, ###）を正しく使用し、各スニペットがどの見出しに組み込まれたかが一目でわかるように整理してください。
   余計な挨拶や説明は省き、マークダウン本文のみを出力してください。

【既存の辞書ツリー構造】
{EXISTING_TREE_STRUCTURE}
"""

    # =========================================================
    # 4. API呼び出しと推論の実行
    # =========================================================
    try:
        # 最新のGeminiモデルを指定（プロジェクトのクォータに合わせて調整可能）
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"【新着テキスト・雑多なデータ】\n{raw_text}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2, # 創造性より正確なルーティングを優先するため低めに設定
            )
        )
        
        generated_markdown = response.text.strip()
        
        # LLM特有の ```markdown ～ ``` という余計なラッパーを剥がす
        if generated_markdown.startswith("```markdown"):
            generated_markdown = generated_markdown[11:]
        if generated_markdown.startswith("```"):
            generated_markdown = generated_markdown[3:]
        if generated_markdown.endswith("```"):
            generated_markdown = generated_markdown[:-3]
        
        generated_markdown = generated_markdown.strip()

        # =========================================================
        # 5. 構造化されたMarkdownの保存
        # =========================================================
        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(generated_markdown)
            
        print(f"✨ 成功: AIによる自動振り分けが完了し、{output_md_path} に保存されました！")

    except Exception as e:
        print(f"❌ APIエラーが発生しました: {e}")

if __name__ == "__main__":
    # 実行前に、読み込ませたい雑多なテキストを 'raw_memo.txt' として同じフォルダに作成してください
    route_and_compile_content("raw_memo.txt", "ai_routed_dictionary.md")