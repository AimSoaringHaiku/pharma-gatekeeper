import pandas as pd
import re
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import japanize_matplotlib

# ==========================================
# 1. Sources / Staging
# ==========================================

df = pd.read_csv("package_verification.csv")

df = df.dropna(subset=["days"])
df["days"] = pd.to_numeric(df["days"])

# ==========================================
# 2. Intermediate
# ==========================================

processed_data = []

for name, group in df.groupby("product"):

    valid_rows = group[group["days"] > 0]

    if len(valid_rows) == 0:
        continue

    # --------------------------------------
    # 1日量の算出
    # --------------------------------------

    r = valid_rows.iloc[0]

    match = re.search(r"([\d\.]+)", str(r["package"]))
    unit_match = re.search(r"[^\d\.]+", str(r["package"]))

    amount = float(match.group(1)) if match else 0
    unit = unit_match.group(0).strip() if unit_match else ""

    daily = amount / r["days"] if r["days"] > 0 else 0

    if daily.is_integer():
        daily_str = f"{int(daily)}{unit}/日"
    else:
        daily_str = f"{round(daily, 1)}{unit}/日"

    # --------------------------------------
    # 大容量境界
    # --------------------------------------

    limit = r["limit"]

    limit_amount = limit * daily

    if float(limit_amount).is_integer():
        limit_amount_str = f"{int(limit_amount)}{unit}"
    else:
        limit_amount_str = f"{round(limit_amount, 1)}{unit}"

    # --------------------------------------
    # 小包装 / 大包装
    # --------------------------------------

    small_pkgs = []
    large_pkgs = []

    max_days = 0

    for _, row in group.iterrows():

        max_days = max(max_days, row["days"])

        if row["days"] <= limit:
            small_pkgs.append(row["package"])
        else:
            large_pkgs.append(row["package"])

    processed_data.append({
        "product": name,
        "daily_amount": daily_str,
        "limit_days": limit,
        "limit_amount": limit_amount_str,
        "small_pkgs": small_pkgs,
        "large_pkgs": large_pkgs,
        "max_days": max_days
    })

# ==========================================
# 3. Data Mart
# ==========================================

mart_df = pd.DataFrame(processed_data)

mart_df = mart_df.sort_values(
    by="max_days",
    ascending=True
).reset_index(drop=True)

# ==========================================
# 4. 既存の詳細早見表
# ==========================================

fig_height = max(10, len(mart_df) * 0.7)

fig, ax = plt.subplots(
    figsize=(14, fig_height)
)

ax.set_xlim(0, 10)
ax.set_ylim(-1, len(mart_df))
ax.axis("off")

header_y = len(mart_df) - 0.2

ax.text(
    0.1,
    header_y,
    "薬剤名",
    fontweight="bold",
    fontsize=12,
    ha="left",
    va="bottom"
)

ax.text(
    3.5,
    header_y,
    "1日量",
    fontweight="bold",
    fontsize=12,
    ha="center",
    va="bottom"
)

ax.text(
    4.8,
    header_y,
    "大容量の\n境界",
    fontweight="bold",
    fontsize=12,
    ha="center",
    va="bottom"
)

ax.text(
    6.5,
    header_y,
    "適正包装 (小)",
    fontweight="bold",
    fontsize=12,
    ha="center",
    va="bottom"
)

ax.text(
    8.5,
    header_y,
    "大容量包装 (大)",
    fontweight="bold",
    fontsize=12,
    ha="center",
    va="bottom"
)

ax.hlines(
    header_y - 0.2,
    0,
    10,
    colors="black",
    linewidth=1.5
)

for i, row in mart_df.iterrows():

    y = i

    if i % 2 == 0:
        ax.add_patch(
            patches.Rectangle(
                (0, y - 0.45),
                10,
                0.9,
                color="#f4f4f4",
                zorder=0
            )
        )

    ax.text(
        0.1,
        y,
        row["product"],
        fontsize=10,
        ha="left",
        va="center",
        fontweight="bold"
    )

    ax.text(
        3.5,
        y,
        row["daily_amount"],
        fontsize=11,
        ha="center",
        va="center"
    )

    ax.text(
        4.8,
        y,
        row["limit_amount"],
        fontsize=11,
        ha="center",
        va="center",
        color="#555555"
    )

    # 小包装
    if row["small_pkgs"]:

        small_text = "\n".join(row["small_pkgs"])

        ax.text(
            6.5,
            y,
            small_text,
            fontsize=10,
            ha="center",
            va="center",
            bbox=dict(
                boxstyle="square,pad=0.5",
                facecolor="white",
                edgecolor="black",
                linewidth=1
            ),
            zorder=2
        )

    else:

        ax.text(
            6.5,
            y,
            "-",
            fontsize=10,
            ha="center",
            va="center",
            color="gray"
        )

    # 大包装
    if row["large_pkgs"]:

        large_text = "\n".join(row["large_pkgs"])

        ax.text(
            8.5,
            y,
            large_text,
            fontsize=10,
            ha="center",
            va="center",
            bbox=dict(
                boxstyle="square,pad=0.5",
                facecolor="#d9d9d9",
                edgecolor="black",
                linestyle="--",
                linewidth=1.2
            ),
            zorder=2
        )

    else:

        ax.text(
            8.5,
            y,
            "-",
            fontsize=10,
            ha="center",
            va="center",
            color="gray"
        )

    ax.hlines(
        y - 0.45,
        0,
        10,
        colors="#e0e0e0",
        linewidth=1,
        zorder=1
    )

