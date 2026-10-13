import pandas as pd
import re
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import japanize_matplotlib

PACKAGE_CSV = "package_verification.csv"
OUTPUT_PNG = "atomic_card_table_v12_front.png"
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
INK = "#1a1a1a"  # 白黒印刷を基本とし、×7/×5・成分判別マーカー・解釈層(☞)以外の見出し等はこの色に統一


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


def draw_point_seal(ax, cx, cy, label, r=1.1, color=RED, fontsize=3.4, rotation=-6):
    """視線誘導用の「ハンコ風ポイントシール」。二重丸＋白抜き文字。
    塗り色だけに頼らず二重の輪郭線で作るため、白黒印刷でも判別できる。"""
    ax.add_patch(patches.Circle((cx, cy), r, facecolor=color, edgecolor="white", linewidth=0.9, zorder=6))
    ax.add_patch(patches.Circle((cx, cy), r * 0.74, facecolor="none", edgecolor="white",
                                 linewidth=0.5, linestyle=(0, (1, 1)), zorder=7))
    ax.text(cx, cy, label, fontsize=fontsize, fontweight="bold", ha="center", va="center",
            color="white", zorder=8, rotation=rotation)


def draw_magnifier_icon(ax, x, y, r=0.62, handle_len=0.85, color=RED, angle_deg=-40):
    """虫眼鏡アイコン：レンズ(円)＋斜めの持ち手。持ち手の先端座標を返す（そこから説明文を続ける）。"""
    import math
    rad = math.radians(angle_deg)
    dx, dy = math.cos(rad), math.sin(rad)
    edge_x, edge_y = x + r * dx, y + r * dy
    tip_x, tip_y = x + (r + handle_len) * dx, y + (r + handle_len) * dy
    ax.add_patch(patches.Circle((x, y), r, facecolor="white", edgecolor=color, linewidth=1.1, zorder=8))
    ax.plot([edge_x, tip_x], [edge_y, tip_y], color=color, linewidth=1.6, solid_capstyle="round", zorder=8)
    return tip_x, tip_y


def draw_eye_guide(ax, x, y, text, color=RED, fontsize=5.0, ha="left"):
    """短い道案内（解釈層）。虫眼鏡アイコン＋断定しすぎない一言を、白抜き吹き出しで軽く強調する。"""
    icon_r = fontsize * 0.11
    icon_cx = x + icon_r * 1.3 if ha == "left" else x - icon_r * 1.3
    tip_x, _ = draw_magnifier_icon(ax, icon_cx, y + icon_r * 0.7, r=icon_r, handle_len=icon_r * 1.6,
                                    color=color, angle_deg=-40 if ha == "left" else -140)
    text_x = tip_x + icon_r * 0.6 if ha == "left" else tip_x - icon_r * 0.6
    ax.text(text_x, y, text, fontsize=fontsize, fontweight="bold", ha=ha, va="center",
            color=color, fontstyle="italic", zorder=8,
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor=color, linewidth=0.7, alpha=0.92))


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
INGREDIENT_DETAILS = {
    "アレグラFX": "(2錠中)フェキソフェナジン120mg",
    "コリホグス": "(2錠中)クロルゾキサゾン300mg/エテンザミド300mg/カフェイン水和物50mg",
    "トラベルミンR": "(1錠中)ジフェニドール16.6mg/スコポラミン0.16mg/無水カフェイン30mg/ピリドキシン5mg",
    "ナロン錠": "(2錠中)アセトアミノフェン265mg/エテンザミド300mg/ブロモバレリル尿素200mg/無水カフェイン50mg",
    "新コンタック鼻炎Z": "(1錠中)セチリジン10mg",
    "新ルルAゴールドDXα": "(9錠中)クレマスチン/ベラドンナ総アルカロイド/ブロムヘキシン/トラネキサム酸/アセトアミノフェン/dl-メチルエフェドリン/デキストロメトルファン/無水カフェイン",
    "葛根湯エキス錠S「コタロー」": "(12錠中)葛根湯エキス2.2g(カッコン/マオウ/タイソウ/ケイヒ/シャクヤク/カンゾウ/ショウキョウ)",
}
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
        status_text, status_color = "この商品名は【該当】", INK
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
                            "status_color": status_color, "note": final_note,
                            "ingr_detail": INGREDIENT_DETAILS.get(product, "")})
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

