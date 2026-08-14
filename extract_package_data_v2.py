import pandas as pd
import json

INPUT_CSV = "data_updated.csv"
OUTPUT_CSV = "package_verification.csv"

raw_df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")

records = []

for _, row in raw_df.iterrows():

    product = str(row.get("製品名", "")).strip()
    kubun = str(row.get("指定濫用(＊：同ﾌﾞﾗﾝﾄﾞ内に対象含む)", "")).strip()
    note = str(row.get("注釈･補足等", "")).strip()

    # 成分フラグを読み込む（「-」や空白は除去）
    ingredients = str(row.get("対象成分含有フラグ", "")).strip()
    if ingredients == "nan" or ingredients == "-":
        ingredients = "" 

    # ここを追加：スプシの「dailyDose」列（またはそれに該当する1日量の列）を直接取得
    daily_dose = row.get("dailyDose", 0)

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
                "note": note,             # ← ここにカンマが必要でした
                "ingredients": ingredients,
                "daily_dose": daily_dose
            })

    except Exception:
        continue

df = pd.DataFrame(records)

columns = [
    "product",
    "kubun",
    "package",
    "days",
    "judgment",
    "limit",
    "note",           # ← ここにカンマが必要でした
    "ingredients",
    "daily_dose"
]

df = df.reindex(columns=columns)

df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

print("==========================================")
print("package_verification.csv 再生成完了")
print("==========================================")
print(f"抽出パッケージ数：{len(df)}")
print(f"出力：{OUTPUT_CSV}")