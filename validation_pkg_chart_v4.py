import pandas as pd
import re
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import japanize_matplotlib

PACKAGE_CSV = "package_verification.csv"
OUTPUT_PNG = "atomic_card_table_v4.png"


def extract_amount_unit(package_str):
    text = str(package_str)
    match = re.search(r"([\d\.]+)", text)
    unit_match = re.search(r"[^\d\.]+", text)
    amount = float(match.group(1)) if match else 0
    unit = unit_match.group(0).strip() if unit_match else ""
    return amount, unit


def shorten_note(text, max_len=85):
    text = str(text).replace("\\n", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


# ==========================================================
# 1. 一本化した package_verification.csv を読む
# ==========================================================

df = pd.read_csv(PACKAGE_CSV, encoding="utf-8-sig")

required = ["product", "kubun", "package", "days", "limit"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(
        "package_verification.csv に必要な列がありません: "
        + ", ".join(missing)
    )

df["kubun"] = df["kubun"].fillna("").astype(str).str.strip()
df["days"] = pd.to_numeric(df["days"], errors="coerce")
df["limit"] = pd.to_numeric(df["limit"], errors="coerce")

# ==========================================================
# 2. 容量判定本体：〇・＊〇だけ
# ==========================================================

judgment_df = df[df["kubun"].isin(["〇", "＊〇"])].copy()
judgment_df = judgment_df.dropna(subset=["days", "limit"])

processed = []

for product, group in judgment_df.groupby("product"):
    valid = group[group["days"] > 0]
    if valid.empty:
        continue

    r = valid.iloc[0]

    amount, unit = extract_amount_unit(r["package"])
    daily = amount / r["days"] if r["days"] > 0 else 0

    daily_round = round(daily, 1)
    daily_str = (
        f"{int(daily_round)}{unit}"
        if float(daily_round).is_integer()
        else f"{daily_round}{unit}"
    )

    limit = float(r["limit"])
    boundary = limit * daily
    boundary_round = round(boundary, 1)

    boundary_str = (
        f"{int(boundary_round)}{unit}"
        if float(boundary_round).is_integer()
        else f"{boundary_round}{unit}"
    )

    small = []
    large = []

    for _, row in group.iterrows():
        if row["days"] <= limit:
            small.append(str(row["package"]))
        else:
            large.append(str(row["package"]))

    processed.append({
        "product": product,
        "daily": daily_str,
        "boundary": boundary_str,
        "small": " ".join(small) if small else "-",
        "large": " ".join(large) if large else "-"
    })

mart = pd.DataFrame(processed).sort_values("product").reset_index(drop=True)


# ==========================================================
# 3. 判定注意・参考：＊対象外・△
# ==========================================================

reference_df = df[df["kubun"].isin(["＊対象外", "△"])].copy()

# 1商品1行にする
reference_rows = []

for product, group in reference_df.groupby("product", sort=True):
    kubuns = "・".join(
        dict.fromkeys(
            str(x).strip()
            for x in group["kubun"]
            if str(x).strip()
        )
    )

    notes = []
    if "note" in group.columns:
        for x in group["note"]:
            x = str(x).strip()
            if x and x != "nan" and x not in notes:
                notes.append(x)

    reference_rows.append({
        "product": product,
        "kubun": kubuns,
        "note": " / ".join(notes)
    })

reference = pd.DataFrame(reference_rows)


# ==========================================================
# 4. 描画
# ==========================================================

main_rows = len(mart)
ref_rows = len(reference)

fig_height = max(
    8,
    0.62 * main_rows + 0.72 * ref_rows + 4
)

fig, ax = plt.subplots(figsize=(15, fig_height))

ax.set_xlim(0, 10)
ax.set_ylim(
    -(ref_rows + 3),
    main_rows + 2
)
ax.axis("off")


# --------------------------
# タイトル
# --------------------------

ax.text(
    5,
    main_rows + 1.25,
    "薬剤別 包装区分 早見表",
    fontsize=19,
    fontweight="bold",
    ha="center",
    va="bottom"
)


# --------------------------
# 本体ヘッダー
# --------------------------

header_y = main_rows + 0.35

ax.text(
    0.15, header_y, "薬剤名",
    fontweight="bold", fontsize=11
)

ax.text(
    3.35, header_y, "1日量",
    fontweight="bold", fontsize=11,
    ha="center"
)

ax.text(
    4.75, header_y, "境界",
    fontweight="bold", fontsize=11,
    ha="center"
)

ax.text(
    6.6, header_y, "小包装",
    fontweight="bold", fontsize=11,
    ha="center"
)

ax.text(
    8.65, header_y, "大包装",
    fontweight="bold", fontsize=11,
    ha="center"
)

ax.hlines(
    header_y - 0.22,
    0, 10,
    linewidth=1.5
)


# --------------------------
# 本体描画
# --------------------------

for i, row in mart.iterrows():

    y = main_rows - 1 - i

    if i % 2 == 0:
        ax.add_patch(
            patches.Rectangle(
                (0, y - 0.42),
                10,
                0.84,
                facecolor="#f5f5f5",
                edgecolor="none",
                zorder=0
            )
        )

    ax.text(
        0.15, y,
        row["product"],
        fontsize=9.5,
        fontweight="bold",
        ha="left",
        va="center"
    )

    ax.text(
        3.35, y,
        row["daily"],
        fontsize=10.5,
        ha="center",
        va="center"
    )

    # 境界線
    ax.vlines(
        4.75,
        y - 0.34,
        y + 0.34,
        color="black",
        linewidth=1.5,
        zorder=1
    )

    ax.text(
        4.75, y,
        row["boundary"],
        fontsize=9.5,
        ha="center",
        va="center",
        bbox=dict(
            boxstyle="round,pad=0.22",
            facecolor="white",
            edgecolor="gray"
        ),
        zorder=2
    )

    # 小包装：白地
    if row["small"] != "-":
        ax.text(
            6.6, y,
            row["small"],
            fontsize=9.5,
            ha="center",
            va="center",
            bbox=dict(
                boxstyle="square,pad=0.38",
                facecolor="white",
                edgecolor="black",
                linewidth=1
            )
        )

    # 大包装：グレー地・破線
    if row["large"] != "-":
        ax.text(
            8.65, y,
            row["large"],
            fontsize=9.5,
            ha="center",
            va="center",
            bbox=dict(
                boxstyle="square,pad=0.38",
                facecolor="#d9d9d9",
                edgecolor="black",
                linestyle="--",
                linewidth=1
            )
        )

    ax.hlines(
        y - 0.42,
        0, 10,
        colors="#dddddd",
        linewidth=0.8
    )


# ==========================================================
# 5. 下部：判定注意・参考
# ==========================================================

if ref_rows > 0:

    ref_top = -0.2

    ax.hlines(
        ref_top + 0.55,
        0, 10,
        colors="black",
        linewidth=1.5
    )

    ax.text(
        0.15,
        ref_top,
        "判定注意・参考",
        fontsize=13,
        fontweight="bold",
        ha="left",
        va="center"
    )

    ax.text(
        4.25,
        ref_top,
        "区分",
        fontsize=10.5,
        fontweight="bold",
        ha="center",
        va="center"
    )

    ax.text(
        7.0,
        ref_top,
        "同ブランド内比較・注釈",
        fontsize=10.5,
        fontweight="bold",
        ha="center",
        va="center"
    )

    for j, (_, row) in enumerate(reference.iterrows()):

        y = ref_top - 0.85 - j * 0.72

        if j % 2 == 0:
            ax.add_patch(
                patches.Rectangle(
                    (0, y - 0.31),
                    10,
                    0.62,
                    facecolor="#fafafa",
                    edgecolor="none"
                )
            )

        ax.text(
            0.15, y,
            row["product"],
            fontsize=9.5,
            fontweight="bold",
            ha="left",
            va="center"
        )

        ax.text(
            4.25, y,
            row["kubun"],
            fontsize=9.5,
            ha="center",
            va="center"
        )

        ax.text(
            7.0, y,
            shorten_note(row["note"]),
            fontsize=8.5,
            ha="center",
            va="center"
        )

        ax.hlines(
            y - 0.31,
            0, 10,
            colors="#e5e5e5",
            linewidth=0.7
        )


plt.tight_layout()

plt.savefig(
    OUTPUT_PNG,
    dpi=200,
    bbox_inches="tight"
)

plt.close()

print("==========================================")
print("v4 早見表生成完了")
print("==========================================")
print(f"容量判定：{main_rows}薬剤")
print(f"判定注意・参考：{ref_rows}薬剤")
print(f"出力：{OUTPUT_PNG}")
print()
print("〇・＊〇       → 容量判定")
print("＊対象外・△   → 下部の判定注意・参考")
print("対象外等      → 今回の早見表から除外")
print()
print("元CSV・package_verification.csvは変更していません。")