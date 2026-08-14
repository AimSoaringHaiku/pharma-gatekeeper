import pandas as pd
import re
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import japanize_matplotlib

PACKAGE_CSV = "package_verification.csv"
OUTPUT_PNG = "atomic_card_table_v5_final.png"

def extract_amount_unit(package_str):
    text = str(package_str)
    match = re.search(r"([\d\.]+)", text)
    unit_match = re.search(r"[^\d\.]+", text)
    amount = float(match.group(1)) if match else 0
    unit = unit_match.group(0).strip() if unit_match else ""
    return amount, unit

def shorten_note(text, max_len=80):
    text = str(text).replace("\\n", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if text == "nan" or text == "None":
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"

# ==========================================================
# 1. データの読み込み
# ==========================================================
df = pd.read_csv(PACKAGE_CSV, encoding="utf-8-sig")

df["kubun"] = df["kubun"].fillna("").astype(str).str.strip()
df["days"] = pd.to_numeric(df["days"], errors="coerce")
df["limit"] = pd.to_numeric(df["limit"], errors="coerce")

# 古いCSVを読んだ際のエラー回避（フォールバック）
if "ingredients" not in df.columns:
    df["ingredients"] = ""
else:
    df["ingredients"] = df["ingredients"].fillna("").astype(str).str.strip()

# ==========================================================
# 2. 容量判定本体（テトリス）： 〇・＊〇
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
    daily_str = f"{int(daily_round)}{unit}" if float(daily_round).is_integer() else f"{daily_round}{unit}"

    limit = float(r["limit"])
    boundary = limit * daily
    boundary_round = round(boundary, 1)
    boundary_str = f"{int(boundary_round)}{unit}" if float(boundary_round).is_integer() else f"{boundary_round}{unit}"

    small, large = [], []
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
        "large": " ".join(large) if large else "-",
        "ingredients": str(r.get("ingredients", "")) # 成分データを引き継ぐ
    })

mart = pd.DataFrame(processed).sort_values("product").reset_index(drop=True)

# ==========================================================
# 3. 判定注意・参考（マトリックス）： ＊〇・＊対象外・△
# ==========================================================
reference_df = df[df["kubun"].isin(["＊〇", "＊対象外", "△"])].copy()
reference_rows = []

CUSTOM_NOTES = {
    "アレグラFX": "「FXプレミアム」には血管収縮剤（プソイドエフェドリン）が追加配合されている点に注意が必要です。",
    "コリホグス": "中枢抑制作用による重篤な呼吸抑制のリスクがあるため、アルコールやベンゾ系薬との併用・ODには要注意。",
    "トラベルミンR": "「無印（大人用）」はジフェンヒドラミンを含有。本品は代替成分（ジフェニドール）を採用した処方です。",
    "ナロン錠": "依存性成分「ブロモバレリル尿素」を含有。主流の「エースT」や「m」等にはこの成分が含まれていません。",
    "新コンタック鼻炎Z": "ブランド内で唯一制限成分を含みません。※主成分のセチリジン塩酸塩は、妊婦への使用が禁忌とされています。",
    "新ルルAゴールドDXα": "内服かぜ薬や「メディカルドロップ」は該当。※医薬部外品の「のど飴」「トローチ」は対象外です。",
    "葛根湯エキス錠S「コタロー」": "マオウ成分を含有しますが、法規上「漢方・生薬製剤」に分類されるため、単一化学成分の規制枠から外れます。"
}

for product, group in reference_df.groupby("product", sort=True):
    kubuns = [str(x).strip() for x in group["kubun"] if str(x).strip()]
    kubun_val = kubuns[0] if kubuns else ""
    
    if kubun_val == "＊〇":
        status_text = "【該当】この商品名は該当"
        status_color = "#d32f2f" 
    elif kubun_val in ["＊対象外", "△"]:
        status_text = "【対象外】"
        status_color = "#444444" 
    else:
        continue
    
    if product in CUSTOM_NOTES:
        final_note = CUSTOM_NOTES[product]
    else:
        notes = [str(x).strip() for x in group["note"] if str(x).strip() and str(x).strip() != "nan"]
        raw_note = " / ".join(list(dict.fromkeys(notes)))
        final_note = shorten_note(raw_note)
        
    reference_rows.append({
        "product": product,
        "status_text": status_text,
        "status_color": status_color,
        "note": final_note
    })

