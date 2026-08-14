import pandas as pd
import re
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import japanize_matplotlib

PACKAGE_CSV = "package_verification.csv"
OUTPUT_PNG = "atomic_card_table_v7.png"
QR_APP_PATH = "QR_667832.png"          # 判定アプリQR（既存）
QR_FORM_PATH = "QR_form.png"           # ご意見・改善案フォームQR（新規、事前に画像生成して配置してください）
APP_URL = "https://aimsoaringhaiku.github.io/pharma-gatekeeper/"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7A1Hz3jx1FpkuV-3V7X69qNcNLJao2o-G0K6HbnbrYFlOqA/viewform"

TARGET_INGREDIENTS_LEGEND = (
    "指定8成分: エフェドリン/メチルエフェドリン/プソイドエフェドリン/"
    "コデイン/ジヒドロコデイン/デキストロメトルファン/ジフェンヒドラミン/ブロモバレリル尿素"
)

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

# カプレット注意（末尾に「錠」がない＝カプレット。⑦対応）
CAPLET_PRODUCTS = {
    "ベンザブロックIP", "ベンザブロックL", "ベンザブロックS", "ベンザブロックTプレミアムDX",
    "ベンザブロックIPプレミアム", "ベンザブロックLプレミアムDX", "ベンザブロックSプレミアムDX",
}

# ==========================================================
# 1. データの読み込み
# ==========================================================
df = pd.read_csv(PACKAGE_CSV, encoding="utf-8-sig")

