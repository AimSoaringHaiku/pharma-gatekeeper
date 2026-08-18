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
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSf7A1Hz3jx1FpkuV-3V7X69qNcNLJao2o-G0K6HbnbrYFlOqA/viewform"

TARGET_INGREDIENTS_LEGEND = (
    "指定8成分: エフェドリン/メチルエフェドリン/プソイドエフェドリン/コデイン/ジヒドロコデイン/"
    "デキストロメトルファン/ジフェンヒドラミン/ブロモバレリル尿素　｜　"
    "非対象（紛らわしい）: 生薬マオウ/無水カフェイン/プロメタジン等の抗ヒス/アリルイソプロピルアセチル尿素"
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
COL_SMALL_X = 61.0
COL_BOUND_X = 71.0
COL_LARGE_X = 81.5
FLOW_X = 92.5

# --- タイトル ---
current_y = LOGICAL_H - 1.7
ax.text(LOGICAL_W / 2, current_y, "薬剤別 包装区分 早見表", fontsize=18.91, fontweight="bold", ha="center", va="center")
today_str = datetime.date.today().strftime("%Y/%m/%d")
ax.text(LOGICAL_W, current_y + 1.4, f"作成日: {today_str}", fontsize=7.93, ha="right", va="center", color="#888888")
ax.text(LOGICAL_W, current_y + 0.3, "※AIによる試作品/実使用前に最新の公式情報(添付文書等)を確認",
        fontsize=4.6, ha="right", va="center", color="#999999")

# --- 使い方・販売可否（①を年齢規制＝この表の根幹に。ルール未経験者でもこの1枚で可否判断できるよう最上部に配置） ---
current_y -= 1.55
ax.hlines(current_y + 0.85, 0, LOGICAL_W, colors=BLUE, linewidth=1.2)
current_y -= 0.15
ax.text(COL_NAME_X, current_y, "① 18歳未満:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=RED)
ax.text(COL_NAME_X + 12.0, current_y,
        "小容量1個のみ販売可（氏名・年齢確認＋他店購入状況確認が必須）。大容量・複数個(種類違いの対象薬も合算)は家族用でも理由問わず一律禁止（販売不可）",
        fontsize=6.3, ha="left", va="center", color="#333333", fontweight="bold")
current_y -= 1.55
ax.text(COL_NAME_X, current_y, "② 18歳以上:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 12.0, current_y,
        "小容量は通常販売可（他店購入状況確認は必須）。大容量・複数個の購入は理由確認が必須（正当な理由がなければ販売不可）",
        fontsize=6.6, ha="left", va="center", color="#333333")
current_y -= 1.55
ax.text(COL_NAME_X, current_y, "③ 年齢確認:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 12.0, current_y,
        "見た目で18歳以上と判断できない場合、学生証・健康保険証・マイナンバーカード・運転免許証等の身分証で氏名・年齢を確認。提示がなければ販売不可",
        fontsize=6.3, ha="left", va="center", color="#333333")
current_y -= 1.55
ax.text(COL_NAME_X, current_y, "④ 商品の確認:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 12.0, current_y, "下表で商品名を検索し「小包装/大包装」どちらの区分か確認（", fontsize=6.6, ha="left", va="center", color="#333333")
ax.text(COL_NAME_X + 38.1, current_y, "×7", fontsize=7.2, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 40.1, current_y, "＝かぜ薬・解熱鎮痛薬・鼻炎用内服薬/", fontsize=6.6, ha="left", va="center", color="#333333")
ax.text(COL_NAME_X + 56.8, current_y, "×5", fontsize=7.2, fontweight="bold", ha="left", va="center", color=ORANGE)
ax.text(COL_NAME_X + 58.8, current_y, "＝それ以外）", fontsize=6.6, ha="left", va="center", color="#333333")
current_y -= 1.35
ax.text(COL_NAME_X + 12.0, current_y,
        "※×7区分は、風邪の諸症状や長引く頭痛・鼻炎など症状が1週間程度続くことが臨床上多いための設定です",
        fontsize=5.6, ha="left", va="center", color=LGRAY)
ax.text(COL_NAME_X + 53.0, current_y, "表にない商品は判定アプリ(右下QR)で確認", fontsize=5.6, ha="left", va="center", color="#888888")
current_y -= 1.45
ax.text(COL_NAME_X, current_y, "よくある質問:", fontsize=6.6, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 11.0, current_y,
        "対象薬を種類違いで1個ずつ購入→複数個扱いで販売不可/身分証の提示を拒否された→年齢確認不能のため販売不可",
        fontsize=6.0, ha="left", va="center", color="#333333")
current_y -= 1.5
ax.hlines(current_y, 0, LOGICAL_W, colors=BLUE, linewidth=1.2)
current_y -= 0.35

# --- 計算手順・ブランド速断・成分判別（実務でよく使う判別系を、本体テーブルの直前に集約） ---
current_y -= 1.55
ax.text(COL_NAME_X, current_y, "計算手順:", fontsize=7.07, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 9.5, current_y,
        "①分類で基準日数(×7=かぜ薬等/×5=それ以外)②1日最大服用量を確認③総量÷1日量=消費日数④基準日数以下=小容量/超=大容量",
        fontsize=6.4, ha="left", va="center", color=GRAY)
current_y -= 1.5
ax.text(COL_NAME_X, current_y, "ブランド速断:", fontsize=7.07, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 10.5, current_y,
        "外用薬・のどスプレー等は全て対象外。原則対象:ルル・パブロン(50除く)・ベンザブロック｜対象外:セデス・ノーシン・バファリン・イブ",
        fontsize=6.4, ha="left", va="center", color=GRAY)
current_y -= 1.55
ax.text(COL_NAME_X, current_y, "成分判別:", fontsize=7.07, fontweight="bold", ha="left", va="center", color=BLUE)
marker(ax, COL_NAME_X + 9.0, current_y, RED, "circle", 0.42)
ax.text(COL_NAME_X + 9.9, current_y,
        "対象(指定8成分)＝エフェドリン/メチルエフェドリン/プソイドエフェドリン/コデイン/ジヒドロコデイン/デキストロメトルファン/ジフェンヒドラミン/ブロモバレリル尿素",
        fontsize=5.9, ha="left", va="center", color=GRAY)
current_y -= 1.4
marker(ax, COL_NAME_X + 9.0, current_y, GREEN, "circle", 0.42)
ax.text(COL_NAME_X + 9.9, current_y,
        "対象外(紛らわしい)＝生薬マオウ/無水カフェイン/プロメタジン等の他の抗ヒス/アリルイソプロピルアセチル尿素",
        fontsize=5.9, ha="left", va="center", color=GRAY)
current_y -= 1.45
ax.hlines(current_y, 0, LOGICAL_W, colors="#dddddd", linewidth=0.8)
current_y -= 0.35

# --- 本体ヘッダー ---
current_y -= 1.75
ax.text(COL_NAME_X, current_y, "薬剤名", fontweight="bold", fontsize=11.59, ha="left", va="center")
ax.text(COL_INGR_X, current_y, "対象成分", fontweight="bold", fontsize=11.59, ha="left", va="center")
ax.text(COL_DOSE_X, current_y, "1日量", fontweight="bold", fontsize=11.59, ha="center", va="center")
ax.text(COL_MULT_X, current_y, "区分", fontweight="bold", fontsize=9.6, ha="center", va="center", color="#666666")
ax.text(COL_SMALL_X, current_y, "小包装", fontweight="bold", fontsize=11.59, ha="center", va="center")
ax.text(COL_BOUND_X, current_y, "境界", fontweight="bold", fontsize=10.37, ha="center", va="center", color="#666666")
ax.text(COL_LARGE_X, current_y, "大包装", fontweight="bold", fontsize=11.59, ha="center", va="center")
ax.text(FLOW_X, current_y, "レジ確認フロー", fontweight="bold", fontsize=8.3, ha="center", va="center", color="#666666")

current_y -= 1.2
ax.text(COL_NAME_X, current_y, "小包装＝単品1個は18歳未満も可/大包装＝18歳未満へ不可　｜　1日量＝成人(15歳以上)の1日最大服用量", fontsize=6.35, ha="left", va="center", color="#555555")
ax.text(52.3, current_y, "×7", fontsize=6.3, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(53.7, current_y, "＝かぜ薬等", fontsize=5.7, ha="left", va="center", color="#555555")
current_y -= 1.05
ax.text(52.3, current_y, "×5", fontsize=6.3, fontweight="bold", ha="left", va="center", color=ORANGE)
ax.text(53.7, current_y, "＝それ以外", fontsize=5.7, ha="left", va="center", color="#555555")
current_y -= 1.05
ax.text(COL_NAME_X, current_y, "※年齢に関わらず、この判別は常に「成人(15歳以上)の1日量」で計算します（18歳未満の購入者でも同じ）",
        fontsize=5.6, ha="left", va="center", color=LGRAY)

current_y -= 1.25
ax.hlines(current_y, 0, LOGICAL_W, linewidth=1.6)
current_y -= 1.6

main_rows = len(mart)
row_height = 2.42

# --- レジ確認フロー（本体テーブル右の空きスペースに縦長ミニフローチャート） ---
FLOW_HALF_W = 7.0
flow_nodes = [
    (["18歳未満の疑い", "→身分証で氏名・", "年齢を確認"], BLUE, "#eef4fc"),
    (["小容量1個のみ", "購入？"], BLUE, "#eef4fc"),
    (["【いいえ】大容量/複数個", "→18歳未満は一律禁止", "18歳以上は理由確認"], RED, "#fdecea"),
    (["【はい】小容量1個", "→18歳未満は氏名+", "他店確認、以上は他店確認"], ORANGE, "#fff3e6"),
    (["条件を満たせば", "販売可"], GREEN, "#eaf5ea"),
]
flow_top = 111.5
flow_bottom = 64.5
n = len(flow_nodes)
flow_gap = (flow_top - flow_bottom) / (n - 1)
flow_box_h = flow_gap - 1.9
prev_y = None
for idx, (lines, edge_color, fill_color) in enumerate(flow_nodes):
    yc = flow_top - idx * flow_gap
    box = patches.FancyBboxPatch((FLOW_X - FLOW_HALF_W, yc - flow_box_h / 2), FLOW_HALF_W * 2, flow_box_h,
                                  boxstyle="round,pad=0.3", linewidth=1.3, edgecolor=edge_color,
                                  facecolor=fill_color, zorder=3)
    ax.add_patch(box)
    n_lines = len(lines)
    line_h = 1.55
    start_y = yc + (n_lines - 1) * line_h / 2
    for li, line in enumerate(lines):
        ax.text(FLOW_X, start_y - li * line_h, line, fontsize=5.9, ha="center", va="center", color="#333333")
    if prev_y is not None:
        ax.annotate("", xy=(FLOW_X, yc + flow_box_h / 2 + 0.2), xytext=(FLOW_X, prev_y - flow_box_h / 2 - 0.2),
                    arrowprops=dict(arrowstyle="-|>", color="#999999", lw=1.3))
    prev_y = yc

for i, row in mart.iterrows():
    if i % 2 == 0:
        ax.add_patch(patches.Rectangle((0, current_y - 1.9), LOGICAL_W, row_height, facecolor="#f5f5f5", edgecolor="none", zorder=0))

    name_len = len(row["product"])
    name_fontsize = 10.3 if name_len <= 8 else (9.2 if name_len <= 12 else 8.2)
    name_text = row["product"] + ("※" if row["is_caplet"] else "")
    ax.text(COL_NAME_X, current_y, name_text, fontsize=name_fontsize, fontweight="bold", ha="left", va="center")

    if row["ingredients"]:
        clean_ingr = re.sub(r'(塩酸塩|リン酸塩|硫酸塩|臭化水素酸塩|マレイン酸塩|酒石酸塩|フマル酸塩)', '', row["ingredients"])
        if len(clean_ingr) > 26:
            clean_ingr = clean_ingr[:26] + "…"
        ax.text(COL_INGR_X, current_y, clean_ingr, fontsize=5.8, ha="left", va="center", color="#666666")
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
        "※＝カプレット表記（ベンザブロック◯◯/末尾「錠」なし）。1日成分量は「◯◯錠」と同一ですが服用粒数が異なります。",
        fontsize=6.1, ha="left", va="center", color="#888888")

# --- ゾーン区分：ここから下は「精査ゾーン」（安全確認業務の質を担保する詳細情報） ---
current_y -= 1.1
zone_top = current_y + 0.55
ax.add_patch(patches.Rectangle((0, -3), LOGICAL_W, zone_top + 3, facecolor="#eaecef", edgecolor="none", zorder=-2))
ax.text(LOGICAL_W / 2, current_y, "▼ ここからは安全確認を担保するための精査ゾーン（必要に応じて確認）",
        fontsize=6.0, fontweight="bold", ha="center", va="center", color="#8a8a8a", style="italic")
current_y -= 0.55

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
        current_y -= 2.44

current_y -= 0.65
ax.hlines(current_y, 0, LOGICAL_W, colors="#dddddd", linewidth=0.7)
current_y -= 1.08

# --- QR（右側に縦積み。詳細参考テキストと横並びにして高さを共有） ---
detail_top = current_y

def wrap_by_width(text, chars_per_line):
    return [text[i:i + chars_per_line] for i in range(0, len(text), chars_per_line)]

qr_size = 6.4
QR_X = 89.5

qr1_top = detail_top - 0.2
qr1_center_y = qr1_top - qr_size / 2
try:
    qr_img = mpimg.imread(QR_APP_PATH)
    ax.imshow(qr_img, extent=[QR_X - qr_size/2, QR_X + qr_size/2,
                              qr1_center_y - qr_size/2, qr1_center_y + qr_size/2], zorder=3)
except Exception:
    ax.add_patch(patches.Rectangle((QR_X - qr_size/2, qr1_center_y - qr_size/2), qr_size, qr_size,
                                   fill=False, edgecolor="#cccccc", zorder=3))
qr1_y = qr1_center_y - qr_size/2 - 0.85
ax.text(QR_X, qr1_y, "判定アプリ", fontsize=6.8, ha="center", va="top", color="#555555", fontweight="bold")
qr1_y -= 1.05
ax.text(QR_X, qr1_y, "(表にない商品はこちら)", fontsize=5.0, ha="center", va="top", color="#999999")
qr1_y -= 0.85
ax.text(QR_X, qr1_y, APP_URL.replace("https://", ""), fontsize=3.7, ha="center", va="top", color="#999999")

qr2_top = qr1_y - 1.7
qr2_center_y = qr2_top - qr_size / 2
try:
    qr_img2 = mpimg.imread(QR_FORM_PATH)
    ax.imshow(qr_img2, extent=[QR_X - qr_size/2, QR_X + qr_size/2,
                               qr2_center_y - qr_size/2, qr2_center_y + qr_size/2], zorder=3)
except Exception:
    ax.add_patch(patches.Rectangle((QR_X - qr_size/2, qr2_center_y - qr_size/2), qr_size, qr_size,
                                   fill=False, edgecolor="#cccccc", zorder=3))
qr2_y = qr2_center_y - qr_size/2 - 0.85
ax.text(QR_X, qr2_y, "ご意見・改善案", fontsize=6.8, ha="center", va="top", color="#555555", fontweight="bold")
qr2_y -= 1.05
# FORM_URL_SHORT に短縮URL（例: qr.quel.jp等で発行したもの）を設定すると、QRの下にテキスト表示されます。
FORM_URL_SHORT = ""
if FORM_URL_SHORT:
    ax.text(QR_X, qr2_y, FORM_URL_SHORT, fontsize=4.4, ha="center", va="top", color="#999999")
    qr2_y -= 1.0

# --- 詳細参考資料の要約（旧2ページ目を集約・QR列を避けて配置） ---
DL, DR = 0.0, 82.0  # 本文カラム幅（右のQR縦積み列を避ける）
y = detail_top
ax.hlines(y, 0, LOGICAL_W, colors="#999999", linewidth=1.0)
y -= 1.62
ax.text(COL_NAME_X, y, "【詳細参考】医療エビデンス・授乳婦指導・必須質問（相談時の深掘り用/販売可否・判別は最上部を参照）",
        fontsize=9.15, fontweight="bold", ha="left", va="center")
y -= 1.84

# E. 医療エビデンス（1行要約×3）
ax.text(COL_NAME_X, y, "過量服薬リスク:", fontsize=7.07, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 12.0, y, "初日=急性心毒性(無水カフェイン等)で致死性不整脈。3日目以降=劇症肝不全(アセトアミノフェン)が急速進行",
        fontsize=6.59, ha="left", va="center", color=GRAY)
y -= 1.5
ax.text(COL_NAME_X + 12.0, y, "(NSAIDsは服用後すぐ胃痛等の自覚症状が出るが、AAPは無症状のまま進行するため特に注意)",
        fontsize=6.0, ha="left", va="center", color=LGRAY)
y -= 1.5
ax.text(COL_NAME_X + 12.0, y, "頭痛が月15日以上ある環境下で複合鎮痛薬を月10日超・3ヶ月超服用すると薬剤乱用頭痛(MOH)に進展しやすい",
        fontsize=6.4, ha="left", va="center", color=GRAY)
y -= 2.0

# F. 授乳婦指導（色マーカー4段）
ax.text(COL_NAME_X, y, "授乳婦指導:", fontsize=7.07, fontweight="bold", ha="left", va="center", color=BLUE)
# ▼ y -= 1.62 を削除し、1行目から並べる
nursing_rows = [
    (GREEN, "circle", "通常授乳可", "アセトアミノフェン/イブプロフェン/無水カフェイン(通常量)"),
    (ORANGE, "circle", "服薬後2-4h授乳回避", "デキストロメトルファン/ジフェンヒドラミン(短期)"),
    (RED, "circle", "搾乳破棄(半減期×3-4h)", "クロルフェニラミン(長期)/プロメタジン/ブロモバレリル尿素"),
    (DARKRED, "square", "代替薬へ変更提案", "コデイン/ジヒドロコデイン(乳児モルヒネ代謝リスク)"),
]
for color, shape, tag, ingr in nursing_rows:
    marker(ax, COL_NAME_X + 12.0, y, color, shape, 0.45)  # X座標を+12.0ずらしてタイトル横に配置
    ax.text(COL_NAME_X + 13.2, y, ingr, fontsize=6.3, fontweight="bold", ha="left", va="center", color="#333333")
    ax.text(COL_NAME_X + 41.0, y, "→ " + tag, fontsize=6.4, fontweight="bold", ha="left", va="center", color=color)
    y -= 1.51

# G. 必須質問5箇条（青枠を外し、他と同じテキストベースのレイアウトに変更）
y -= 0.5
ax.text(COL_NAME_X, y, "レジでの必須質問:", fontsize=7.07, fontweight="bold", ha="left", va="center", color=BLUE)
# タイトルの下に小さく補足を表示
ax.text(COL_NAME_X, y - 1.5, "※該当時は", fontsize=5.5, ha="left", va="center", color=GRAY)
ax.text(COL_NAME_X, y - 2.5, "裏面を参照", fontsize=5.5, ha="left", va="center", color=GRAY)

questions = [
    "①【年齢】18歳未満ですか？（または身分証はお持ちですか？）",
    "②【重複】本日、他店で風邪薬・咳止め等を購入されましたか？",
    "③【体質】アレルギー、喘息、不整脈などの持病はありますか？",
    "④【併用】病院の薬や、他のお薬を飲まれていますか？",
    "⑤【妊婦】妊娠中、または授乳中ではありませんか？",
]
for q in questions:
    ax.text(COL_NAME_X + 12.0, y, q, fontsize=6.6, fontweight="bold", ha="left", va="center", color="#222222")
    y -= 1.55
ax.text(COL_NAME_X + 12.0, y, "＋ 複数個希望の方には「どのようなご事情でしょうか？」", fontsize=5.9, ha="left", va="center", color=GRAY)
y -= 1.5

y -= 0.25
ax.text(COL_NAME_X, y,
        "免責: 過去に用法用量超過の自己判断服用で重篤な健康被害が生じた事例を踏まえた確認です。意図的な過量服薬は保証・救済制度の対象外です。",
        fontsize=6.1, ha="left", va="center", color=LGRAY)
y -= 0.85
ax.text(COL_NAME_X, y,
        "準拠: 厚生労働省 局長通知「指定濫用防止医薬品の指定について」・厚生労働大臣が定める数量（告示）/JSMI「指定濫用防止医薬品の販売制度について」/兵庫県 薬務課 制度改正資料",
        fontsize=4.8, ha="left", va="center", color="#aaaaaa")

plt.savefig(OUTPUT_PNG, dpi=300)
plt.close()

print("==========================================")
print("v11【表面】A4 早見表生成完了")
print(f"出力ファイル: {OUTPUT_PNG}")
print(f"最終y座標(0付近が理想): {y:.2f}")
print("==========================================")
