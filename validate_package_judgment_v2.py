import pandas as pd
from pathlib import Path
import re
import unicodedata


# ============================================================
# validate_package_judgment_v2.py
#
# 正規化済みCSVを使って package_verification.csv と再照合する。
#
# 目的：
# 1. 対象外は触らない
# 2. 完全一致
# 3. 正規化商品名＋包装数量
# 4. 剤形表記などを吸収した比較
# 5. それでも無理なら照合不能
#
# このプログラムは元CSV・Excelを書き換えない。
# ============================================================

REFERENCE_CSV = Path("package_verification.csv")

TARGET_CSV = Path(
    "otc_master_updates_abuse_prevention_normalized.csv"
)

OUTPUT_REPORT = Path(
    "package_judgment_validation_report_v2.csv"
)

REFERENCE_ENCODING = "utf-8-sig"
TARGET_ENCODING = "utf-8-sig"

PRODUCT_COL = "商品名"
JUDGMENT_COL = "指定濫用防止容量"
FLAG_COL = "指定濫用防止区分"

NORMALIZED_PRODUCT_COL = "正規化商品名"
NORMALIZED_PACKAGE_COL = "正規化包装数量"


# ------------------------------------------------------------
# 基本正規化
# ------------------------------------------------------------

def normalize_text(value):
    if value is None or pd.isna(value):
        return ""

    text = unicodedata.normalize("NFKC", str(value))

    text = (
        text.replace("☆", "")
            .replace("★", "")
            .replace("〈", "")
            .replace("〉", "")
            .replace("<", "")
            .replace(">", "")
            .replace("(", "")
            .replace(")", "")
            .replace("（", "")
            .replace("）", "")
    )

    text = re.sub(r"\s+", "", text)

    return text.strip().lower()


# ------------------------------------------------------------
# 比較用の剤形表記吸収
#
# 「錠」「カプセル」等そのものを消すのではなく、
# 比較時だけ吸収する。
# 元データは変更しない。
# ------------------------------------------------------------

DOSAGE_FORM_PATTERN = re.compile(
    r"(錠剤|錠|カプセル剤|カプセル|顆粒剤|顆粒|細粒剤|細粒|"
    r"散剤|散|液剤|液|シロップ剤|シロップ|軟膏剤|軟膏|"
    r"クリーム剤|クリーム|点眼剤|点眼|テープ剤|テープ|"
    r"貼付剤|貼付|坐剤|坐薬|口腔内崩壊錠)"
)


def normalize_product_for_loose_match(value):
    text = normalize_text(value)

    # 剤形の違いだけを比較上吸収
    text = DOSAGE_FORM_PATTERN.sub("", text)

    return text


# ------------------------------------------------------------
# 包装数量正規化
# ------------------------------------------------------------