# --- 確認順ガイド（解釈層）：実務での確認の流れを、タイトル左の余白に1行で先に示す ---
ax.text(0.5, current_y - 0.35, "確認順：①成分判別→②年齢確認→③包装確認→④レジ確認",
        fontsize=4.0, fontweight="bold", fontstyle="italic", ha="left", va="center", color=BLUE)

# --- 使い方・販売可否（①を年齢規制＝この表の根幹に。ルール未経験者でもこの1枚で可否判断できるよう最上部に配置） ---
current_y -= 1.55
ax.hlines(current_y + 0.85, 0, LOGICAL_W, colors=INK, linewidth=1.2)
current_y -= 0.15
ax.text(COL_NAME_X, current_y, "18歳未満:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=INK)
ax.text(COL_NAME_X + 12.0, current_y,
        "小容量1個のみ販売可（氏名・年齢確認＋他店購入状況確認が必須）。大容量・複数個(種類違いの対象薬も合算)は家族用でも理由問わず一律禁止（販売不可）",
        fontsize=6.3, ha="left", va="center", color="#333333", fontweight="bold")
current_y -= 1.55
ax.text(COL_NAME_X, current_y, "18歳以上:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=INK)
ax.text(COL_NAME_X + 12.0, current_y,
        "小容量は通常販売可（他店購入状況確認は必須）。大容量・複数個の購入は理由確認が必須（正当な理由がなければ販売不可）",
        fontsize=6.6, ha="left", va="center", color="#333333")
current_y -= 1.55
ax.text(COL_NAME_X, current_y, "② 年齢確認:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=INK)
ax.text(COL_NAME_X + 12.0, current_y,
        "見た目で18歳以上と判断できない場合、学生証・健康保険証・マイナンバーカード・運転免許証等の身分証で氏名・年齢を確認",
        fontsize=6.3, ha="left", va="center", color="#333333")
current_y -= 1.55
ax.text(COL_NAME_X, current_y, "③ 包装制限の確認:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=INK)
ax.text(COL_NAME_X + 12.0, current_y, "下表で商品名を検索し「小包装/大包装」どちらの区分か確認（", fontsize=6.6, ha="left", va="center", color="#333333")
ax.text(COL_NAME_X + 38.1, current_y, "×7", fontsize=7.2, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 40.1, current_y, "＝かぜ薬・解熱鎮痛薬・鼻炎用内服薬/", fontsize=6.6, ha="left", va="center", color="#333333")
ax.text(COL_NAME_X + 56.8, current_y, "×5", fontsize=7.2, fontweight="bold", ha="left", va="center", color=ORANGE)
ax.text(COL_NAME_X + 58.8, current_y, "＝それ以外）", fontsize=6.6, ha="left", va="center", color="#333333")
current_y -= 1.35
ax.text(COL_NAME_X + 12.0, current_y,
        "※×7区分は、風邪の諸症状や長引く頭痛・鼻炎など症状が1週間程度続くことが臨床上多いための設定です",
        fontsize=5.6, ha="left", va="center", color=LGRAY)
ax.text(COL_NAME_X + 53.0, current_y, "表にない商品は、右下のQRからご確認いただけます", fontsize=5.6, ha="left", va="center", color="#888888")
current_y -= 1.45
ax.text(COL_NAME_X, current_y, "よくある質問:", fontsize=6.6, fontweight="bold", ha="left", va="center", color=INK)
ax.text(COL_NAME_X + 11.0, current_y,
        "対象薬を種類違いで1個ずつ購入→複数個扱いで販売不可/身分証の提示が難しい→年齢・氏名を確認できる方法がないか丁寧に確認",
        fontsize=6.0, ha="left", va="center", color="#333333")
current_y -= 1.5
ax.hlines(current_y, 0, LOGICAL_W, colors=INK, linewidth=1.2)
current_y -= 0.35

# --- 計算ドリル（実務でよく使う判別系を、本体テーブルの直前に集約。太枠で目立たせる） ---
DRILL_FS, DRILL_LH = 7.6, 1.75
drill_top = current_y + 1.0
current_y -= 1.75
ax.text(COL_NAME_X + 1.0, current_y, "計算ドリル", fontsize=8.3, fontweight="bold", ha="left", va="center", color=INK)
ax.text(COL_NAME_X + 15.0, current_y, "（下表を見ずに、ご自身で計算してみましょう）", fontsize=5.4, fontstyle="italic",
        ha="left", va="center", color=LGRAY)
current_y -= DRILL_LH
ax.text(COL_NAME_X + 1.0, current_y, "①分類：", fontsize=DRILL_FS, fontweight="bold", ha="left", va="center", color="#333333")
ax.text(COL_NAME_X + 9.5, current_y, "かぜ薬・解熱鎮痛薬・鼻炎用内服薬", fontsize=DRILL_FS - 0.4, ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 32.5, current_y, "＝", fontsize=DRILL_FS - 0.4, ha="left", va="center", color="#333333")
ax.text(COL_NAME_X + 34.3, current_y, "×7", fontsize=DRILL_FS, fontweight="bold", ha="left", va="center", color=BLUE)
ax.text(COL_NAME_X + 38.3, current_y, "／それ以外＝", fontsize=DRILL_FS - 0.4, ha="left", va="center", color="#333333")
ax.text(COL_NAME_X + 51.8, current_y, "×5", fontsize=DRILL_FS, fontweight="bold", ha="left", va="center", color=ORANGE)
ax.text(COL_NAME_X + 55.8, current_y, "　②1日量(15歳以上基準)：", fontsize=DRILL_FS - 0.4, ha="left", va="center", color="#333333")
ax.text(COL_NAME_X + 78.0, current_y, "〇", fontsize=DRILL_FS + 0.6, fontweight="bold", ha="left", va="center", color=INK)
current_y -= DRILL_LH
ax.text(COL_NAME_X + 1.0, current_y, "③計算：", fontsize=DRILL_FS, fontweight="bold", ha="left", va="center", color="#333333")
ax.text(COL_NAME_X + 9.5, current_y, "包装数量", fontsize=DRILL_FS - 0.4, ha="left", va="center", color="#333333")
ax.text(COL_NAME_X + 16.9, current_y, "〇", fontsize=DRILL_FS + 0.6, fontweight="bold", ha="left", va="center", color=INK)
ax.text(COL_NAME_X + 20.0, current_y, "÷1日量", fontsize=DRILL_FS - 0.4, ha="left", va="center", color="#333333")
ax.text(COL_NAME_X + 26.3, current_y, "〇", fontsize=DRILL_FS + 0.6, fontweight="bold", ha="left", va="center", color=INK)
ax.text(COL_NAME_X + 29.4, current_y, "＝消費日数", fontsize=DRILL_FS - 0.4, ha="left", va="center", color="#333333")
ax.text(COL_NAME_X + 37.9, current_y, "□", fontsize=DRILL_FS + 0.6, fontweight="bold", ha="left", va="center", color=INK)
ax.text(COL_NAME_X + 41.5, current_y, "日", fontsize=DRILL_FS - 0.4, ha="left", va="center", color="#333333")
current_y -= DRILL_LH
ax.text(COL_NAME_X + 1.0, current_y, "④判定：", fontsize=DRILL_FS, fontweight="bold", ha="left", va="center", color="#333333")
ax.text(COL_NAME_X + 9.5, current_y, "消費日数が①の基準日数(7日/5日)以下なら", fontsize=DRILL_FS - 0.4, ha="left", va="center", color="#333333")
ax.text(COL_NAME_X + 44.0, current_y, "【小容量】", fontsize=DRILL_FS, fontweight="bold", ha="left", va="center", color=INK)
ax.text(COL_NAME_X + 52.5, current_y, "・超えたら", fontsize=DRILL_FS - 0.4, ha="left", va="center", color="#333333")
ax.text(COL_NAME_X + 62.0, current_y, "【大容量】", fontsize=DRILL_FS, fontweight="bold", ha="left", va="center", color=INK)
current_y -= 1.05
ax.add_patch(patches.FancyBboxPatch((COL_NAME_X - 1.0, current_y), LOGICAL_W - 2 * (COL_NAME_X - 1.0), drill_top - current_y,
                                     boxstyle="round,pad=0.15", linewidth=1.6, edgecolor=INK, facecolor="none", zorder=6))
current_y -= 0.55
ax.text(COL_NAME_X, current_y, "① 成分判別:", fontsize=7.07, fontweight="bold", ha="left", va="center", color=INK)
marker(ax, COL_NAME_X + 9.0, current_y, RED, "circle", 0.42)
ax.text(COL_NAME_X + 9.9, current_y, "対象(指定8成分)＝", fontsize=5.9, ha="left", va="center", color=GRAY)
ax.text(COL_NAME_X + 17.3, current_y,
        "エフェドリン/メチルエフェドリン/プソイドエフェドリン/コデイン/ジヒドロコデイン/デキストロメトルファン/ジフェンヒドラミン/ブロモバレリル尿素",
        fontsize=5.9, fontweight="bold", ha="left", va="center", color=INK)
current_y -= 1.4
marker(ax, COL_NAME_X + 9.0, current_y, GREEN, "circle", 0.42)
ax.text(COL_NAME_X + 9.9, current_y,
        "対象外(紛らわしい)＝生薬マオウ/無水カフェイン/プロメタジン等の他の抗ヒス/アリルイソプロピルアセチル尿素",
        fontsize=5.9, ha="left", va="center", color=GRAY)
current_y -= 1.4
marker(ax, COL_NAME_X + 9.0, current_y, GREEN, "circle", 0.42)
ax.text(COL_NAME_X + 9.9, current_y,
        "対象外(剤形)＝トローチ・のど飴は「口腔内用剤」のため、指定成分を含んでいても対象外（軟膏等の外用剤と同様の扱い）",
        fontsize=5.9, ha="left", va="center", color=GRAY)
current_y -= 1.45
draw_eye_guide(ax, COL_NAME_X + 9.9, current_y,
               "↑順番が前後しますが、①はここです（商品が指定濫用対象かの確認）", color=BLUE, fontsize=5.9)
current_y -= 1.45
WATERMARK_GRAY = "#a8a8a8"  # alpha合成は印刷時に消えることがあるため、不透明な淡いグレー+斜体+小フォントで「参考情報」を表現
ax.text(COL_NAME_X, current_y, "ブランド速断:", fontsize=6.0, fontweight="bold", fontstyle="italic",
        ha="left", va="center", color=WATERMARK_GRAY)
ax.text(COL_NAME_X + 9.0, current_y,
        "外用薬・のどスプレー等は全て対象外。原則対象:ルル・パブロン(50除く)・ベンザブロック｜対象外:セデス・ノーシン・バファリン・イブ"
        "　※正式ルールではなく参考の目安",
        fontsize=5.5, fontstyle="italic", ha="left", va="center", color=WATERMARK_GRAY)
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

# --- 虫眼鏡フォーカス（解釈層）：小/大の枠が本当に照合すべき箇所であることを、
#     本文中の該当見出しを直接囲む枠で示す。説明は下の視線誘導へ続く ---
ax.add_patch(patches.FancyBboxPatch((COL_SMALL_X - 4.2, current_y - 1.15), COL_LARGE_X - COL_SMALL_X + 8.4, 2.3,
                                     boxstyle="round,pad=0.15", linewidth=1.1, edgecolor=BLUE,
                                     facecolor="none", linestyle=(0, (2, 1.5)), zorder=5))

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

# --- 視線誘導（解釈層）：小/大の枠は②③のルールと合わせて確認する運用上のポイントを一言添える ---
current_y -= 1.45
draw_eye_guide(ax, COL_NAME_X, current_y,
               "小/大の枠は②③のルールと合わせて確認を", color=BLUE, fontsize=6.2)
current_y -= 1.45
draw_eye_guide(ax, COL_NAME_X, current_y,
               "新しめの包装は「要確認」の「要」に囲みがあるかも目安に(旧包装は記載がない場合も)",
               color=BLUE, fontsize=5.8)

current_y -= 1.25
ax.hlines(current_y, 0, LOGICAL_W, linewidth=1.6)
current_y -= 1.6

main_rows = len(mart)
row_height = 2.05

# --- レジ確認フロー（本体テーブル右の空きスペースに縦長ミニフローチャート） ---
FLOW_HALF_W = 7.0
flow_nodes = [
    (["18歳未満の疑い", "→身分証等で氏名・", "年齢を確認"], INK, "#f2f2f2", 1.3),
    (["小容量1個のみ", "購入？"], INK, "#f2f2f2", 1.3),
    (["【いいえ】大容量/複数個", "→18歳未満は一律禁止", "18歳以上は理由を確認"], INK, "#e2e2e2", 2.0),
    (["【はい】小容量1個", "→18歳未満は氏名+周辺状況確認", "18歳以上は周辺状況確認"], INK, "#f2f2f2", 1.3),
    (["条件を満たせば", "販売可"], INK, "#e8e8e8", 1.6),
]
flow_top = 111.5
flow_bottom = 64.5
n = len(flow_nodes)
flow_gap = (flow_top - flow_bottom) / (n - 1)
flow_box_h = flow_gap - 1.9
prev_y = None
for idx, (lines, edge_color, fill_color, edge_w) in enumerate(flow_nodes):
    yc = flow_top - idx * flow_gap
    box = patches.FancyBboxPatch((FLOW_X - FLOW_HALF_W, yc - flow_box_h / 2), FLOW_HALF_W * 2, flow_box_h,
                                  boxstyle="round,pad=0.3", linewidth=edge_w, edgecolor=edge_color,
                                  facecolor=fill_color, zorder=3)
    ax.add_patch(box)
    n_lines = len(lines)
    line_h = 1.55
    start_y = yc + (n_lines - 1) * line_h / 2
    is_warning = edge_w > 1.5
    for li, line in enumerate(lines):
        ax.text(FLOW_X, start_y - li * line_h, line, fontsize=5.9, fontweight="bold" if is_warning else "normal",
                ha="center", va="center", color="#222222" if is_warning else "#333333")
    if prev_y is not None:
        ax.annotate("", xy=(FLOW_X, yc + flow_box_h / 2 + 0.2), xytext=(FLOW_X, prev_y - flow_box_h / 2 - 0.2),
                    arrowprops=dict(arrowstyle="-|>", color="#999999", lw=1.3))
    prev_y = yc

for i, row in mart.iterrows():
    if i % 2 == 0:
        ax.add_patch(patches.Rectangle((0, current_y - row_height * 0.785), LOGICAL_W, row_height, facecolor="#f5f5f5", edgecolor="none", zorder=0))

    name_len = len(row["product"])
    name_fontsize = 8.6 if name_len <= 8 else (7.8 if name_len <= 12 else 7.0)
    name_text = row["product"] + ("※" if row["is_caplet"] else "")
    ax.text(COL_NAME_X, current_y, name_text, fontsize=name_fontsize, fontweight="bold", ha="left", va="center")

    if row["ingredients"]:
        clean_ingr = re.sub(r'(塩酸塩|リン酸塩|硫酸塩|臭化水素酸塩|マレイン酸塩|酒石酸塩|フマル酸塩)', '', row["ingredients"])
        if len(clean_ingr) > 26:
            clean_ingr = clean_ingr[:26] + "…"
        ax.text(COL_INGR_X, current_y, clean_ingr, fontsize=5.4, ha="left", va="center", color="#666666")
    else:
        ax.text(COL_INGR_X, current_y, "-", fontsize=7.2, ha="left", va="center", color="#aaaaaa")

    ax.text(COL_DOSE_X, current_y, row["daily"], fontsize=9.4, ha="center", va="center")

    mult_color = "#1565c0" if row["limit"] == 7 else "#e65100"
    ax.text(COL_MULT_X, current_y, f"×{row['limit']}", fontsize=7.8, ha="center", va="center",
            color=mult_color, fontweight="bold")

    if row["small"] != "-":
        ax.text(COL_SMALL_X, current_y, row["small"], fontsize=8.1, fontweight="bold", ha="center", va="center")

    ax.vlines(COL_BOUND_X, current_y - 0.78, current_y + 0.78, color="#bbbbbb", linewidth=1.0, zorder=1)
    ax.text(COL_BOUND_X, current_y, row["boundary"], fontsize=6.9, ha="center", va="center", color=GRAY, zorder=2)

    if row["large"] != "-":
        ax.text(COL_LARGE_X, current_y, row["large"], fontsize=8.1, fontweight="bold", ha="center", va="center", color="#444444")

    current_y -= row_height

current_y -= 1.35
ax.text(COL_NAME_X, current_y,
        "※＝カプレット表記（ベンザブロック◯◯/末尾「錠」なし）。1日成分量は「◯◯錠」と同一ですが服用粒数が異なります。",
        fontsize=6.1, ha="left", va="center", color="#888888")

current_y -= 0.55
zone_top = current_y + 0.55
ax.add_patch(patches.Rectangle((0, -3), LOGICAL_W, zone_top + 3, facecolor="#eaecef", edgecolor="none", zorder=-2))
current_y -= 0.55

# --- 判定注意・参考（マトリックス） ---
ref_rows = len(reference) if not reference.empty else 0
if ref_rows > 0:
    current_y -= 1.03
    ax.hlines(current_y, 0, LOGICAL_W, colors="black", linewidth=1.1)
    current_y -= 1.84

    ax.text(COL_NAME_X, current_y, "判定注意・参考", fontsize=10.37, fontweight="bold", ha="left", va="center", color=INK)
    ax.text(COL_NAME_X + 10.5, current_y, "※該当はまれです", fontsize=5.0, fontstyle="italic",
            ha="left", va="center", color=LGRAY)
    ax.text(28.0, current_y, "指定濫用判定", fontsize=8.54, fontweight="bold", ha="center", va="center")
    ax.text(41.0, current_y, "同ブランド内比較・注釈（「対比:」＝取り違え注意ポイント）", fontsize=8.54, fontweight="bold", ha="left", va="center")

    current_y -= 1.4
    ax.hlines(current_y, 0, LOGICAL_W, colors="#cccccc", linewidth=0.8)
    current_y -= 2.0

    ref_row_h = 3.15
    for j, (_, row) in enumerate(reference.iterrows()):
        if j % 2 == 0:
            ax.add_patch(patches.Rectangle((0, current_y - 1.55), LOGICAL_W, ref_row_h, facecolor="#fafafa", edgecolor="none"))
        ax.text(COL_NAME_X, current_y, row["product"], fontsize=8.42, fontweight="bold", ha="left", va="center")
        ax.text(28.0, current_y, row["status_text"], fontsize=8.42, fontweight="bold", ha="center", va="center", color=row["status_color"])
        is_taichi = row["note"].startswith("対比")
        ax.text(41.0, current_y, row["note"], fontsize=7.34, fontweight="bold" if is_taichi else "normal",
                ha="left", va="center", color=INK if is_taichi else GRAY)
        if row["ingr_detail"]:
            detail_text = row["ingr_detail"]
            if len(detail_text) > 34:
                detail_text = detail_text[:34] + "…"
            ax.text(COL_NAME_X, current_y - 1.25, detail_text, fontsize=5.1, ha="left", va="center", color="#999999")
        current_y -= ref_row_h

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
ax.text(QR_X, qr1_y, "参考：商品検索", fontsize=6.8, ha="center", va="top", color=INK, fontweight="bold")
qr1_y -= 1.05
ax.text(QR_X, qr1_y, "(表にない商品はこちらから)", fontsize=5.0, ha="center", va="top", color="#999999")
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
ax.text(COL_NAME_X, y, "",
        fontsize=9.15, fontweight="bold", ha="left", va="center")
y -= 1.84

# G. 必須質問（厚労省チェック項目に準拠。該当時は裏面の「状況別対応のポイント」を参照）
y -= 0.5
box_top = y + 0.7
# box_hは内容量から決まる固定値（内容が伸びてbox_topが下がっても、
# 下端が5.9固定だと後半の項目がはみ出すため、内容基準に変更）
box_h = 19.9
ax.add_patch(patches.FancyBboxPatch((COL_NAME_X - 0.5, box_top - box_h), LOGICAL_W - 2 * (COL_NAME_X - 0.5), box_h,
                                     boxstyle="round,pad=0.2", linewidth=1.4, edgecolor=INK, facecolor="#f7f7f7", zorder=2))
ax.add_patch(patches.FancyBboxPatch((COL_NAME_X - 0.5, box_top - 1.9), LOGICAL_W - 2 * (COL_NAME_X - 0.5), 1.9,
                                     boxstyle="round,pad=0.2", linewidth=0, facecolor=INK, zorder=2))
ax.text(LOGICAL_W / 2, box_top - 0.95, "④ レジでの確認事項　※該当する場合は裏面「状況別対応のポイント」を参照",
        fontsize=7.6, fontweight="bold", ha="center", va="center", color="white", zorder=3)

qy = box_top - 3.3
ax.text(COL_NAME_X + 1.0, qy, "＋【使用者】今回のお薬は、どなた（ご本人様／12歳未満の小児等）が使われますか？",
        fontsize=7.1, fontweight="bold", ha="left", va="center", color="#222222", zorder=3)
qy -= 1.6
ax.text(COL_NAME_X + 1.0, qy, "＋ いつから、どの程度の症状ですか？（適正な使用期間の確認、長引く場合は受診勧奨を判断します）",
        fontsize=7.1, ha="left", va="center", color=GRAY, zorder=3)
qy -= 1.6
ax.text(COL_NAME_X + 1.0, qy, "＋ すでに受診・服薬を開始していますか？（重複投与や飲み合わせ確認のため）",
        fontsize=7.1, ha="left", va="center", color=GRAY, zorder=3)
qy -= 1.75
ax.text(COL_NAME_X + 1.0, qy, "①【年齢・氏名】18歳未満ですか？（※18歳未満への大容量・複数個は理由問わず一律販売不可。小容量1個のみ可。氏名・年齢の記録が必須）",
        fontsize=7.3, fontweight="bold", ha="left", va="center", color="#222222", zorder=3)
qy -= 1.85
ax.text(COL_NAME_X + 1.0, qy, "②【重複】他店や他のレジで同じお薬（風邪薬、咳止め等）のご購入はありませんか？（譲り受けも含みます）",
        fontsize=7.3, fontweight="bold", ha="left", va="center", color="#222222", zorder=3)
qy -= 1.85
ax.text(COL_NAME_X + 1.0, qy, "以下は、お薬の安全な選択に関わります。", fontsize=6.2, fontstyle="italic",
        ha="left", va="center", color=LGRAY, zorder=3)
qy -= 1.55
ax.text(COL_NAME_X + 1.0, qy, "③【体質】アレルギー歴（アスピリン喘息等）や、喘息、不整脈、緑内障、前立腺肥大の持病はありますか？",
        fontsize=7.3, fontweight="bold", ha="left", va="center", color="#222222", zorder=3)
qy -= 1.85
ax.text(COL_NAME_X + 1.0, qy, "④【併用】現在、病院で処方されたお薬や、他のお薬を飲まれていますか？（SSRI等との重複防止）",
        fontsize=7.3, fontweight="bold", ha="left", va="center", color="#222222", zorder=3)
qy -= 1.85
ax.text(COL_NAME_X + 1.0, qy, "⑤【妊婦】妊娠中、または授乳中ではありませんか？（妊娠後期のNSAIDs禁忌、授乳中のコデイン避止）",
        fontsize=7.3, fontweight="bold", ha="left", va="center", color="#222222", zorder=3)
qy -= 1.75
ax.text(COL_NAME_X + 1.0, qy, "＋【大容量・複数個（成人）】ご事情をお伺いできますか？（※正当な使用理由が確認できない場合は販売不可）",
        fontsize=7.1, ha="left", va="center", color=GRAY, zorder=3)

# === 【追加】必須質問ボックスの下辺から0.9下がった位置に y を再設定 ===
y = box_top - box_h - 0.9

y -= 0.25  # y = 4.55 (免責事項の描画位置)
ax.text(COL_NAME_X, y, "免責: 過去に用法用量超過の自己判断服用で重篤な健康被害が生じた事例を踏まえた確認です。意図的な過量服薬は保証・救済制度の対象外です。", fontsize=6.1, ha="left", va="center", color=LGRAY)
y -= 0.85  # y = 3.70 (準拠資料の描画位置)
ax.text(COL_NAME_X, y,
        "準拠: 厚生労働省 局長通知「指定濫用防止医薬品の指定について」・厚生労働大臣が定める数量（告示）/JSMI「指定濫用防止医薬品の販売制度について」/兵庫県 薬務課 制度改正資料",
        fontsize=4.8, ha="left", va="center", color="#aaaaaa")

plt.savefig(OUTPUT_PNG, dpi=300)
plt.close()

print("==========================================")
print("v12【表面】A4 早見表生成完了")
print(f"出力ファイル: {OUTPUT_PNG}")
print(f"最終y座標(0付近が理想): {y:.2f}")
print("==========================================")
