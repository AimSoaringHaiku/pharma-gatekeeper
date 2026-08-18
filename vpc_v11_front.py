import pandas as pd
import re
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import japanize_matplotlib

PACKAGE_CSV = "package_verification.csv"
OUTPUT_PNG = "atomic_card_table_v11_front.png"
QR_APP_PATH = "QR_667832.png"
QR_FORM_PATH = "QR_form.png"
APP_URL = "https://aimsoaringhaiku.github.io/pharma-gatekeeper/"

GRAY, LGRAY, RED, BLUE, GREEN, ORANGE = "#555555", "#888888", "#d32f2f", "#1565c0", "#2e7d32", "#e65100"

def extract_amount_unit(package_str):
    match = re.search(r"([\d\.]+)", str(package_str))
    unit_match = re.search(r"[^\d\.]+", str(package_str))
    return (float(match.group(1)) if match else 0), (unit_match.group(0).strip() if unit_match else "")

# ==========================================================
# 1. データ読み込み集計
# ==========================================================
df = pd.read_csv(PACKAGE_CSV, encoding="utf-8-sig")
df["kubun"] = df["kubun"].fillna("").astype(str).str.strip()
df["days"] = pd.to_numeric(df["days"], errors="coerce")
df["limit"] = pd.to_numeric(df["limit"], errors="coerce")
if "ingredients" not in df.columns: df["ingredients"] = ""

processed = []
for product, group in df[df["kubun"].isin(["〇", "＊〇"])].dropna(subset=["days", "limit"]).groupby("product"):
    r = group[group["days"] > 0].iloc[0] if not group[group["days"] > 0].empty else None
    if r is None: continue
    amount, unit = extract_amount_unit(r["package"])
    daily_int = int(float(r["daily_dose"]))
    limit = int(float(r["limit"]))
    boundary = limit * daily_int
    small = [str(row["package"]) for _, row in group.iterrows() if row["days"] <= limit]
    large = [str(row["package"]) for _, row in group.iterrows() if row["days"] > limit]
    processed.append({
        "product": product, "daily": f"{daily_int}{unit}", "limit": limit, "boundary": f"{int(boundary)}{unit}",
        "small": " ".join(small) if small else "-", "large": " ".join(large) if large else "-",
        "ingredients": str(r.get("ingredients", "")), "is_caplet": product in {"ベンザブロックIP", "ベンザブロックL", "ベンザブロックS", "ベンザブロックTプレミアムDX", "ベンザブロックIPプレミアム", "ベンザブロックLプレミアムDX", "ベンザブロックSプレミアムDX"}
    })
mart = pd.DataFrame(processed).sort_values("product").reset_index(drop=True)

# ==========================================================
# 2. 描画 (A4 表面)
# ==========================================================
LOGICAL_W, LOGICAL_H = 100.0, 141.4
fig, ax = plt.subplots(figsize=(10, 14.14))
ax.set_xlim(0, LOGICAL_W); ax.set_ylim(0, LOGICAL_H); ax.axis("off")

COL_NAME_X, COL_INGR_X, COL_DOSE_X, COL_MULT_X, COL_SMALL_X, COL_BOUND_X, COL_LARGE_X, FLOW_X = 2.0, 28.0, 48.0, 55.0, 61.0, 71.0, 81.5, 92.5

# --- タイトル ---
y = LOGICAL_H - 1.7
ax.text(LOGICAL_W / 2, y, "薬剤別 包装区分 早見表", fontsize=19, fontweight="bold", ha="center", va="center")
ax.text(LOGICAL_W, y + 1.4, f"作成日: {datetime.date.today().strftime('%Y/%m/%d')}", fontsize=8, ha="right", color=LGRAY)

