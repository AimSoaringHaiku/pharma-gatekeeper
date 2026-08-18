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
if "ingredients" not in df.columns:
    df["ingredients"] = ""
else:
    df["ingredients"] = df["ingredients"].fillna("").astype(str).str.strip()

processed = []
judgment_df = df[df["kubun"].isin(["〇", "＊〇"])].copy().dropna(subset=["days", "limit"])
for product, group in judgment_df.groupby("product"):
    valid = group[group["days"] > 0]
    if valid.empty:
        continue
    r = valid.iloc[0]
    amount, unit = extract_amount_unit(r["package"])
    daily_int = int(float(r["daily_dose"]))
    limit = int(float(r["limit"]))
    boundary = limit * daily_int
    small = [str(row["package"]) for _, row in group.iterrows() if row["days"] <= limit]
    large = [str(row["package"]) for _, row in group.iterrows() if row["days"] > limit]
    processed.append({
        "product": product, "daily": f"{daily_int}{unit}", "limit": limit, "boundary": f"{int(boundary)}{unit}",
        "small": " ".join(small) if small else "-", "large": " ".join(large) if large else "-",
        "ingredients": str(r.get("ingredients", "")),
        "is_caplet": product in {"ベンザブロックIP", "ベンザブロックL", "ベンザブロックS", "ベンザブロックTプレミアムDX",
                                  "ベンザブロックIPプレミアム", "ベンザブロックLプレミアムDX", "ベンザブロックSプレミアムDX"}
    })
mart = pd.DataFrame(processed).sort_values("product").reset_index(drop=True)

reference_df = df[df["kubun"].isin(["＊〇", "＊対象外", "△"])].copy()
reference_rows = []
CUSTOM_NOTES = {
    "アレグラFX": "対比: FX(通常版)は対象外/プレミアムのみ血管収縮剤(プソイドエフェドリン)追加で該当。",
    "コリホグス": "中枢抑制作用による呼吸抑制リスク。アルコール・ベンゾ系併用/ODに要注意。",
    "トラベルミンR": "対比: R・ジュニア・ファミリー・「1」は対象外/無印(大人用)のみジフェンヒドラミン含有で該当。",
    "ナロン錠": "対比: エースT・m等は対象外/ナロン錠・顆粒のみブロモバレリル尿素含有で該当。",
    "新コンタック鼻炎Z": "対比: 鼻炎Zのみ対象外(唯一制限成分なし)/600プラス・かぜ総合等は該当。※セチリジンは妊婦禁忌。",
    "新ルルAゴールドDXα": "対比: のど飴・トローチ(部外品)は対象外/内服かぜ薬・メディカルドロップは該当。",
    "葛根湯エキス錠S「コタロー」": "対比: 葛根湯・小青竜湯等の漢方製剤は対象外(マオウは化学成分外で規制対象外)。",
}
for product, group in reference_df.groupby("product", sort=True):
    kubuns = [str(x).strip() for x in group["kubun"] if str(x).strip()]
    kubun_val = kubuns[0] if kubuns else ""
    if kubun_val == "＊〇":
        status_text, status_color = "この商品名は【該当】", RED
    elif kubun_val in ["＊対象外", "△"]:
        status_text, status_color = "【対象外】", "#444444"
    else:
        continue
    final_note = CUSTOM_NOTES.get(product, "")
    reference_rows.append({"product": product, "status_text": status_text,
                            "status_color": status_color, "note": final_note})
reference = pd.DataFrame(reference_rows)
if not reference.empty:
    reference = reference.sort_values("product").reset_index(drop=True)

# ==========================================================
# 2. 描画 (A4 表面)
# ==========================================================
LOGICAL_W, LOGICAL_H = 100.0, 141.4
fig, ax = plt.subplots(figsize=(10, 14.14))
ax.set_position([0, 0, 1, 1])  # savefigでbbox_inches="tight"を使わず全面を使う（A4比率を保つため必須）
ax.set_xlim(0, LOGICAL_W)
ax.set_ylim(0, LOGICAL_H)
ax.axis("off")

COL_NAME_X, COL_INGR_X, COL_DOSE_X, COL_MULT_X = 2.0, 28.0, 48.0, 55.0
COL_SMALL_X, COL_BOUND_X, COL_LARGE_X, FLOW_X = 61.0, 71.0, 81.5, 92.5