reference = pd.DataFrame(reference_rows)
if not reference.empty:
    reference = reference.sort_values("product").reset_index(drop=True)

# ==========================================================
# 4. 描画
# ==========================================================
main_rows = len(mart)
ref_rows = len(reference) if not reference.empty else 0

# A4縦に合わせた高さの計算
fig_height = max(11, 0.65 * main_rows + 0.75 * ref_rows + 4.5)
fig, ax = plt.subplots(figsize=(12, fig_height)) # 幅を12に拡張

ax.set_xlim(0, 12)
ax.set_ylim(-(ref_rows + 4.5), main_rows + 2)
ax.axis("off")

# 配置X座標（幅12に合わせて調整）
COL_NAME_X = 0.3
COL_DOSE_X = 4.2
COL_BOUND_X = 5.8
COL_SMALL_X = 7.8
COL_LARGE_X = 10.3

# --- タイトル ---
ax.text(6, main_rows + 1.25, "薬剤別 包装区分 早見表", fontsize=19, fontweight="bold", ha="center", va="bottom")

# --- 本体ヘッダー ---
header_y = main_rows + 0.35
ax.text(COL_NAME_X, header_y, "薬剤名", fontweight="bold", fontsize=11)
ax.text(COL_DOSE_X, header_y, "1日量", fontweight="bold", fontsize=11, ha="center")
ax.text(COL_BOUND_X, header_y, "境界", fontweight="bold", fontsize=11, ha="center")
ax.text(COL_SMALL_X, header_y, "小包装", fontweight="bold", fontsize=11, ha="center")
ax.text(COL_LARGE_X, header_y, "大包装", fontweight="bold", fontsize=11, ha="center")
ax.hlines(header_y - 0.22, 0, 12, linewidth=1.5)