# --- 使い方・販売可否 ---
y -= 1.45
ax.hlines(y + 0.85, 0, LOGICAL_W, colors=BLUE, linewidth=1.2)
y -= 0.15
ax.text(COL_NAME_X, y, "① 18歳未満:", fontsize=7.4, fontweight="bold", color=RED)
ax.text(COL_NAME_X + 12.0, y, "小容量1個のみ販売可（氏名・年齢＋他店確認必須）。大容量・複数個(種類違い合算)は理由問わず一律禁止", fontsize=6.3, fontweight="bold")
y -= 1.45
ax.text(COL_NAME_X, y, "② 18歳以上:", fontsize=7.4, fontweight="bold", color=BLUE)
ax.text(COL_NAME_X + 12.0, y, "小容量は通常販売可（他店確認必須）。大容量・複数個の購入は理由確認が必須（正当な理由がなければ不可）", fontsize=6.6)
y -= 1.45
ax.text(COL_NAME_X, y, "③ 年齢確認:", fontsize=7.4, fontweight="bold", color=BLUE)
ax.text(COL_NAME_X + 12.0, y, "見た目で18歳以上と判断できない場合、学生証・免許証等の身分証で氏名・年齢を確認。提示なしは販売不可", fontsize=6.3)
y -= 1.45
ax.hlines(y, 0, LOGICAL_W, colors="#dddddd", linewidth=0.8)
y -= 1.75

# --- 本体ヘッダー ---
for col_x, label in zip([COL_NAME_X, COL_INGR_X, COL_DOSE_X, COL_MULT_X, COL_SMALL_X, COL_BOUND_X, COL_LARGE_X], 
                        ["薬剤名", "対象成分", "1日量", "区分", "小包装", "境界", "大包装"]):
    ax.text(col_x, y, label, fontweight="bold", fontsize=11.5, ha="left" if col_x < COL_DOSE_X else "center")
ax.text(FLOW_X, y, "レジ確認フロー", fontweight="bold", fontsize=8.3, ha="center", color=GRAY)

y -= 1.2
ax.text(COL_NAME_X, y, "小包装＝単品1個は18歳未満も可/大包装＝18歳未満へ不可 ｜ 1日量＝成人(15歳以上)の1日最大服用量", fontsize=6.3, color=GRAY)
y -= 1.25
ax.hlines(y, 0, LOGICAL_W, linewidth=1.6)
y -= 1.6

row_height = 2.4

# --- レジ確認フロー ---
FLOW_HALF_W = 7.0
flow_nodes = [
    (["18歳未満の疑い", "→身分証で確認"], BLUE, "#eef4fc"),
    (["小容量1個のみ", "購入？"], BLUE, "#eef4fc"),
    (["【いいえ】大容量/複数", "→18歳未満は一律禁止", "18歳以上は理由確認"], RED, "#fdecea"),
    (["【はい】小容量1個", "→他店確認必須"], ORANGE, "#fff3e6"),
    (["条件を満たせば", "販売可"], GREEN, "#eaf5ea"),
]
flow_top, flow_bottom = 120.0, 75.0
flow_gap = (flow_top - flow_bottom) / 4
prev_y = None
for idx, (lines, edge_color, fill_color) in enumerate(flow_nodes):
    yc = flow_top - idx * flow_gap
    ax.add_patch(patches.FancyBboxPatch((FLOW_X - FLOW_HALF_W, yc - 1.3), FLOW_HALF_W * 2, 2.6, boxstyle="round,pad=0.3", linewidth=1.3, edgecolor=edge_color, facecolor=fill_color))
    for li, line in enumerate(lines):
        ax.text(FLOW_X, yc + (len(lines)-1)*0.75 - li * 1.5, line, fontsize=5.9, ha="center", va="center")
    if prev_y is not None:
        ax.annotate("", xy=(FLOW_X, yc + 1.5), xytext=(FLOW_X, prev_y - 1.5), arrowprops=dict(arrowstyle="-|>", color=LGRAY, lw=1.3))
    prev_y = yc