# --- タイトル ---
y = LOGICAL_H - 1.7
ax.text(LOGICAL_W / 2, y, "薬剤別 包装区分 早見表", fontsize=19, fontweight="bold", ha="center", va="center")
ax.text(LOGICAL_W, y + 1.4, f"作成日: {datetime.date.today().strftime('%Y/%m/%d')}", fontsize=8, ha="right", va="center", color=LGRAY)
ax.text(LOGICAL_W, y + 0.3, "※AIによる試作品/実使用前に最新の公式情報を確認", fontsize=4.6, ha="right", va="center", color="#999999")

# --- 使い方・販売可否 ---
y -= 1.5
ax.hlines(y + 0.85, 0, LOGICAL_W, colors=BLUE, linewidth=1.2)
y -= 0.1
ax.text(COL_NAME_X, y, "① 18歳未満:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=RED)
ax.text(COL_NAME_X + 12.0, y,
        "小容量1個のみ販売可（氏名・年齢＋他店確認必須）。大容量・複数個(種類違い合算)は理由問わず一律禁止（販売不可）",
        fontsize=6.2, fontweight="bold", ha="left", va="center", color="#333333")
y -= 1.45
ax.text(COL_NAME_X, y, "② 18歳以上:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 12.0, y,
        "小容量は通常販売可（他店確認必須）。大容量・複数個の購入は理由確認が必須（正当な理由がなければ不可）",
        fontsize=6.5, ha="left", va="center", color="#333333")
y -= 1.45
ax.text(COL_NAME_X, y, "③ 年齢確認:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 12.0, y,
        "見た目で18歳以上と判断できない場合、学生証・免許証等の身分証で氏名・年齢を確認。提示なしは販売不可",
        fontsize=6.2, ha="left", va="center", color="#333333")
y -= 1.45
ax.text(COL_NAME_X, y,
        "※年齢に関わらず、この判別は常に「成人(15歳以上)の1日量」で計算します（18歳未満の購入者でも同じ）",
        fontsize=5.5, ha="left", va="center", color=LGRAY)
y -= 1.3
ax.hlines(y, 0, LOGICAL_W, colors="#dddddd", linewidth=0.8)
y -= 1.7

# --- 本体ヘッダー ---
header_y = y
for col_x, label, fs in zip(
        [COL_NAME_X, COL_INGR_X, COL_DOSE_X, COL_MULT_X, COL_SMALL_X, COL_BOUND_X, COL_LARGE_X],
        ["薬剤名", "対象成分", "1日量", "区分", "小包装", "境界", "大包装"],
        [11.5, 11.5, 11.5, 9.6, 11.5, 10.3, 11.5]):
    ax.text(col_x, header_y, label, fontweight="bold", fontsize=fs, ha="left" if col_x < COL_DOSE_X else "center")
ax.text(FLOW_X, header_y, "レジ確認フロー", fontweight="bold", fontsize=8.3, ha="center", va="center", color=GRAY)

y -= 1.15
ax.text(51.8, y, "×7", fontsize=6.1, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(53.2, y, "＝かぜ薬等", fontsize=5.4, ha="left", va="center", color=GRAY)
y -= 1.0
ax.text(COL_NAME_X, y, "小包装＝単品1個は18歳未満も可/大包装＝18歳未満へ不可 ｜ 1日量＝成人(15歳以上)の1日最大服用量",
        fontsize=6.0, ha="left", va="center", color=GRAY)
ax.text(51.8, y, "×5", fontsize=6.1, fontweight="bold", ha="left", va="center", color=ORANGE)
ax.text(53.2, y, "＝それ以外", fontsize=5.4, ha="left", va="center", color=GRAY)

y -= 1.2
ax.hlines(y, 0, LOGICAL_W, linewidth=1.6)
y -= 1.5
table_top_y = y  # レジ確認フローの上端をここに合わせる

row_height = 2.4

# --- テトリス表描画 ---
for i, row in mart.iterrows():
    if i % 2 == 0:
        ax.add_patch(patches.Rectangle((0, y - 1.75), LOGICAL_W, row_height, facecolor="#f5f5f5", edgecolor="none"))
    name_len = len(row["product"])
    name_fs = 9.5 if name_len <= 8 else (8.5 if name_len <= 12 else 7.7)
    ax.text(COL_NAME_X, y, row["product"] + ("※" if row["is_caplet"] else ""), fontsize=name_fs, fontweight="bold", va="center")
    cl_ingr = re.sub(r'(塩酸塩|リン酸塩|硫酸塩|臭化水素酸塩|マレイン酸塩|酒石酸塩|フマル酸塩)', '', row["ingredients"])[:24]
    ax.text(COL_INGR_X, y, cl_ingr, fontsize=5.8, color=GRAY, va="center")
    ax.text(COL_DOSE_X, y, row["daily"], fontsize=10.0, ha="center", va="center")
    ax.text(COL_MULT_X, y, f"×{row['limit']}", fontsize=8.3, ha="center", va="center",
            color=BLUE if row['limit'] == 7 else ORANGE, fontweight="bold")
    if row["small"] != "-":
        ax.text(COL_SMALL_X, y, row["small"], fontsize=8.5, ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.3", facecolor="white", edgecolor="black", linewidth=0.8))
    ax.vlines(COL_BOUND_X, y - 0.9, y + 0.9, color="black", linewidth=1.1)
    ax.text(COL_BOUND_X, y, row["boundary"], fontsize=8.0, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="gray"))
    if row["large"] != "-":
        ax.text(COL_LARGE_X, y, row["large"], fontsize=8.5, ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.3", facecolor="#d9d9d9", edgecolor="black", linestyle="--", linewidth=0.8))
    y -= row_height

table_bottom_y = y  # レジ確認フローの下端をここに合わせる（実測値を使うのが安全）

# --- レジ確認フロー（テーブルの実測範囲に合わせて動的配置） ---
FLOW_HALF_W = 7.0
flow_nodes = [
    (["18歳未満の疑い", "→身分証で確認"], BLUE, "#eef4fc"),
    (["小容量1個のみ", "購入？"], BLUE, "#eef4fc"),
    (["【いいえ】大容量/複数", "→18歳未満は一律禁止", "18歳以上は理由確認"], RED, "#fdecea"),
    (["【はい】小容量1個", "→他店確認必須"], ORANGE, "#fff3e6"),
    (["条件を満たせば", "販売可"], GREEN, "#eaf5ea"),
]
flow_top = table_top_y - 1.0
flow_bottom = table_bottom_y + 1.5
n_flow = len(flow_nodes)
flow_gap = (flow_top - flow_bottom) / (n_flow - 1)
flow_box_h = min(flow_gap - 1.5, 8.0)
prev_y = None
for idx, (lines, edge_color, fill_color) in enumerate(flow_nodes):
    yc = flow_top - idx * flow_gap
    ax.add_patch(patches.FancyBboxPatch((FLOW_X - FLOW_HALF_W, yc - flow_box_h / 2), FLOW_HALF_W * 2, flow_box_h,
                                         boxstyle="round,pad=0.25", linewidth=1.2, edgecolor=edge_color, facecolor=fill_color, zorder=3))
    n_lines = len(lines)
    line_h = 1.5
    start_y = yc + (n_lines - 1) * line_h / 2
    for li, line in enumerate(lines):
        ax.text(FLOW_X, start_y - li * line_h, line, fontsize=5.6, ha="center", va="center", color="#333333")
    if prev_y is not None:
        ax.annotate("", xy=(FLOW_X, yc + flow_box_h / 2 + 0.2), xytext=(FLOW_X, prev_y - flow_box_h / 2 - 0.2),
                    arrowprops=dict(arrowstyle="-|>", color=LGRAY, lw=1.2))
    prev_y = yc

y -= 1.3
ax.text(COL_NAME_X, y, "※＝カプレット表記（ベンザブロック◯◯/末尾「錠」なし）。1日成分量は同一ですが服用粒数が異なります。",
        fontsize=5.6, ha="left", va="center", color="#888888")
y -= 1.5
ax.hlines(y, 0, LOGICAL_W, colors="#999999", linewidth=1.0)
y -= 2.0

# ==========================================================
# 下部：トラップ注意 ＆ 【必須質問 5箇条】
# ==========================================================
bottom_section_top = y

# 左側：トラップ注意
ax.text(COL_NAME_X, y, "【同ブランド内のトラップ注意】 左(対象外) ⇔ 右(該当)", fontsize=8.2, fontweight="bold", color=GRAY)
traps = [
    ("アレグラ", "FX(通常版)", "FXプレミアム"),
    ("トラベルミン", "R・ジュニア・ファミリー", "無印 大人用"),
    ("ナロン", "エースT・m 等", "ナロン錠・ナロン顆粒"),
    ("コンタック", "鼻炎Z", "600プラス・かぜ総合等"),
    ("ルル", "のど飴・トローチ", "内服かぜ薬・ドロップ"),
]
ty = y - 2.3
for brand, left, right in traps:
    ax.text(COL_NAME_X, ty, f"・{brand}", fontsize=7.6)
    ax.text(14.0, ty, left, fontsize=7.6)
    ax.text(32.0, ty, "⇔", fontsize=7.6, ha="center")
    ax.text(34.0, ty, right, fontsize=7.6, color=RED)
    ty -= 2.3
trap_bottom = ty

# 右側：必須質問 5箇条（トラップ欄と高さを揃える）
Q_X = 48.0
Q_W = 50.0
q_box_top = bottom_section_top + 1.0
q_box_bottom = min(trap_bottom, bottom_section_top - 17.0)
q_box_h = q_box_top - q_box_bottom
ax.add_patch(patches.Rectangle((Q_X, q_box_bottom), Q_W, q_box_h, fill=False, edgecolor=BLUE, linewidth=1.8))
ax.add_patch(patches.Rectangle((Q_X, q_box_top - 2.3), Q_W, 2.3, facecolor=BLUE, edgecolor="none"))
ax.text(Q_X + Q_W / 2, q_box_top - 1.15, "レジでの【必須質問 5箇条】 ※該当時は裏面へ", fontsize=8.2, fontweight="bold", ha="center", va="center", color="white")

questions = [
    "①【年齢】18歳未満ですか？（または身分証はお持ちですか？）",
    "②【重複】本日、他店で風邪薬・咳止め等を購入されましたか？",
    "③【体質】アレルギー、喘息、不整脈などの持病はありますか？",
    "④【併用】病院の薬や、他のお薬を飲まれていますか？",
    "⑤【妊婦】妊娠中、または授乳中ではありませんか？",
]
qy = q_box_top - 3.1
q_line_h = (q_box_top - 3.1 - (q_box_bottom + 1.6)) / len(questions)
for q in questions:
    ax.text(Q_X + 1.5, qy, q, fontsize=7.6, fontweight="bold", color="#222222")
    qy -= q_line_h
ax.text(Q_X + 1.5, q_box_bottom + 0.8, "＋ 複数個希望の方には「どのようなご事情でしょうか？」", fontsize=6.8, color=GRAY)

# --- QR（右下・トラップ欄の下） ---
qr_size = 6.5
qr_y_center = trap_bottom - qr_size / 2 - 1.5
qr_x = 90.0
try:
    qr_img = mpimg.imread(QR_APP_PATH)
    ax.imshow(qr_img, extent=[qr_x - qr_size / 2, qr_x + qr_size / 2,
                              qr_y_center - qr_size / 2, qr_y_center + qr_size / 2], zorder=3)
except Exception:
    ax.add_patch(patches.Rectangle((qr_x - qr_size / 2, qr_y_center - qr_size / 2), qr_size, qr_size,
                                   fill=False, edgecolor="#cccccc", zorder=3))
ax.text(qr_x, qr_y_center - qr_size / 2 - 0.8, "判定アプリ", fontsize=6.0, ha="center", va="top", color=GRAY, fontweight="bold")
ax.text(qr_x, qr_y_center - qr_size / 2 - 1.7, "(表にない商品はこちら)", fontsize=4.6, ha="center", va="top", color="#999999")

plt.savefig(OUTPUT_PNG, dpi=300)  # bbox_inches="tight"を使わない（A4比率固定のため）
plt.close()
print(f"v11【表面】出力完了: {OUTPUT_PNG}")
print(f"table_top={table_top_y:.2f} table_bottom={table_bottom_y:.2f} trap_bottom={trap_bottom:.2f} q_box_bottom={q_box_bottom:.2f}")
