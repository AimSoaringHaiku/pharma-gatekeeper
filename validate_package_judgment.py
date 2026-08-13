import pandas as pd
from pathlib import Path
import re
import unicodedata


# ============================================================
# 検証専用
#
# 目的：
# package_verification.csv を「正解候補」として、
# otc_master_updates_abuse_prevention.csv の
# 「指定濫用防止区分=対象」だけを照合する。
#
# この段階ではExcel/CSVを一切書き換えない。
# ============================================================

REFERENCE_CSV = Path("package_verification.csv")
TARGET_CSV = Path("otc_master_updates_abuse_prevention.csv")

OUTPUT_REPORT = Path(
    "package_judgment_validation_report.csv"
)

REFERENCE_ENCODING = "utf-8-sig"
TARGET_ENCODING = "cp932"

PRODUCT_COL = "商品名"
JUDGMENT_COL = "指定濫用防止容量"
TARGET_FLAG_COL = "指定濫用防止区分"


def normalize_text(value):
    if value is None or pd.isna(value):
        return ""

    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("☆", "").replace("★", "")
    text = re.sub(r"\s+", "", text)

    return text.strip().lower()


# ------------------------------------------------------------
# 1. 読み込み
# ------------------------------------------------------------

reference_df = pd.read_csv(
    REFERENCE_CSV,
    encoding=REFERENCE_ENCODING
)

target_df = pd.read_csv(
    TARGET_CSV,
    encoding=TARGET_ENCODING
)


# ------------------------------------------------------------
# 2. 必須列チェック
# ------------------------------------------------------------

for col in ["product", "package", "judgment"]:
    if col not in reference_df.columns:
        raise ValueError(
            f"package_verification.csv に '{col}' 列がありません。"
        )

for col in [TARGET_FLAG_COL, JUDGMENT_COL, PRODUCT_COL]:
    if col not in target_df.columns:
        raise ValueError(
            f"検証対象CSVに '{col}' 列がありません。"
        )


# ------------------------------------------------------------
# 3. 正解CSVを正規化
# ------------------------------------------------------------

reference_df["_product_norm"] = (
    reference_df["product"].map(normalize_text)
)

reference_df["_package_norm"] = (
    reference_df["package"].map(normalize_text)
)


# ------------------------------------------------------------
# 4. 対象行だけ照合
# ------------------------------------------------------------

results = []

for index, row in target_df.iterrows():

    row_no = index + 2
    product = normalize_text(row[PRODUCT_COL])
    current = str(row[JUDGMENT_COL]).strip()
    flag = str(row[TARGET_FLAG_COL]).strip()

    # --------------------------------------------------------
    # 対象外は判定しない
    # --------------------------------------------------------

    if flag != "対象":
        results.append({
            "row": row_no,
            "JAN": row.get("JAN", ""),
            "商品名": row[PRODUCT_COL],
            "指定濫用防止区分": flag,
            "現在の指定濫用防止容量": current,
            "正解CSV判定": "",
            "判定": "対象外・照合しない",
            "照合方法": "",
            "候補": ""
        })
        continue

    # --------------------------------------------------------
    # 商品名 + 包装で候補検索
    # JANは package_verification.csv に無いため、
    # この検証版では商品名・包装を使う。
    # --------------------------------------------------------

    product_candidates = reference_df[
        reference_df["_product_norm"].apply(
            lambda x: bool(x) and (x in product or product in x)
        )
    ].copy()

    exact_candidates = product_candidates[
        product_candidates["_package_norm"].apply(
            lambda x: bool(x) and x in product
        )
    ].copy()

    if len(exact_candidates) == 0:
        results.append({
            "row": row_no,
            "JAN": row.get("JAN", ""),
            "商品名": row[PRODUCT_COL],
            "指定濫用防止区分": flag,
            "現在の指定濫用防止容量": current,
            "正解CSV判定": "",
            "判定": "照合不能",
            "照合方法": "商品名＋包装",
            "候補": ""
        })
        continue

    judgments = sorted(
        set(exact_candidates["judgment"].astype(str).str.strip())
    )

    candidates_text = " / ".join(
        f"{r['product']}｜{r['package']}｜{r['judgment']}"
        for _, r in exact_candidates.iterrows()
    )

    # 候補が複数でも判定が同じなら、判定自体は一意
    if len(judgments) == 1:
        correct = judgments[0]

        if current == correct:
            status = "一致"
        else:
            status = "不一致・修正候補"

        method = (
            "商品名＋包装"
            if len(exact_candidates) == 1
            else "商品名＋包装（候補複数・判定同一）"
        )

    else:
        correct = " / ".join(judgments)
        status = "複数候補・要確認"
        method = "商品名＋包装"

    results.append({
        "row": row_no,
        "JAN": row.get("JAN", ""),
        "商品名": row[PRODUCT_COL],
        "指定濫用防止区分": flag,
        "現在の指定濫用防止容量": current,
        "正解CSV判定": correct,
        "判定": status,
        "照合方法": method,
        "候補": candidates_text
    })


# ------------------------------------------------------------
# 5. レポート保存
# ------------------------------------------------------------

report_df = pd.DataFrame(results)

report_df.to_csv(
    OUTPUT_REPORT,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# 6. 結果表示
# ------------------------------------------------------------

print("")
print("==========================================")
print("検証完了（書き換えはしていません）")
print("==========================================")

print(f"対象CSV件数：{len(target_df)}")
print(
    f"指定濫用防止区分=対象："
    f"{sum(target_df[TARGET_FLAG_COL].astype(str).str.strip() == '対象')}件"
)

print("")
print("判定内訳：")

for status, count in report_df["判定"].value_counts().items():
    print(f"  {status}：{count}件")

print("")
print(f"検証レポート：{OUTPUT_REPORT}")

print("")
print("【重要】")
print("このプログラムは、元CSV・Excelを変更しません。")
print("レポートを確認してから、別プログラムで反映します。")