# --- 本体描画 ---
for i, row in mart.iterrows():
    y = main_rows - 1 - i
    if i % 2 == 0:
        ax.add_patch(patches.Rectangle((0, y - 0.42), 12, 0.84, facecolor="#f5f5f5", edgecolor="none", zorder=0))

    # 成分表示の有無でレイアウトを分岐
    if row["ingredients"]:
        ax.text(COL_NAME_X, y + 0.08, row["product"], fontsize=9.5, fontweight="bold", ha="left", va="center")
        ax.text(COL_NAME_X, y - 0.22, f"({row['ingredients']})", fontsize=7.5, ha="left", va="center", color="#777777")
    else:
        ax.text(COL_NAME_X, y, row["product"], fontsize=9.5, fontweight="bold", ha="left", va="center")

    ax.text(COL_DOSE_X, y, row["daily"], fontsize=10.5, ha="center", va="center")
    
    ax.vlines(COL_BOUND_X, y - 0.34, y + 0.34, color="black", linewidth=1.5, zorder=1)
    ax.text(COL_BOUND_X, y, row["boundary"], fontsize=9.5, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="gray"), zorder=2)

    if row["small"] != "-":
        ax.text(COL_SMALL_X, y, row["small"], fontsize=9.5, ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.38", facecolor="white", edgecolor="black", linewidth=1))

    if row["large"] != "-":
        ax.text(COL_LARGE_X, y, row["large"], fontsize=9.5, ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.38", facecolor="#d9d9d9", edgecolor="black", linestyle="--", linewidth=1))

    ax.hlines(y - 0.42, 0, 12, colors="#dddddd", linewidth=0.8)

# --- 下部：判定注意・参考（マトリックス） ---
if ref_rows > 0:
    ref_top = -0.2
    ax.hlines(ref_top + 0.55, 0, 12, colors="black", linewidth=1.5)
    
    ax.text(COL_NAME_X, ref_top, "判定注意・参考", fontsize=13, fontweight="bold", ha="left", va="center")
    ax.text(4.0, ref_top, "指定濫用 判定", fontsize=10.5, fontweight="bold", ha="center", va="center")
    ax.text(5.5, ref_top, "同ブランド内比較・注釈", fontsize=10.5, fontweight="bold", ha="left", va="center")

    for j, (_, row) in enumerate(reference.iterrows()):
        y = ref_top - 0.85 - j * 0.72

        if j % 2 == 0:
            ax.add_patch(patches.Rectangle((0, y - 0.31), 12, 0.62, facecolor="#fafafa", edgecolor="none"))

        ax.text(COL_NAME_X, y, row["product"], fontsize=9.5, fontweight="bold", ha="left", va="center")
        ax.text(4.0, y, row["status_text"], fontsize=9.5, fontweight="bold", ha="center", va="center", color=row["status_color"])
        ax.text(5.5, y, row["note"], fontsize=8.5, ha="left", va="center")
        
        ax.hlines(y - 0.31, 0, 12, colors="#e5e5e5", linewidth=0.7)

# --- 最下部：トラップ注意（左右対比・中央揃え） ---
bottom_start_y = ref_top - 0.85 - (ref_rows * 0.72) - 0.4

ax.text(COL_NAME_X, bottom_start_y, "【同ブランド内のトラップ注意】取違いを防ぐため、成分の違いによる区分を「左(対象外) ⇔ 右(該当)」で対比する。", 
        fontsize=9.5, ha="left", va="top", color="#444444", fontweight="bold")

trap_list = [
    ("アレグラ", "[対象外] FX（通常版）", "[該当] FXプレミアム（※血管収縮剤追加）"),
    ("トラベルミン", "[対象外] R・ジュニア・ファミリー・「1」", "[該当] 無印 大人用（※ジフェンヒドラミン含有）"),
    ("ナロン", "[対象外] エースT・m など", "[該当] ナロン錠・ナロン顆粒（※ブロモバレリル尿素含有）"),
    ("コンタック", "[対象外] 鼻炎Z", "[該当] 600プラス・かぜ総合 など他製品総じて"),
    ("ルル", "[対象外] のど飴・トローチ（医薬部外品）", "[該当] 内服かぜ薬すべて・メディカルドロップ"),
    ("漢方・生薬製剤", "[対象外] 葛根湯・小青竜湯など", "（※マオウエキスは化学成分ではないため法規制外）")
]

center_x = 5.2
current_y = bottom_start_y - 0.45

for brand, left_text, right_text in trap_list:
    ax.text(0.4, current_y, f"・{brand}", fontsize=9.5, ha="left", va="top", color="#444444")
    separator = "⇔" if "該当" in right_text else ""
    ax.text(center_x, current_y, separator, fontsize=9.5, ha="center", va="top", color="#444444")
    ax.text(center_x - 0.15, current_y, left_text, fontsize=9.5, ha="right", va="top", color="#444444")
    text_color = "#d32f2f" if "該当" in right_text else "#444444"
    ax.text(center_x + 0.15, current_y, right_text, fontsize=9.5, ha="left", va="top", color=text_color)
    current_y -= 0.35

# --- 右下：QRコードとアプリリンクの配置 ---
qr_x_center = 10.8
qr_y_center = bottom_start_y - 1.2
qr_size = 1.3

try:
    qr_img = mpimg.imread("QR_667832.png")
    ax.imshow(qr_img, extent=[qr_x_center - qr_size/2, qr_x_center + qr_size/2, 
                              qr_y_center - qr_size/2, qr_y_center + qr_size/2], zorder=3)
except Exception as e:
    ax.add_patch(patches.Rectangle((qr_x_center - qr_size/2, qr_y_center - qr_size/2), 
                                   qr_size, qr_size, fill=False, edgecolor="#cccccc", zorder=3))
    ax.text(qr_x_center, qr_y_center, "QR Error", ha="center", va="center", color="#cccccc")

ax.text(qr_x_center, qr_y_center - qr_size/2 - 0.15, "判定アプリ\n(GEMINI Pro 3.1 試作)", 
        fontsize=8.5, ha="center", va="top", color="#555555", fontweight="bold")

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches="tight")
plt.close()

print("==========================================")
print("v5 最終印刷用 早見表生成完了")
print(f"出力ファイル: {OUTPUT_PNG}")
print("==========================================")