def normalize_package(value):
    text = normalize_text(value)

    if not text:
        return ""

    # 表記ゆれを比較上統一
    replacements = {
        "カプセル": "cap",
        "capsule": "cap",
        "錠": "錠",
        "包": "包",
        "p": "p",
        "ml": "ml",
        "mℓ": "ml",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# ------------------------------------------------------------
# 正解CSV側の比較キー
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
# 必須列確認
# ------------------------------------------------------------

for col in ["product", "package", "judgment"]:
    if col not in reference_df.columns:
        raise ValueError(
            f"package_verification.csv に '{col}' 列がありません。"
        )

for col in [
    FLAG_COL,
    JUDGMENT_COL,
    PRODUCT_COL,
    NORMALIZED_PRODUCT_COL,
    NORMALIZED_PACKAGE_COL,
]:
    if col not in target_df.columns:
        raise ValueError(
            f"正規化CSVに '{col}' 列がありません。"
        )


# ------------------------------------------------------------
# 正解側に比較用キーを作る
# ------------------------------------------------------------

reference_df["_product_exact"] = (
    reference_df["product"].map(normalize_text)
)

reference_df["_package_exact"] = (
    reference_df["package"].map(normalize_package)
)

reference_df["_product_loose"] = (
    reference_df["product"].map(
        normalize_product_for_loose_match
    )
)


# ------------------------------------------------------------
# 検証
# ------------------------------------------------------------

results = []

for index, row in target_df.iterrows():

    row_no = index + 2

    flag = str(
        row[FLAG_COL]
    ).strip()

    product_original = row[PRODUCT_COL]

    current = str(
        row[JUDGMENT_COL]
    ).strip()

    # --------------------------------------------------------
    # 対象外は完全スルー
    # --------------------------------------------------------

    if flag != "対象":

        results.append({
            "row": row_no,
            "JAN": row.get("JAN", ""),
            "商品名": product_original,
            "指定濫用防止区分": flag,
            "現在の指定濫用防止容量": current,
            "正解CSV判定": "",
            "判定": "対象外・照合しない",
            "照合レベル": "",
            "照合方法": "",
            "候補": ""
        })

        continue


    # --------------------------------------------------------
    # 正規化CSVから取得
    # --------------------------------------------------------

    normalized_product = normalize_text(
        row[NORMALIZED_PRODUCT_COL]
    )

    normalized_package = normalize_package(
        row[NORMALIZED_PACKAGE_COL]
    )

    loose_product = normalize_product_for_loose_match(
        row[NORMALIZED_PRODUCT_COL]
    )


    # --------------------------------------------------------
    # LEVEL 1
    # 完全な商品名＋包装数量
    # --------------------------------------------------------

    candidates = reference_df[
        (reference_df["_product_exact"] == normalized_product)
        &
        (reference_df["_package_exact"] == normalized_package)
    ].copy()


    if len(candidates) > 0:

        level = "1"
        method = "完全一致"


    else:

        # ----------------------------------------------------
        # LEVEL 2
        # 正規化商品名＋包装数量
        # ----------------------------------------------------

        candidates = reference_df[
            (
                reference_df["_product_exact"]
                == normalized_product
            )
            &
            (
                reference_df["_package_exact"]
                == normalized_package
            )
        ].copy()

        if len(candidates) > 0:

            level = "2"
            method = "正規化商品名＋包装数量"

        else:

            # ------------------------------------------------
            # LEVEL 3
            # 剤形表記を吸収＋包装数量
            # ------------------------------------------------

            candidates = reference_df[
                (
                    reference_df["_product_loose"]
                    == loose_product
                )
                &
                (
                    reference_df["_package_exact"]
                    == normalized_package
                )
            ].copy()

            if len(candidates) > 0:

                level = "3"
                method = (
                    "剤形表記吸収＋包装数量"
                )

            else:

                # --------------------------------------------
                # LEVEL 4
                # 商品名だけの候補
                #
                # 判定は確定しない。
                # 「候補」として出す。
                # --------------------------------------------

                candidates = reference_df[
                    (
                        reference_df["_product_loose"]
                        == loose_product
                    )
                ].copy()

                if len(candidates) > 0:

                    level = "4"
                    method = (
                        "商品名候補のみ・包装数量不一致"
                    )

                else:

                    level = "9"
                    method = "照合不能"


    # --------------------------------------------------------
    # 判定
    # --------------------------------------------------------

    if len(candidates) == 0:

        status = "照合不能"
        correct = ""
        candidate_text = ""

    else:

        judgments = sorted(
            set(
                candidates["judgment"]
                .astype(str)
                .str.strip()
            )
        )

        candidate_text = " / ".join(
            f"{r['product']}｜{r['package']}｜{r['judgment']}"
            for _, r in candidates.iterrows()
        )

        if level == "4":

            status = "候補あり・要確認"
            correct = " / ".join(judgments)

        elif len(judgments) == 1:

            correct = judgments[0]

            if current == correct:

                status = "一致"

            else:

                status = "不一致・修正候補"

        else:

            correct = " / ".join(judgments)
            status = "複数候補・要確認"


    results.append({
        "row": row_no,
        "JAN": row.get("JAN", ""),
        "商品名": product_original,
        "指定濫用防止区分": flag,
        "現在の指定濫用防止容量": current,
        "正解CSV判定": correct,
        "判定": status,
        "照合レベル": level,
        "照合方法": method,
        "候補": candidate_text
    })


# ------------------------------------------------------------
# レポート保存
# ------------------------------------------------------------

report_df = pd.DataFrame(results)

report_df.to_csv(
    OUTPUT_REPORT,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# 結果表示
# ------------------------------------------------------------

print("")
print("==========================================")
print("検証 v2 完了")
print("==========================================")

print(
    f"対象CSV件数：{len(target_df)}件"
)

print(
    "指定濫用防止区分=対象："
    f"{sum(target_df[FLAG_COL].astype(str).str.strip() == '対象')}件"
)

print("")
print("判定内訳：")

for status, count in (
    report_df["判定"]
    .value_counts()
    .items()
):
    print(f"  {status}：{count}件")

print("")
print("照合レベル：")

for level, count in (
    report_df["照合レベル"]
    .replace("", "対象外")
    .value_counts()
    .sort_index()
    .items()
):
    print(f"  Level {level}：{count}件")

print("")
print(
    f"検証レポート：{OUTPUT_REPORT}"
)

print("")
print("【重要】")
print("このプログラムは元CSV・Excelを書き換えません。")
print("v2では正規化済みCSVを使って再照合しています。")