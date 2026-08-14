import pandas as pd
import json

INPUT_CSV = "data_updated.csv"
OUTPUT_CSV = "package_verification.csv"

raw_df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")

records = []

for _, row in raw_df.iterrows():

    product = str(row.get("製品名", "")).strip()

    # 指定濫用区分を保持
    kubun = str(
        row.get("指定濫用(＊：同ﾌﾞﾗﾝﾄﾞ内に対象含む)", "")
    ).strip()

    # 今回は容量判定本体＋判定注意情報を保持する
    # 「対象外」「一般用検査薬」は容量判定からは外すが、
    # 元データ上の区分自体は失わない。
    note = str(row.get("注釈･補足等", "")).strip()

    try:
        info_raw = row.get("付加情報_JSON", "{}")

        if pd.isna(info_raw):
            info_raw = "{}"

        info = json.loads(info_raw)

        limit = info.get("category_limit", 7)

        for pkg in info.get("packages", []):

            records.append({
                "product": product,
                "kubun": kubun,
                "package": pkg.get("package_type", ""),
                "days": pkg.get("estimated_days"),
                "judgment": pkg.get("capacity_judgment", ""),
                "limit": limit,
                "note": note
            })

    except Exception:
        # JSONを読めない商品も、元データそのものを壊さない
        # 容量判定用の行だけ作れないためスキップ
        continue


df = pd.DataFrame(records)

# v4が使いやすい列順
columns = [
    "product",
    "kubun",
    "package",
    "days",
    "judgment",
    "limit",
    "note"
]

df = df.reindex(columns=columns)

# UTF-8 BOM付き。Excelでも開きやすい形式
df.to_csv(
    OUTPUT_CSV,
    index=False,
    encoding="utf-8-sig"
)

print("==========================================")
print("package_verification.csv 再生成完了")
print("==========================================")
print(f"抽出パッケージ数：{len(df)}")

if "kubun" in df.columns:
    print()
    print("指定濫用区分の内訳：")
    print(df["kubun"].value_counts(dropna=False).to_string())

print()
print(f"出力：{OUTPUT_CSV}")
print("元の data_updated.csv は変更していません。")