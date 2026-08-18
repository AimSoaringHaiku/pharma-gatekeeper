import pandas as pd
import re
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import japanize_matplotlib

PACKAGE_CSV = "package_verification.csv"
OUTPUT_PNG = "atomic_card_table_v9_single_page.png"
QR_APP_PATH = "QR_667832.png"
QR_FORM_PATH = "QR_form.png"
APP_URL = "https://aimsoaringhaiku.github.io/pharma-gatekeeper/"
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7A1Hz3jx1FpkuV-3V7X69qNcNLJao2o-G0K6HbnbrYFlOqA/viewform"

TARGET_INGREDIENTS_LEGEND = (
    "指定8成分: エフェドリン/メチルエフェドリン/プソイドエフェドリン/コデイン/ジヒドロコデイン/"
    "デキストロメトルファン/ジフェンヒドラミン/ブロモバレリル尿素　｜　"
    "非対象（紛らわしい）: 生薬マオウ／無水カフェイン／プロメタジン等の抗ヒス／アリルイソプロピルアセチル尿素"
)

GRAY = "#555555"
LGRAY = "#888888"
RED = "#d32f2f"
BLUE = "#1565c0"
GREEN = "#2e7d32"
ORANGE = "#e65100"
DARKRED = "#8e0000"


def extract_amount_unit(package_str):
    text = str(package_str)
    match = re.search(r"([\d\.]+)", text)
    unit_match = re.search(r"[^\d\.]+", text)
    amount = float(match.group(1)) if match else 0
    unit = unit_match.group(0).strip() if unit_match else ""
    return amount, unit


