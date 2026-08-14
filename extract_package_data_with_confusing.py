import pandas as pd
import json

INPUT_FILE = "data_updated.csv"
OUTPUT_FILE = "package_verification.csv"

# 容量判定対象：〇・＊〇
# ＊対象外：容量判定はしないが、下部の「紛らわしい薬剤」用に保持

raw_df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")

records = []
confusing = []

for _, row in raw_df.iterrows():
    name = row.get("製品名")
    kubun = str(
        row.get("指定濫用(＊：同ﾌﾞﾗﾝﾄﾞ内に対象含む)", "")
    ).strip()
    note = str(row.get("注釈･補足等", "")).strip()

    # ① 容量判定する商品
    if kubun in ["〇", "＊〇"]:
        try:
            info = json.loads(row.get("付加情報_JSON", "{}"))
            limit = info.get("category_limit", 7)

            for pkg in info.get("packages", []):
                records.append({
                    "product": name,
                    "kubun": kubun,
                    "package": pkg.get("package_type"),
                    "days": pkg.get("estimated_days"),
                    "judgment": pkg.get("capacity_judgment"),
                    "limit": limit,
                    "note": note
                })
        except Exception:
            continue

    # ② 紛らわしい薬剤：＊対象外
    elif kubun == "＊対象外":
        confusing.append({
            "product": name,
            "kubun": kubun,
            "note": note
        })

# 容量判定用CSV
df = pd.DataFrame(records)
df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

# 紛らわしい薬剤を別CSVにも保存
confusing_df = pd.DataFrame(confusing)
confusing_df.to_csv(
    "confusing_medicines_reference.csv",
    index=False,
    encoding="utf-8-sig"
)

print("==========================================")
print("抽出完了")
print("==========================================")
print(f"容量判定対象（〇・＊〇）：{len(df)}パッケージ")
print(f"紛らわしい薬剤（＊対象外）：{len(confusing_df)}件")
print()
print(f"容量判定CSV：{OUTPUT_FILE}")
print("紛らわしい薬剤CSV：confusing_medicines_reference.csv")
print("元のCSVは変更していません。")