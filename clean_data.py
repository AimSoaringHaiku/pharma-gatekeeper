import json
import pandas as pd

def clean_maternity_text(text):
    """文章の重複やゴミ文字（",など）をきれいに掃除する関数"""
    if pd.isna(text) or not text:
        return ""
    # ゴミ文字の削除
    text = str(text).replace('",', '').replace('",', '')
    
    # 改行で段落に分けて、重複している段落を1つにまとめる
    paragraphs = text.split("\n\n")
    unique_paras = []
    seen = set()
    for p in paragraphs:
        p_clean = p.strip()
        if p_clean and p_clean not in seen:
            seen.add(p_clean)
            unique_paras.append(p_clean)
    return "\n\n".join(unique_paras)

def fix_matrix_json(json_str):
    """「報告なし」なのに「△(慎重)」になっている矛盾を「〇(－)」に直す関数"""
    if pd.isna(json_str) or not json_str:
        return ""
    try:
        data = json.loads(str(json_str))
        for item in data.get("成分マトリックス", []):
            for cat, cell in item.items():
                if isinstance(cell, dict):
                    j = cell.get("判定")
                    r = cell.get("備考", "")
                    # 備考に「報告なし」「影響なし」等があるのに △ や 慎重 になっている場合
                    if j in ["△", "慎重"]:
                        if any(kw in r for kw in ["報告されていません", "影響はありません", "問題ありません", "低いと考えられます", "該当しません"]):
                            cell["判定"] = "〇"
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return json_str

def main():
    print("🚀 データのお掃除（重複段落の削除 ＆ 判定矛盾の修正）を開始します...")
    
    # データの読み込み
    df = pd.read_csv("data_updated.csv")
    
    # お掃除処理の適用
    if "妊婦・授乳婦_専門家エビデンス" in df.columns:
        df["妊婦・授乳婦_専門家エビデンス"] = df["妊婦・授乳婦_専門家エビデンス"].apply(clean_maternity_text)
        print("✅ 妊婦・授乳婦エビデンスの重複お掃除 完了")
        
    if "マトリックス_JSON" in df.columns:
        df["マトリックス_JSON"] = df["マトリックス_JSON"].apply(fix_matrix_json)
        print("✅ マトリックス判定の矛盾修正（△ ➡ 〇） 完了")
        
    # 上書き保存
    df.to_csv("data_updated.csv", index=False)
    print("🎯 すべての処理が完了しました！ 'data_updated.csv' をきれいに更新しました。")

if __name__ == "__main__":
    main()