import pandas as pd
from pathlib import Path
import re
import unicodedata

INPUT_CSV = Path("otc_master_updates_abuse_prevention.csv")
OUTPUT_CSV = Path("otc_master_updates_abuse_prevention_normalized.csv")
ENCODING = "cp932"
PRODUCT_COL = "商品名"
FLAG_COL = "指定濫用防止区分"

def normalize_text(value):
    if value is None or pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("☆", "").replace("★", "")
    text = re.sub(r"\s+", "", text)
    return text.strip()

PACKAGE_PATTERN = re.compile(
    r"(?P<package>\d+(?:\.\d+)?(?:錠|包|P|p|カプセル|CAP|cap|mL|ml|g|mg|枚|本|個|袋))$"
)

def split_product_and_package(value):
    normalized = normalize_text(value)
    if not normalized:
        return "", ""
    match = PACKAGE_PATTERN.search(normalized)
    if not match:
        return normalized, ""
    return normalized[:match.start()], match.group("package")

df = pd.read_csv(INPUT_CSV, encoding=ENCODING)
for col in [PRODUCT_COL, FLAG_COL]:
    if col not in df.columns:
        raise ValueError(f"列 '{col}' がCSVにありません。")

df["正規化商品名"] = ""
df["正規化包装数量"] = ""
df["正規表現キー"] = ""
df["正規化処理"] = ""

for index, row in df.iterrows():
    flag = str(row[FLAG_COL]).strip()
    product = row[PRODUCT_COL]
    if flag != "対象":
        df.at[index, "正規化処理"] = "対象外・処理しない"
        continue
    normalized_product, package = split_product_and_package(product)
    df.at[index, "正規化商品名"] = normalized_product
    df.at[index, "正規化包装数量"] = package
    df.at[index, "正規表現キー"] = normalized_product + ("|" + package if package else "")
    df.at[index, "正規化処理"] = (
        "商品名正規化＋末尾包装数量分離" if package
        else "商品名正規化・包装数量未検出"
    )

df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

target_count = df[FLAG_COL].astype(str).str.strip().eq("対象").sum()
package_count = df["正規化包装数量"].astype(str).str.strip().ne("").sum()
print("==========================================")
print("正規化完了")
print("==========================================")
print(f"元CSV件数：{len(df)}件")
print(f"指定濫用防止「対象」：{target_count}件")
print(f"包装数量を分離できた件数：{package_count}件")
print(f"出力：{OUTPUT_CSV}")
print("元CSVは変更していません。")