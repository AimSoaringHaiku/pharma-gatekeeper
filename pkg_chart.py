import pandas as pd
import json
import matplotlib.pyplot as plt
import japanize_matplotlib
from matplotlib.lines import Line2D

# ==========================================
# 1. データ抽出 (JSON → DataFrame)
# ==========================================

raw_df = pd.read_csv("data_updated.csv")

records = []

for _, row in raw_df.iterrows():

    name = row.get("製品名")

    try:
        info = json.loads(row.get("付加情報_JSON", "{}"))

        limit = info.get("category_limit", 7)

        for pkg in info.get("packages", []):

            records.append({
                "product": name,
                "package": pkg["package_type"],
                "days": pkg["estimated_days"],
                "judgment": pkg["capacity_judgment"],
                "limit": limit
            })

    except Exception:
        continue


df = pd.DataFrame(records)

# ==========================================
# 2. データ加工
# ==========================================

df = df.dropna(subset=["days"])

df["days"] = pd.to_numeric(df["days"])

# CSV保存（確認用）
df.to_csv(
    "package_verification.csv",
    index=False,
    encoding="utf-8-sig"
)

print("package_verification.csv を保存しました")

# 最大日数順に並べる
product_max_days = (
    df.groupby("product")["days"]
      .max()
      .sort_values(ascending=False)
)

ordered_products = product_max_days.index.tolist()

# ==========================================
# 3. グラフ描画
# ==========================================

fig_height = max(10, len(ordered_products) * 0.45)

fig, ax = plt.subplots(figsize=(14, fig_height))

y_ticks = []
y_labels = []

for y, product in enumerate(ordered_products):

    g = (
        df[df["product"] == product]
        .sort_values("days")
        .reset_index(drop=True)
    )

    limit = g["limit"].iloc[0]

    max_days = g["days"].max()

    # -------------------------
    # 閾値まで背景バー
    # -------------------------

    ax.barh(
        y,
        limit,
        color="#E8F0FE",
        height=0.35,
        zorder=1
    )

    # 閾値ライン
    ax.vlines(
        limit,
        y - 0.35,
        y + 0.35,
        colors="gray",
        linestyles="dashed",
        linewidth=1.2,
        zorder=2
    )

    # -------------------------
    # 包装点
    # -------------------------

    for i, (_, r) in enumerate(g.iterrows()):

        days = r["days"]

        pkg = r["package"]

        safe = days <= limit

        color = "#4A90E2" if safe else "#C00000"

        ax.scatter(
            days,
            y,
            s=70,
            color=color,
            edgecolors="white",
            linewidth=0.8,
            zorder=3
        )

        # ラベルを上下交互に配置
        offset = -0.20 if i % 2 == 0 else 0.20

        va = "top" if offset < 0 else "bottom"

        ax.text(
            days,
            y + offset,
            pkg,
            fontsize=7,
            ha="center",
            va=va,
            zorder=4
        )

    y_ticks.append(y)
    y_labels.append(product)

# ==========================================
# 4. 軸設定
# ==========================================

ax.set_yticks(y_ticks)
ax.set_yticklabels(y_labels)

ax.set_xlabel("消費日数（日安）")
ax.set_ylabel("薬剤")

ax.set_xlim(left=0)

ax.invert_yaxis()

ax.xaxis.grid(
    True,
    linestyle="--",
    alpha=0.4
)

plt.title(
    "薬剤ごとの包装戦略と容量超過リスク",
    fontsize=15,
    pad=15
)
# -------------------------
# 凡例
# -------------------------

legend_elements = [
    Line2D(
        [0], [0],
        marker='o',
        color='w',
        label='小容量包装（区分内）',
        markerfacecolor='#4A90E2',
        markersize=8
    ),
    Line2D(
        [0], [0],
        marker='o',
        color='w',
        label='大容量包装（区分超過）',
        markerfacecolor='#C00000',
        markersize=8
    ),
    Line2D(
        [0], [0],
        color='gray',
        linestyle='--',
        label='容量区分の境界'
    )
]

ax.legend(
    handles=legend_elements,
    loc='upper right',
    frameon=True
)

plt.tight_layout()

plt.savefig(
    "grouped_package_chart_filtered.png",
    dpi=200
)

plt.show()

print("grouped_package_chart_filtered.png を保存しました")