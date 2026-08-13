import pandas as pd
import re
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import japanize_matplotlib  # 日本語フォント用

# ==========================================
# 1. データ準備 (Sources / Staging)
# ==========================================
df = pd.read_csv("package_verification.csv")
df = df.dropna(subset=["days"])
df["days"] = pd.to_numeric(df["days"])

# ==========================================
# 2. データ加工 (Intermediate)
# ==========================================
processed_data = []

for name, group in df.groupby("product"):
    valid_rows = group[group["days"] > 0]
    if len(valid_rows) == 0:
        continue

    r = valid_rows.iloc[0]
    
    # 包装文字から数字と単位を抽出
    match = re.search(r"([\d\.]+)", str(r["package"]))
    unit_match = re.search(r"[^\d\.]+", str(r["package"]))
    amount = float(match.group(1)) if match else 0
    unit = unit_match.group(0).strip() if unit_match else ""
    
    # 1日量の算出
    daily = amount / r["days"] if r["days"] > 0 else 0
    if daily.is_integer():
        daily_str = f"{int(daily)}{unit}"
    else:
        daily_str = f"{round(daily, 1)}{unit}"

    # 境界値の算出
    limit = r["limit"]
    limit_amount = limit * daily
    if float(limit_amount).is_integer():
        limit_amount_str = f"{int(limit_amount)}{unit}"
    else:
        limit_amount_str = f"{round(limit_amount, 1)}{unit}"

    # パッケージの振り分け（包装が小さい順にソートしておく）
    sorted_group = group.sort_values("days")
    small_pkgs = []
    large_pkgs = []
    
    for _, row in sorted_group.iterrows():
        if row["days"] <= limit:
            small_pkgs.append(row["package"])
        else:
            large_pkgs.append(row["package"])

    processed_data.append({
        "product": name,
        "daily_amount": daily_str,
        "limit_amount": limit_amount_str,
        "small_pkgs": small_pkgs,
        "large_pkgs": large_pkgs,
    })

# ==========================================
# 3. データマート化とソート (Marts)
# ==========================================
mart_df = pd.DataFrame(processed_data)

# ★検索性を高めるため、製品名でソート（昇順：ア〜ワ順）
mart_df = mart_df.sort_values(by="product", ascending=True).reset_index(drop=True)

# ==========================================
# 4. 描画 (Presentation)
# ==========================================
fig_height = max(10, len(mart_df) * 0.55)
fig, ax = plt.subplots(figsize=(15, fig_height))

# X軸の基準となる中央の境界線位置
center_x = 7.5

ax.set_xlim(0, 15)
ax.set_ylim(-1, len(mart_df) + 1)
ax.axis("off")

# ヘッダー描画
header_y = len(mart_df) + 0.2
ax.text(0.2, header_y, "薬剤名 (検索順)", fontsize=11, fontweight="bold", ha="left", va="bottom")
ax.text(3.5, header_y, "1日量", fontsize=11, fontweight="bold", ha="center", va="bottom")
ax.text(center_x, header_y, "境界線", fontsize=11, fontweight="bold", ha="center", va="bottom", color="#444444")
ax.hlines(header_y - 0.2, 0, 15, colors="black", linewidth=1.5)

# 各薬剤の行を描画
for i, row in mart_df.iterrows():
    # 上から五十音順に表示させるため、Y座標を上から下へ計算
    y = len(mart_df) - i - 0.5
    
    # 偶数行に背景色（ゼブラストライプ）
    if i % 2 == 0:
        ax.add_patch(patches.Rectangle((0, y - 0.35), 15, 0.7, facecolor="#f4f4f4", edgecolor="none", zorder=0))
        
    # 基本情報のテキスト
    ax.text(0.2, y, row["product"], fontsize=10, fontweight="bold", ha="left", va="center")
    ax.text(3.5, y, row["daily_amount"], fontsize=10, ha="center", va="center")
    
    # --------------------------------------
    # 中央の境界線と境界数値
    # --------------------------------------
    ax.vlines(center_x, y - 0.35, y + 0.35, colors="#333333", linewidth=2.5, zorder=1)
    ax.text(center_x, y, f" {row['limit_amount']} ", fontsize=9, fontweight="bold", 
            ha="center", va="center", color="white",
            bbox=dict(boxstyle="square,pad=0.2", facecolor="#333333", edgecolor="none"), zorder=3)
    
    # --------------------------------------
    # 小包装（白ブロック）: 境界線から「左」へ積む
    # --------------------------------------
    small_pkgs = row["small_pkgs"]
    # 境界に近い方（大きい包装）から左へ配置していく
    for j, pkg in enumerate(reversed(small_pkgs)): 
        block_x = center_x - 0.8 - (j * 1.1)
        ax.text(block_x, y, pkg, fontsize=9, ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.3", facecolor="white", edgecolor="black", linewidth=1.2), zorder=2)
        
    # --------------------------------------
    # 大包装（グレーブロック）: 境界線から「右」へ積む
    # --------------------------------------
    large_pkgs = row["large_pkgs"]
    # 境界に近い方（小さい包装）から右へ配置していく
    for j, pkg in enumerate(large_pkgs): 
        block_x = center_x + 0.8 + (j * 1.1)
        ax.text(block_x, y, pkg, fontsize=9, ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.3", facecolor="#cccccc", edgecolor="black", linewidth=1.2), zorder=2)
                
    # 行を区切る薄い線
    ax.hlines(y - 0.35, 0, 15, colors="#dddddd", linewidth=0.8, zorder=1)

# タイトル
ax.text(7.5, len(mart_df) + 1.2, "薬剤別 包装ブロック早見表", fontsize=16, fontweight="bold", ha="center", va="bottom")

# 余白をなくして保存
plt.tight_layout()
plt.savefig("tetris_card_table.png", dpi=200, bbox_inches="tight")
print("完了：tetris_card_table.png を生成しました")