def shorten_note(text, max_len=60):
    text = str(text).replace("\\n", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if text == "nan" or text == "None":
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


def marker(ax, x, y, color, shape="circle", size=0.55):
    if shape == "circle":
        ax.add_patch(patches.Circle((x, y), size, facecolor=color, edgecolor="none", zorder=3))
    else:
        ax.add_patch(patches.Rectangle((x - size, y - size), size * 2, size * 2,
                                        facecolor=color, edgecolor="none", zorder=3))


CAPLET_PRODUCTS = {
    "ベンザブロックIP", "ベンザブロックL", "ベンザブロックS", "ベンザブロックTプレミアムDX",
    "ベンザブロックIPプレミアム", "ベンザブロックLプレミアムDX", "ベンザブロックSプレミアムDX",
}

# ==========================================================
# 1. データの読み込み・集計（vpc_v8と同一ロジック）
# ==========================================================
df = pd.read_csv(PACKAGE_CSV, encoding="utf-8-sig")
df["kubun"] = df["kubun"].fillna("").astype(str).str.strip()
df["days"] = pd.to_numeric(df["days"], errors="coerce")
df["limit"] = pd.to_numeric(df["limit"], errors="coerce")
if "ingredients" not in df.columns:
    df["ingredients"] = ""
else:
    df["ingredients"] = df["ingredients"].fillna("").astype(str).str.strip()

judgment_df = df[df["kubun"].isin(["〇", "＊〇"])].copy().dropna(subset=["days", "limit"])
processed = []
for product, group in judgment_df.groupby("product"):
    valid = group[group["days"] > 0]
    if valid.empty:
        continue
    r = valid.iloc[0]
    amount, unit = extract_amount_unit(r["package"])
    daily_int = int(float(r["daily_dose"]))
    daily_str = f"{daily_int}{unit}"
    limit = int(float(r["limit"]))
    boundary = limit * daily_int
    boundary_str = f"{int(boundary)}{unit}"
    small, large = [], []
    for _, row in group.iterrows():
        if row["days"] <= limit:
            small.append(str(row["package"]))
        else:
            large.append(str(row["package"]))
    processed.append({
        "product": product, "daily": daily_str, "limit": limit, "boundary": boundary_str,
        "small": " ".join(small) if small else "-", "large": " ".join(large) if large else "-",
        "ingredients": str(r.get("ingredients", "")), "is_caplet": product in CAPLET_PRODUCTS,
    })
mart = pd.DataFrame(processed).sort_values("product").reset_index(drop=True)

reference_df = df[df["kubun"].isin(["＊〇", "＊対象外", "△"])].copy()
reference_rows = []
CUSTOM_NOTES = {
    "アレグラFX": "対比: FX(通常版)は対象外／プレミアムのみ血管収縮剤(プソイドエフェドリン)追加で該当。",
    "コリホグス": "中枢抑制作用による呼吸抑制リスク。アルコール・ベンゾ系併用/ODに要注意。",
    "トラベルミンR": "対比: R・ジュニア・ファミリー・「1」は対象外／無印(大人用)のみジフェンヒドラミン含有で該当。",
    "ナロン錠": "対比: エースT・m等は対象外／ナロン錠・顆粒のみブロモバレリル尿素含有で該当。",
    "新コンタック鼻炎Z": "対比: 鼻炎Zのみ対象外(唯一制限成分なし)／600プラス・かぜ総合等は該当。※セチリジンは妊婦禁忌。",
    "新ルルAゴールドDXα": "対比: のど飴・トローチ(部外品)は対象外／内服かぜ薬・メディカルドロップは該当。",
    "葛根湯エキス錠S「コタロー」": "対比: 葛根湯・小青竜湯等の漢方製剤は対象外(マオウは化学成分外で規制対象外)。",
}
for product, group in reference_df.groupby("product", sort=True):
    kubuns = [str(x).strip() for x in group["kubun"] if str(x).strip()]
    kubun_val = kubuns[0] if kubuns else ""
    if kubun_val == "＊〇":
        status_text, status_color = "この商品名は【該当】", "#d32f2f"
    elif kubun_val in ["＊対象外", "△"]:
        status_text, status_color = "【対象外】", "#444444"
    else:
        continue
    if product in CUSTOM_NOTES:
        final_note = CUSTOM_NOTES[product]
    else:
        notes = [str(x).strip() for x in group["note"] if str(x).strip() and str(x).strip() != "nan"]
        final_note = shorten_note(" / ".join(list(dict.fromkeys(notes))))
    reference_rows.append({"product": product, "status_text": status_text,
                            "status_color": status_color, "note": final_note})
reference = pd.DataFrame(reference_rows)
if not reference.empty:
    reference = reference.sort_values("product").reset_index(drop=True)

# ==========================================================
# 2. 描画 (A4 1枚固定レイアウト・情報量2ページ分を集約)
# ==========================================================
LOGICAL_W = 100.0
LOGICAL_H = 141.4

fig, ax = plt.subplots(figsize=(10, 14.14))
ax.set_position([0, 0, 1, 1])
ax.set_xlim(0, LOGICAL_W)
ax.set_ylim(0, LOGICAL_H)
ax.axis("off")

COL_NAME_X = 2.0
COL_INGR_X = 28.0
COL_DOSE_X = 48.0
COL_MULT_X = 55.0
COL_SMALL_X = 65.5
COL_BOUND_X = 78.5
COL_LARGE_X = 91.5

# --- タイトル ---
current_y = LOGICAL_H - 1.7
ax.text(LOGICAL_W / 2, current_y, "薬剤別 包装区分 早見表", fontsize=18.91, fontweight="bold", ha="center", va="center")
today_str = datetime.date.today().strftime("%Y/%m/%d")
ax.text(LOGICAL_W, current_y + 1.4, f"作成日: {today_str}", fontsize=7.93, ha="right", va="center", color="#888888")

current_y -= 2.32
ax.text(LOGICAL_W / 2, current_y,
        "※本表はAIを用いて作成した試作品です。実使用前に最新の公式情報(添付文書・KEGG等)をご確認ください。",
        fontsize=6.71, ha="center", va="center", color="#888888")

# --- 本体ヘッダー ---
current_y -= 2.92
ax.text(COL_NAME_X, current_y, "薬剤名", fontweight="bold", fontsize=11.59, ha="left", va="center")
ax.text(COL_INGR_X, current_y, "対象成分", fontweight="bold", fontsize=11.59, ha="left", va="center")
ax.text(COL_DOSE_X, current_y, "1日量", fontweight="bold", fontsize=11.59, ha="center", va="center")
ax.text(COL_SMALL_X, current_y, "小包装", fontweight="bold", fontsize=11.59, ha="center", va="center")
ax.text(COL_BOUND_X, current_y, "境界", fontweight="bold", fontsize=10.37, ha="center", va="center", color="#666666")
ax.text(COL_LARGE_X, current_y, "大包装", fontweight="bold", fontsize=11.59, ha="center", va="center")

current_y -= 1.19
ax.text(COL_INGR_X, current_y,
        "指定8成分: エフェドリン/メチルエフェドリン/プソイドエフェドリン/コデイン/ジヒドロコデイン/デキストロメトルファン/ジフェンヒドラミン/ブロモバレリル尿素",
        fontsize=4.64, ha="left", va="center", color="#999999")
current_y -= 1.08
ax.text(COL_INGR_X, current_y,
        "非対象(紛らわしい): 生薬マオウ／無水カフェイン／プロメタジン等の抗ヒス／アリルイソプロピルアセチル尿素",
        fontsize=4.64, ha="left", va="center", color="#999999")

current_y -= 1.35
ax.text(COL_NAME_X, current_y,
        "小包装＝単品1個は18歳未満も可／大包装＝18歳未満へ不可　｜　1日量＝成人(15歳以上)の1日最大服用量　｜　×5・×7＝容量区分の基準日数",
        fontsize=6.35, ha="left", va="center", color="#555555")

current_y -= 1.35
ax.hlines(current_y, 0, LOGICAL_W, linewidth=1.6)
current_y -= 1.84

main_rows = len(mart)
row_height = 2.83

for i, row in mart.iterrows():
    if i % 2 == 0:
        ax.add_patch(patches.Rectangle((0, current_y - 1.9), LOGICAL_W, row_height, facecolor="#f5f5f5", edgecolor="none", zorder=0))

    name_len = len(row["product"])
    name_fontsize = 10.3 if name_len <= 8 else (9.2 if name_len <= 12 else 8.2)
    name_text = row["product"] + ("※" if row["is_caplet"] else "")
    ax.text(COL_NAME_X, current_y, name_text, fontsize=name_fontsize, fontweight="bold", ha="left", va="center")

    if row["ingredients"]:
        clean_ingr = re.sub(r'(塩酸塩|リン酸塩|硫酸塩|臭化水素酸塩|マレイン酸塩|酒石酸塩|フマル酸塩)', '', row["ingredients"])
        if len(clean_ingr) > 12:
            clean_ingr = clean_ingr[:12] + "…"
        ax.text(COL_INGR_X, current_y, clean_ingr, fontsize=6.48, ha="left", va="center", color="#666666")
    else:
        ax.text(COL_INGR_X, current_y, "-", fontsize=7.93, ha="left", va="center", color="#aaaaaa")

    ax.text(COL_DOSE_X, current_y, row["daily"], fontsize=10.37, ha="center", va="center")

    mult_color = "#1565c0" if row["limit"] == 7 else "#e65100"
    ax.text(COL_MULT_X, current_y, f"×{row['limit']}", fontsize=8.54, ha="center", va="center",
            color=mult_color, fontweight="bold")

    if row["small"] != "-":
        ax.text(COL_SMALL_X, current_y, row["small"], fontsize=8.91, ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.3", facecolor="white", edgecolor="black", linewidth=0.8))

    ax.vlines(COL_BOUND_X, current_y - 0.95, current_y + 0.95, color="black", linewidth=1.1, zorder=1)
    ax.text(COL_BOUND_X, current_y, row["boundary"], fontsize=8.54, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="gray"), zorder=2)

    if row["large"] != "-":
        ax.text(COL_LARGE_X, current_y, row["large"], fontsize=8.91, ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.3", facecolor="#d9d9d9", edgecolor="black", linestyle="--", linewidth=0.8))

    current_y -= row_height

current_y -= 1.35
ax.text(COL_NAME_X, current_y,
        "※＝カプレット表記（ベンザブロック◯◯／末尾「錠」なし）。1日成分量は「◯◯錠」と同一ですが服用粒数が異なります。",
        fontsize=6.1, ha="left", va="center", color="#888888")

# --- 判定注意・参考（マトリックス） ---
ref_rows = len(reference) if not reference.empty else 0
if ref_rows > 0:
    current_y -= 1.03
    ax.hlines(current_y, 0, LOGICAL_W, colors="black", linewidth=1.1)
    current_y -= 1.84

    ax.text(COL_NAME_X, current_y, "判定注意・参考", fontsize=10.37, fontweight="bold", ha="left", va="center")
    ax.text(28.0, current_y, "指定濫用判定", fontsize=8.54, fontweight="bold", ha="center", va="center")
    ax.text(41.0, current_y, "同ブランド内比較・注釈（「対比:」＝取り違え注意ポイント）", fontsize=8.54, fontweight="bold", ha="left", va="center")

    current_y -= 1.4
    ax.hlines(current_y, 0, LOGICAL_W, colors="#cccccc", linewidth=0.8)
    current_y -= 2.0

    for j, (_, row) in enumerate(reference.iterrows()):
        if j % 2 == 0:
            ax.add_patch(patches.Rectangle((0, current_y - 0.95), LOGICAL_W, 1.9, facecolor="#fafafa", edgecolor="none"))
        ax.text(COL_NAME_X, current_y, row["product"], fontsize=8.42, fontweight="bold", ha="left", va="center")
        ax.text(28.0, current_y, row["status_text"], fontsize=8.42, fontweight="bold", ha="center", va="center", color=row["status_color"])
        note_color = RED if row["note"].startswith("対比") else GRAY
        ax.text(41.0, current_y, row["note"], fontsize=7.34, ha="left", va="center", color=note_color)
        current_y -= 2.54

current_y -= 0.65
ax.hlines(current_y, 0, LOGICAL_W, colors="#dddddd", linewidth=0.7)
current_y -= 1.08

# --- QR（右下） ---
qr_size = 7.0
qr_y_center = current_y - qr_size / 2 - 0.6
qr1_x = 80.0
try:
    qr_img = mpimg.imread(QR_APP_PATH)
    ax.imshow(qr_img, extent=[qr1_x - qr_size/2, qr1_x + qr_size/2,
                              qr_y_center - qr_size/2, qr_y_center + qr_size/2], zorder=3)
except Exception:
    ax.add_patch(patches.Rectangle((qr1_x - qr_size/2, qr_y_center - qr_size/2), qr_size, qr_size,
                                   fill=False, edgecolor="#cccccc", zorder=3))
ax.text(qr1_x, qr_y_center - qr_size/2 - 0.9, "判定アプリ", fontsize=7.32, ha="center", va="top",
        color="#555555", fontweight="bold")
ax.text(qr1_x, qr_y_center - qr_size/2 - 1.9, APP_URL, fontsize=4.4, ha="center", va="top", color="#999999")

qr2_x = 92.0
try:
    qr_img2 = mpimg.imread(QR_FORM_PATH)
    ax.imshow(qr_img2, extent=[qr2_x - qr_size/2, qr2_x + qr_size/2,
                               qr_y_center - qr_size/2, qr_y_center + qr_size/2], zorder=3)
except Exception:
    ax.add_patch(patches.Rectangle((qr2_x - qr_size/2, qr_y_center - qr_size/2), qr_size, qr_size,
                                   fill=False, edgecolor="#cccccc", zorder=3))
ax.text(qr2_x, qr_y_center - qr_size/2 - 0.9, "ご意見・改善案", fontsize=7.32, ha="center", va="top",
        color="#555555", fontweight="bold")

# 右下QR分の高さに揃え、左側スペースに「詳細参考(要約)」を並べて配置
right_block_bottom = qr_y_center - qr_size/2 - 1.9 - 0.8
detail_top = current_y  # QR/トラップ区切り線の直後の高さを起点に、左カラムへ詳細要約を追加
detail_bottom = right_block_bottom

# ==========================================================
# 3. 詳細参考資料の要約（旧2ページ目を集約・左カラムに配置）
# ==========================================================
DL, DR = 0.0, 74.0  # 左カラム幅（QR列を避ける）
y = detail_top
ax.hlines(y, 0, LOGICAL_W, colors="#999999", linewidth=1.0)
y -= 1.62
ax.text(COL_NAME_X, y, "【詳細参考】計算手順・販売ルール・判別・エビデンス（相談時の深掘り用）",
        fontsize=9.15, fontweight="bold", ha="left", va="center")
y -= 1.84

# A. 計算手順（1行に凝縮）
ax.text(COL_NAME_X, y, "計算手順:", fontsize=7.07, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 8.5, y,
        "①分類で基準日数(かぜ薬等=7日/それ以外=5日)②1日最大服用量を確認③総量÷1日量=消費日数④基準日数以下=小容量/超=大容量",
        fontsize=6.59, ha="left", va="center", color=GRAY)
y -= 2.05

# B. 販売ルール（ミニ表）
ax.text(COL_NAME_X, y, "販売ルール:", fontsize=7.07, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 9.5, y, "18歳未満・小容量1個＝氏名年齢確認必須＋他店購入状況確認必須で条件付き販売可／",
        fontsize=6.59, ha="left", va="center", color=GRAY)
y -= 1.62
ax.text(COL_NAME_X + 9.5, y, "18歳以上・小容量1個＝他店購入状況確認のみ必須で通常販売可",
        fontsize=6.59, ha="left", va="center", color=GRAY)
y -= 1.62
ax.text(COL_NAME_X + 9.5, y, "※大容量・複数個の18歳未満への販売は理由問わず一律禁止",
        fontsize=6.59, ha="left", va="center", color=RED, fontweight="bold")
y -= 2.05

# C. 瞬時の判別（ブランド速断）
ax.text(COL_NAME_X, y, "ブランド速断:", fontsize=7.07, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 10.5, y, "外用薬・のどスプレー等は全て対象外。抗ヒスは「ジフェンヒドラミンのみ」該当",
        fontsize=6.59, ha="left", va="center", color=GRAY)
y -= 1.62
ax.text(COL_NAME_X + 10.5, y, "原則対象: ルル・パブロン(50除く)・ベンザブロック　｜　対象外: セデス・ノーシン・バファリン・イブ",
        fontsize=6.59, ha="left", va="center", color=GRAY)
y -= 2.05

# D. 成分判別
ax.text(COL_NAME_X, y, "成分判別:", fontsize=7.07, fontweight="bold", ha="left", va="center", color=BLUE)
marker(ax, COL_NAME_X + 9.0, y, RED, "circle", 0.45)
ax.text(COL_NAME_X + 10.0, y, "対象＝エフェドリン系/コデイン系/デキストロメトルファン/ジフェンヒドラミン/ブロモバレリル尿素",
        fontsize=6.59, ha="left", va="center", color=GRAY)
y -= 1.62
marker(ax, COL_NAME_X + 9.0, y, GREEN, "circle", 0.45)
ax.text(COL_NAME_X + 10.0, y, "対象外＝生薬マオウ/無水カフェイン/プロメタジン等の他の抗ヒス/アリルイソプロピルアセチル尿素",
        fontsize=6.59, ha="left", va="center", color=GRAY)
y -= 2.05

# E. 医療エビデンス（1行要約×3）
ax.text(COL_NAME_X, y, "過量服薬リスク:", fontsize=7.07, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 12.0, y, "初日=急性心毒性(無水カフェイン等)で致死性不整脈。3日目以降=劇症肝不全(アセトアミノフェン)が急速進行",
        fontsize=6.59, ha="left", va="center", color=GRAY)
y -= 1.62
ax.text(COL_NAME_X + 12.0, y, "月10日超・3ヶ月超の定期服用は薬剤乱用頭痛(MOH)に進展しやすい",
        fontsize=6.59, ha="left", va="center", color=GRAY)
y -= 2.05

# F. 授乳婦指導（色マーカー4段）
ax.text(COL_NAME_X, y, "授乳婦指導:", fontsize=7.07, fontweight="bold", ha="left", va="center", color=BLUE)
y -= 1.62
nursing_rows = [
    (GREEN, "circle", "通常授乳可", "アセトアミノフェン/イブプロフェン/無水カフェイン(通常量)"),
    (ORANGE, "circle", "服薬後2-4h授乳回避", "デキストロメトルファン/ジフェンヒドラミン(短期)"),
    (RED, "circle", "搾乳破棄(半減期×3-4h)", "クロルフェニラミン(長期)/プロメタジン/ブロモバレリル尿素"),
    (DARKRED, "square", "代替薬へ変更提案", "コデイン/ジヒドロコデイン(乳児モルヒネ代謝リスク)"),
]
for color, shape, tag, ingr in nursing_rows:
    marker(ax, COL_NAME_X + 1.0, y, color, shape, 0.45)
    ax.text(COL_NAME_X + 2.2, y, tag, fontsize=6.59, fontweight="bold", ha="left", va="center", color="#333333")
    ax.text(COL_NAME_X + 16.0, y, ingr, fontsize=6.35, ha="left", va="center", color=GRAY)
    y -= 1.51

y -= 0.32
ax.text(COL_NAME_X, y,
        "免責: 過去に用法用量超過の自己判断服用で重篤な健康被害が生じた事例を踏まえた確認です。意図的な過量服薬は保証・救済制度の対象外です。",
        fontsize=6.1, ha="left", va="center", color=LGRAY)

plt.savefig(OUTPUT_PNG, dpi=300)
plt.close()

print("==========================================")
print("v9（A4 1枚集約版） 早見表生成完了")
print(f"出力ファイル: {OUTPUT_PNG}")
print(f"最終y座標(0付近が理想): {y:.2f}")
print("==========================================")
