import pandas as pd

def main():
    print("🚀 URLリストとの合体（マージ）処理を開始します...")
    
    # 1. ファイルの読み込み
    df_main = pd.read_csv("data_updated.csv")
    df_url = pd.read_csv("0724_14 - URL付きﾘｽﾄ.csv")
    
    # 2. リスト側から「製品名」と「URL」の辞書を作成（KEGG_薬名をキーにする）
    url_map = {}
    for _, row in df_url.iterrows():
        kegg_name = str(row.get("KEGG_薬名", "")).strip()
        url = str(row.get("KEGG_URL", "")).strip()
        if kegg_name and url.startswith("http"):
            url_map[kegg_name] = url
            
    # 3. メインデータの製品名に合わせて URL を代入（XLOOKUPと同じ動作）
    df_main["KEGG_URL"] = df_main["製品名"].apply(lambda x: url_map.get(str(x).strip(), ""))
    
    # マッチング結果の確認
    success_count = df_main["KEGG_URL"].apply(lambda x: 1 if str(x).startswith("http") else 0).sum()
    print(f"✅ 全 {len(df_main)} 品目中、 {success_count} 品目に公式URLが結合されました！")
    
    # 4. 上書き保存
    df_main.to_csv("data_updated.csv", index=False)
    print("🎯 'data_updated.csv' へのURL付与が完全に完了しました！")

if __name__ == "__main__":
    main()