# --- テトリス表描画 ---
for i, row in mart.iterrows():
    if i % 2 == 0: ax.add_patch(patches.Rectangle((0, y - 1.9), LOGICAL_W, row_height, facecolor="#f5f5f5", edgecolor="none"))
    ax.text(COL_NAME_X, y, row["product"] + ("※" if row["is_caplet"] else ""), fontsize=9.5, fontweight="bold")
    cl_ingr = re.sub(r'(塩酸塩|リン酸塩|硫酸塩|臭化水素酸塩|マレイン酸塩|酒石酸塩|フマル酸塩)', '', row["ingredients"])[:26]
    ax.text(COL_INGR_X, y, cl_ingr, fontsize=6.0, color=GRAY)
    ax.text(COL_DOSE_X, y, row["daily"], fontsize=10.3, ha="center")
    ax.text(COL_MULT_X, y, f"×{row['limit']}", fontsize=8.5, ha="center", color=BLUE if row['limit']==7 else ORANGE, fontweight="bold")
    if row["small"] != "-": ax.text(COL_SMALL_X, y, row["small"], fontsize=9, ha="center", bbox=dict(boxstyle="square,pad=0.3", facecolor="white", lw=0.8))
    ax.vlines(COL_BOUND_X, y - 0.95, y + 0.95, color="black", linewidth=1.1)
    ax.text(COL_BOUND_X, y, row["boundary"], fontsize=8.5, ha="center", bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="gray"))
    if row["large"] != "-": ax.text(COL_LARGE_X, y, row["large"], fontsize=9, ha="center", bbox=dict(boxstyle="square,pad=0.3", facecolor="#d9d9d9", linestyle="--", lw=0.8))
    y -= row_height

y -= 1.35
ax.hlines(y, 0, LOGICAL_W, colors="#999999", linewidth=1.0)
y -= 2.0

# ==========================================================
# 下部：トラップ注意 ＆ 【必須質問 5箇条】
# ==========================================================
# 左側：トラップ注意
ax.text(COL_NAME_X, y, "【同ブランド内のトラップ注意】 左(対象外) ⇔ 右(該当)", fontsize=8.5, fontweight="bold", color=GRAY)
traps = [
    ("アレグラ", "FX(通常版)", "FXプレミアム"), ("トラベルミン", "R・ジュニア・ファミリー", "無印 大人用"),
    ("ナロン", "エースT・m 等", "ナロン錠・ナロン顆粒"), ("コンタック", "鼻炎Z", "600プラス・かぜ総合等"),
    ("ルル", "のど飴・トローチ", "内服かぜ薬・ドロップ")
]
ty = y - 2.5
for brand, left, right in traps:
    ax.text(COL_NAME_X, ty, f"・{brand}", fontsize=8)
    ax.text(14.0, ty, left, fontsize=8)
    ax.text(32.0, ty, "⇔", fontsize=8, ha="center")
    ax.text(34.0, ty, right, fontsize=8, color=RED)
    ty -= 2.5

# 右側：必須質問 5箇条
Q_X = 48.0
ax.add_patch(patches.Rectangle((Q_X, y - 16.0), 50.0, 18.0, fill=False, edgecolor=BLUE, linewidth=2.0))
ax.add_patch(patches.Rectangle((Q_X, y), 50.0, 2.5, facecolor=BLUE, edgecolor="none"))
ax.text(Q_X + 25.0, y + 1.2, "レジでの【必須質問 5箇条】 ※該当時は裏面マニュアルへ", fontsize=9, fontweight="bold", ha="center", color="white")

questions = [
    "①【年齢】18歳未満ですか？ (または身分証はお持ちですか？)",
    "②【重複】本日、他店で風邪薬・咳止め等を購入されましたか？",
    "③【体質】アレルギー、喘息、不整脈などの持病はありますか？",
    "④【併用】病院の薬や、他のお薬を飲まれていますか？",
    "⑤【妊婦】妊娠中、または授乳中ではありませんか？"
]
qy = y - 2.0
for q in questions:
    ax.text(Q_X + 1.5, qy, q, fontsize=8.5, fontweight="bold", color="#222222")
    qy -= 2.8

ax.text(Q_X + 1.5, qy, "＋ 複数個希望の方には「どのようなご事情でしょうか？」", fontsize=7.5, color=GRAY)

# --- QR ---
qr_size = 5.0
try:
    qr_img = mpimg.imread(QR_APP_PATH)
    ax.imshow(qr_img, extent=[LOGICAL_W - qr_size - 1, LOGICAL_W - 1, 1, 1 + qr_size])
except: pass
ax.text(LOGICAL_W - qr_size/2 - 1, 1 + qr_size + 0.5, "判定アプリ", fontsize=6, ha="center", fontweight="bold", color=GRAY)

plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches="tight")
plt.close()
print(f"v11【表面】出力完了: {OUTPUT_PNG}")