df["kubun"] = df["kubun"].fillna("").astype(str).str.strip()
df["days"] = pd.to_numeric(df["days"], errors="coerce")
df["limit"] = pd.to_numeric(df["limit"], errors="coerce")

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

    # 逆算を廃止し、スプシの1日量（daily_dose）を直接使用
    daily_int = int(float(r["daily_dose"]))
    daily_str = f"{daily_int}{unit}"

    limit = int(float(r["limit"]))  # 5 or 7（②の×5/×7表示に使う）
    boundary = limit * daily_int
    boundary_str = f"{int(boundary)}{unit}"

    small, large = [], []
    for _, row in group.iterrows():
        if row["days"] <= limit:
            small.append(str(row["package"]))
        else:
            large.append(str(row["package"]))

    processed.append({
        "product": product,
        "daily": daily_str,
        "limit": limit,
        "boundary": boundary_str,
        "small": " ".join(small) if small else "-",
        "large": " ".join(large) if large else "-",
        "ingredients": str(r.get("ingredients", "")),
        "is_caplet": product in CAPLET_PRODUCTS,
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
    "新コンタック鼻炎Z": "ブランド内で唯一制限成分を含みません。※主成分のセチリジンは、妊婦への使用が禁忌とされています。",
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
# 4. 描画 (A4完全固定レイアウト)
# ==========================================================
LOGICAL_W = 100.0
LOGICAL_H = 141.4

fig, ax = plt.subplots(figsize=(10, 14.14))
ax.set_xlim(0, LOGICAL_W)
ax.set_ylim(0, LOGICAL_H)
ax.axis("off")

# X座標の定義（①：小包装→境界→大包装の順に。②：1日量の隣に×5/×7バッジ）
# ※v7：対象成分列の開始位置を後ろに送り、長い商品名との重なりを解消
COL_NAME_X = 2.0
COL_INGR_X = 30.0
COL_DOSE_X = 50.0
COL_MULT_X = 57.0
COL_SMALL_X = 67.0
COL_BOUND_X = 80.0
COL_LARGE_X = 92.0

# --- タイトル ---
current_y = LOGICAL_H - 3.0
ax.text(LOGICAL_W / 2, current_y, "薬剤別 包装区分 早見表", fontsize=20, fontweight="bold", ha="center", va="center")

# ⓪ 作成日（右上）
today_str = datetime.date.today().strftime("%Y/%m/%d")
ax.text(LOGICAL_W, current_y + 2.5, f"作成日: {today_str}", fontsize=8, ha="right", va="center", color="#888888")

# ③ 試作品・LLM作成・検証済みの旨
current_y -= 3.2
ax.text(LOGICAL_W / 2, current_y,
        "※本表はAIを用いて作成した試作品です。一次資料（添付文書・KEGG等）との照合検証を重ねていますが、"
        "実使用前に必ず最新の公式情報をご確認ください。",
        fontsize=7.0, ha="center", va="center", color="#888888")

# --- 本体ヘッダー ---
current_y -= 4.0
ax.text(COL_NAME_X, current_y, "薬剤名", fontweight="bold", fontsize=11, ha="left", va="center")
ax.text(COL_INGR_X, current_y, "対象成分", fontweight="bold", fontsize=11, ha="left", va="center")
ax.text(COL_DOSE_X, current_y, "1日量", fontweight="bold", fontsize=11, ha="center", va="center")
ax.text(COL_SMALL_X, current_y, "小包装", fontweight="bold", fontsize=11, ha="center", va="center")
ax.text(COL_BOUND_X, current_y, "境界", fontweight="bold", fontsize=10, ha="center", va="center", color="#666666")
ax.text(COL_LARGE_X, current_y, "大包装", fontweight="bold", fontsize=11, ha="center", va="center")

# ⑥ 対象成分の凡例（8成分、ヘッダー直下に一度だけ）
current_y -= 1.6
ax.text(COL_INGR_X, current_y, TARGET_INGREDIENTS_LEGEND, fontsize=5.3, ha="left", va="center", color="#999999")

# ①② 補足注記（小/大包装の販売可否ルール、1日量の定義）
current_y -= 1.4
ax.text(COL_NAME_X, current_y,
        "小包装＝単品1個なら18歳未満へも販売可／大包装＝18歳未満へは販売不可　"
        "｜　1日量＝15歳以上（成人）の1日最大服用量　｜　×5・×7＝容量区分の基準日数",
        fontsize=6.3, ha="left", va="center", color="#555555")

current_y -= 1.5
ax.hlines(current_y, 0, LOGICAL_W, linewidth=2.0)
current_y -= 2.0

main_rows = len(mart)
ref_rows = len(reference) if not reference.empty else 0
bottom_reserved_space = (ref_rows * 3.5) + 34.0
available_main_space = current_y - bottom_reserved_space
row_height = min(4.2, available_main_space / max(1, main_rows))

# --- 本体描画 ---
for i, row in mart.iterrows():
    if i % 2 == 0:
        ax.add_patch(patches.Rectangle((0, current_y - 2.0), LOGICAL_W, row_height, facecolor="#f5f5f5", edgecolor="none", zorder=0))

    # 薬剤名（⑦カプレットは「※」1文字のみ。長い商品名は自動でフォントを縮小して対象成分列との重なりを防止）
    name_len = len(row["product"])
    name_fontsize = 10.0 if name_len <= 8 else (9.0 if name_len <= 12 else 8.0)
    name_text = row["product"] + ("※" if row["is_caplet"] else "")
    ax.text(COL_NAME_X, current_y, name_text, fontsize=name_fontsize,
            fontweight="bold", ha="left", va="center")

    # 対象成分（塩酸塩などの文字列をカット、長すぎる場合は省略）
    if row["ingredients"]:
        clean_ingr = re.sub(r'(塩酸塩|リン酸塩|硫酸塩|臭化水素酸塩|マレイン酸塩|酒石酸塩|フマル酸塩)', '', row["ingredients"])
        if len(clean_ingr) > 22:
            clean_ingr = clean_ingr[:22] + "…"
        ax.text(COL_INGR_X, current_y, clean_ingr, fontsize=7.0, ha="left", va="center", color="#666666")
    else:
        ax.text(COL_INGR_X, current_y, "-", fontsize=8.0, ha="left", va="center", color="#aaaaaa")

    ax.text(COL_DOSE_X, current_y, row["daily"], fontsize=10.5, ha="center", va="center")

    # ② ×5 / ×7 バッジ（7日制限＝青、5日制限＝オレンジ）
    mult_color = "#1565c0" if row["limit"] == 7 else "#e65100"
    ax.text(COL_MULT_X, current_y, f"×{row['limit']}", fontsize=8.5, ha="center", va="center",
            color=mult_color, fontweight="bold")

    # 小包装
    if row["small"] != "-":
        ax.text(COL_SMALL_X, current_y, row["small"], fontsize=9.5, ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.4", facecolor="white", edgecolor="black", linewidth=1))

    # ① 境界（小/大包装の"間の仕切り"として中央に）
    ax.vlines(COL_BOUND_X, current_y - 1.5, current_y + 1.5, color="black", linewidth=1.5, zorder=1)
    ax.text(COL_BOUND_X, current_y, row["boundary"], fontsize=9.0, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="gray"), zorder=2)

    # 大包装
    if row["large"] != "-":
        ax.text(COL_LARGE_X, current_y, row["large"], fontsize=9.5, ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.4", facecolor="#d9d9d9", edgecolor="black", linestyle="--", linewidth=1))

    current_y -= row_height

# --- 下部：判定注意・参考（マトリックス） ---
if ref_rows > 0:
    current_y -= 1.0
    ax.hlines(current_y, 0, LOGICAL_W, colors="black", linewidth=1.5)
    current_y -= 2.5

    ax.text(COL_NAME_X, current_y, "判定注意・参考", fontsize=13, fontweight="bold", ha="left", va="center")
    ax.text(30.0, current_y, "指定濫用 判定", fontsize=10.5, fontweight="bold", ha="center", va="center")
    ax.text(45.0, current_y, "同ブランド内比較・注釈", fontsize=10.5, fontweight="bold", ha="left", va="center")

    current_y -= 2.0
    ax.hlines(current_y, 0, LOGICAL_W, colors="#cccccc", linewidth=1.0)
    current_y -= 2.5

    for j, (_, row) in enumerate(reference.iterrows()):
        if j % 2 == 0:
            ax.add_patch(patches.Rectangle((0, current_y - 1.5), LOGICAL_W, 3.0, facecolor="#fafafa", edgecolor="none"))

        ax.text(COL_NAME_X, current_y, row["product"], fontsize=10.0, fontweight="bold", ha="left", va="center")
        ax.text(30.0, current_y, row["status_text"], fontsize=10.0, fontweight="bold", ha="center", va="center", color=row["status_color"])
        ax.text(45.0, current_y, row["note"], fontsize=7.5, ha="left", va="center")
        current_y -= 3.5

# --- 最下部：トラップ注意（左右対比） ---
current_y -= 1.0
ax.text(COL_NAME_X, current_y, "【同ブランド内のトラップ注意】取違いを防ぐため、成分の違いによる区分を「左(対象外) ⇔ 右(該当)」で対比する。",
        fontsize=9.5, ha="left", va="top", color="#444444", fontweight="bold")

trap_list = [
    ("アレグラ", "[対象外] FX（通常版）", "[該当] FXプレミアム（※血管収縮剤追加）"),
    ("トラベルミン", "[対象外] R・ジュニア・ファミリー・「1」", "[該当] 無印 大人用（※ジフェンヒドラミン含有）"),
    ("ナロン", "[対象外] エースT・m など", "[該当] ナロン錠・ナロン顆粒（※ブロモバレリル尿素含有）"),
    ("コンタック", "[対象外] 鼻炎Z", "[該当] 600プラス・かぜ総合 など他製品総じて"),
    ("ルル", "[対象外] のど飴・トローチ（医薬部外品）", "[該当] 内服かぜ薬すべて・メディカルドロップ"),
    ("漢方・生薬製剤", "[対象外] 葛根湯・小青竜湯など", "（※マオウエキスは化学成分ではないため法規制外）")
]

current_y -= 3.0

# トラップ注意欄はQR幅ぶん右側を空け、左側だけで完結させる（横方向の衝突回避）
TRAP_BRAND_X = 3.0
TRAP_LEFT_X = 16.0
TRAP_ARROW_X = 44.0
TRAP_RIGHT_X = 46.0
TRAP_RIGHT_MAXLEN = 24  # QR領域(x=74〜)に文字が届かないよう右側テキストを制限

for brand, left_text, right_text in trap_list:
    ax.text(TRAP_BRAND_X, current_y, f"・{brand}", fontsize=8.3, ha="left", va="center", color="#444444")
    ax.text(TRAP_LEFT_X, current_y, left_text, fontsize=8.3, ha="left", va="center", color="#444444")
    separator = "⇔" if "該当" in right_text else ""
    ax.text(TRAP_ARROW_X, current_y, separator, fontsize=8.3, ha="center", va="center", color="#444444")
    text_color = "#d32f2f" if "該当" in right_text else "#444444"
    right_display = right_text if len(right_text) <= TRAP_RIGHT_MAXLEN else right_text[:TRAP_RIGHT_MAXLEN] + "…"
    ax.text(TRAP_RIGHT_X, current_y, right_display, fontsize=8.3, ha="left", va="center", color=text_color)
    current_y -= 2.2

# ⑦ カプレット注記の脚注（トラップ欄が終わった後の実際のcurrent_yを使う）
current_y -= 1.8
ax.text(COL_NAME_X, current_y,
        "※＝カプレット表記の品目（ベンザブロック◯◯／末尾「錠」なし）。「◯◯錠」と1日成分量は同一ですが服用粒数が異なります。",
        fontsize=7.0, ha="left", va="center", color="#888888")

# --- 区切り線 ---
current_y -= 2.0
ax.hlines(current_y, 0, LOGICAL_W, colors="#dddddd", linewidth=0.8)
current_y -= 1.0

# --- 右下：QRコード×2（④判定アプリ／⑤意見フォーム）とURL併記 ---
# ※v7：トラップ欄描画後の実際のcurrent_yを基準にする（v6はtrap_start_y基準で欄の途中に重なっていたバグを修正）
qr_size = 9.0
qr_y_center = current_y - qr_size/2 - 1.0

# ④ QR1：判定アプリ（既存）
qr1_x = 78.0
try:
    qr_img = mpimg.imread(QR_APP_PATH)
    ax.imshow(qr_img, extent=[qr1_x - qr_size/2, qr1_x + qr_size/2,
                              qr_y_center - qr_size/2, qr_y_center + qr_size/2], zorder=3)
except Exception:
    ax.add_patch(patches.Rectangle((qr1_x - qr_size/2, qr_y_center - qr_size/2),
                                   qr_size, qr_size, fill=False, edgecolor="#cccccc", zorder=3))
    ax.text(qr1_x, qr_y_center, "QR Error", ha="center", va="center", color="#cccccc")

ax.text(qr1_x, qr_y_center - qr_size/2 - 1.3, "判定アプリ\n(GEMINI Pro 3.1 試作)",
        fontsize=7.5, ha="center", va="top", color="#555555", fontweight="bold")
# ⑤ URL併記
ax.text(qr1_x, qr_y_center - qr_size/2 - 4.0, APP_URL,
        fontsize=4.8, ha="center", va="top", color="#999999")

# ④ QR2：ご意見・改善案フォーム（新規）
qr2_x = 91.0
try:
    qr_img2 = mpimg.imread(QR_FORM_PATH)
    ax.imshow(qr_img2, extent=[qr2_x - qr_size/2, qr2_x + qr_size/2,
                               qr_y_center - qr_size/2, qr_y_center + qr_size/2], zorder=3)
except Exception:
    ax.add_patch(patches.Rectangle((qr2_x - qr_size/2, qr_y_center - qr_size/2),
                                   qr_size, qr_size, fill=False, edgecolor="#cccccc", zorder=3))
    ax.text(qr2_x, qr_y_center, "QR Error", ha="center", va="center", color="#cccccc")

ax.text(qr2_x, qr_y_center - qr_size/2 - 1.3, "ご意見・改善案は\nこちら",
        fontsize=7.5, ha="center", va="top", color="#555555", fontweight="bold")

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches="tight")
plt.close()

print("==========================================")
print("v7（重なり修正版） 早見表生成完了")
print(f"出力ファイル: {OUTPUT_PNG}")
print("==========================================")