ax.text(
    5,
    len(mart_df) + 1.5,
    "薬剤別 包装区分 早見表",
    fontsize=18,
    fontweight="bold",
    ha="center",
    va="bottom"
)

plt.tight_layout()

plt.savefig(
    "atomic_card_table.png",
    dpi=200,
    bbox_inches="tight"
)

plt.close()

print("完了：atomic_card_table.png を生成しました")


# =========================================================
# 5. 横型カード版
# =========================================================
#
# 「読む表」ではなく、
# 「1薬剤を一瞬で見る」ためのカード
#
# =========================================================

card_height = max(
    8,
    len(mart_df) * 0.55
)

fig, ax = plt.subplots(
    figsize=(16, card_height)
)

ax.set_xlim(0, 16)

ax.set_ylim(
    -1,
    len(mart_df) + 1
)

ax.axis("off")

# ------------------------------------------
# ヘッダー
# ------------------------------------------

header_y = len(mart_df) + 0.3

ax.text(
    0.3,
    header_y,
    "薬剤名",
    fontsize=12,
    fontweight="bold",
    ha="left",
    va="center"
)

ax.text(
    4.2,
    header_y,
    "1日量",
    fontsize=12,
    fontweight="bold",
    ha="center",
    va="center"
)

ax.text(
    7.0,
    header_y,
    "小包装",
    fontsize=12,
    fontweight="bold",
    ha="center",
    va="center"
)

ax.text(
    9.2,
    header_y,
    "容量境界",
    fontsize=12,
    fontweight="bold",
    ha="center",
    va="center"
)

ax.text(
    12.5,
    header_y,
    "大包装",
    fontsize=12,
    fontweight="bold",
    ha="center",
    va="center"
)

ax.hlines(
    header_y - 0.35,
    0,
    16,
    colors="black",
    linewidth=1.5
)

# ------------------------------------------
# 各薬剤
# ------------------------------------------

for i, row in mart_df.iterrows():

    y = len(mart_df) - i - 0.5

    # --------------------------------------
    # カード背景
    # --------------------------------------

    if i % 2 == 0:

        ax.add_patch(
            patches.Rectangle(
                (0, y - 0.27),
                16,
                0.54,
                facecolor="#f4f4f4",
                edgecolor="none",
                zorder=0
            )
        )

    # --------------------------------------
    # 薬剤名
    # --------------------------------------

    ax.text(
        0.3,
        y,
        row["product"],
        fontsize=9,
        fontweight="bold",
        ha="left",
        va="center"
    )

    # --------------------------------------
    # 1日量
    # --------------------------------------

    ax.text(
        4.2,
        y,
        row["daily_amount"],
        fontsize=10,
        ha="center",
        va="center"
    )

    # --------------------------------------
    # 小包装
    # --------------------------------------

    if row["small_pkgs"]:

        small_text = "  ".join(row["small_pkgs"])

        ax.text(
            7.0,
            y,
            small_text,
            fontsize=9,
            ha="center",
            va="center",
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor="white",
                edgecolor="black",
                linewidth=1
            )
        )

    else:

        ax.text(
            7.0,
            y,
            "-",
            fontsize=9,
            color="gray",
            ha="center",
            va="center"
        )

    # --------------------------------------
    # 容量境界
    # --------------------------------------

    ax.text(
        9.2,
        y,
        row["limit_amount"],
        fontsize=9,
        color="#555555",
        ha="center",
        va="center"
    )

    # 境界を縦線で視覚化
    ax.vlines(
        10.0,
        y - 0.22,
        y + 0.22,
        colors="#555555",
        linewidth=1.2
    )

    # --------------------------------------
    # 大包装
    # --------------------------------------

    if row["large_pkgs"]:

        large_text = "  ".join(row["large_pkgs"])

        ax.text(
            12.5,
            y,
            large_text,
            fontsize=9,
            ha="center",
            va="center",
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor="#d9d9d9",
                edgecolor="black",
                linestyle="--",
                linewidth=1.2
            )
        )

    else:

        ax.text(
            12.5,
            y,
            "-",
            fontsize=9,
            color="gray",
            ha="center",
            va="center"
        )

    # --------------------------------------
    # 行区切り
    # --------------------------------------

    ax.hlines(
        y - 0.28,
        0,
        16,
        colors="#dddddd",
        linewidth=0.8
    )

# ------------------------------------------
# タイトル
# ------------------------------------------

ax.text(
    8,
    len(mart_df) + 1.1,
    "薬剤別 包装構成カード",
    fontsize=18,
    fontweight="bold",
    ha="center",
    va="bottom"
)

# ------------------------------------------
# 凡例的な説明
# ------------------------------------------

ax.text(
    0.3,
    -0.45,
    "白：小包装　　破線グレー：大包装　　｜：容量境界",
    fontsize=10,
    color="#555555",
    ha="left",
    va="center"
)

plt.tight_layout()

plt.savefig(
    "atomic_card_line.png",
    dpi=200,
    bbox_inches="tight"
)

plt.close()

print("完了：atomic_card_line.png を生成しました")

