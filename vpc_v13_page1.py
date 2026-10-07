import pandas as pd
import re
import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import japanize_matplotlib
from print_style import MIN_FS, check_min_font

PACKAGE_CSV = "package_verification.csv"
OUTPUT_PNG = "atomic_card_table_v13_page1.png"
OUTPUT_PDF = "atomic_card_table_v13_page1.pdf"
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


def reorder_ingredients(ingr_str):
    """対象成分の列は、依存性の観点で最も注意すべきジヒドロコデインを常に一番左に表示する。"""
    tokens = [t.strip() for t in ingr_str.split(",") if t.strip()]
    tokens.sort(key=lambda t: 0 if "ジヒドロコデイン" in t else 1)
    return ", ".join(tokens)


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
    """虫眼鏡アイコン：レンズ(円)＋斜めの持ち手。持ち手の先端座標を返す（そこから説明文を続ける）。
    解釈層であることが一目でわかるよう、やや大きめ・太めに描く。"""
    import math
    rad = math.radians(angle_deg)
    dx, dy = math.cos(rad), math.sin(rad)
    edge_x, edge_y = x + r * dx, y + r * dy
    tip_x, tip_y = x + (r + handle_len) * dx, y + (r + handle_len) * dy
    ax.add_patch(patches.Circle((x, y), r, facecolor="#fff5f5" if color == RED else "#f3f8fd",
                                 edgecolor=color, linewidth=1.5, zorder=8))
    ax.plot([edge_x, tip_x], [edge_y, tip_y], color=color, linewidth=2.1, solid_capstyle="round", zorder=8)
    return tip_x, tip_y


def draw_eye_guide(ax, x, y, text, color=RED, fontsize=5.0, ha="left"):
    """短い道案内（解釈層）。虫眼鏡アイコン＋断定しすぎない一言を、白抜き吹き出しで軽く強調する。"""
    icon_r = min(fontsize * 0.17, 0.85)  # 文字を大きくしても虫眼鏡が上の行に食い込まないよう上限を設ける
    icon_cx = x + icon_r * 1.3 if ha == "left" else x - icon_r * 1.3
    tip_x, _ = draw_magnifier_icon(ax, icon_cx, y + icon_r * 0.3, r=icon_r, handle_len=icon_r * 1.6,
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
mart = pd.DataFrame(processed)

# --- ブランドファミリーのグループ化（アルファベット順では離れてしまう関連商品を隣接表示） ---
GROUP_ORDER_OVERRIDE = {
    "改源": ("改源", 0),
    "新カイゲンせき止め液W": ("改源", 1),
    "ベンザブロックIP": ("ベンザブロックIP", 0),
    "ベンザブロックIP錠": ("ベンザブロックIP", 1),
    "ベンザブロックIPプレミアム": ("ベンザブロックIP", 2),
}

# 表示名だけを差し替える（CAPLET_PRODUCTS等のキーはCSV上の商品名のまま保つ）
DISPLAY_NAME_OVERRIDE = {
    "ベンザブロックIPプレミアム": "ベンザブロックIPプレミアム(2025年廃版)",
}


def merge_products(mart_df, names, new_name):
    """同一成分・同一用量帯の兄弟品を、表では1行に統合して省スペース化する。"""
    rows = mart_df[mart_df["product"].isin(names)]
    if len(rows) < 2:
        return mart_df

    def merge_field(col):
        seen = []
        for v in rows[col]:
            if v != "-":
                for token in v.split(" "):
                    if token not in seen:
                        seen.append(token)
        seen.sort(key=lambda t: extract_amount_unit(t)[0])
        return " ".join(seen) if seen else "-"

    merged = {
        "product": new_name, "daily": rows.iloc[0]["daily"], "limit": rows.iloc[0]["limit"],
        "boundary": rows.iloc[0]["boundary"], "small": merge_field("small"), "large": merge_field("large"),
        "ingredients": rows.iloc[0]["ingredients"], "is_caplet": rows.iloc[0]["is_caplet"],
    }
    mart_df = mart_df[~mart_df["product"].isin(names)]
    return pd.concat([mart_df, pd.DataFrame([merged])], ignore_index=True)


mart = merge_products(mart, ["レスタミンコーワ糖衣錠", "レスタミンUコーワ錠"], "レスタミンコーワ糖衣錠/Uコーワ錠")
mart.loc[mart["product"] == "レスタミンコーワ糖衣錠/Uコーワ錠", "ingredients"] = "ジフェンヒドラミン(Uはビタミン等配合)"
mart["sort_key"] = mart["product"].map(lambda p: GROUP_ORDER_OVERRIDE.get(p, (p, 0)))
mart = mart.sort_values("sort_key").drop(columns=["sort_key"]).reset_index(drop=True)

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
    "ナロン錠": "ナロン系（確認済）: 該当＝ナロン錠(無印)・ナロン顆粒・ナロンエースT／対象外＝ナロンm・エースプレミアム。",
    "新コンタック鼻炎Z": "対比: 鼻炎Zのみ対象外(唯一制限成分なし)/600プラス・かぜ総合等は該当。※セチリジンは妊婦禁忌。",
    "新ルルAゴールドDXα": "対比: 同じ「ルル」でも、ルルのど飴(医薬部外品)は対象外。メディカルドロップ(医薬品)は成分で該当。",
    "葛根湯エキス錠S「コタロー」": "対比: 葛根湯・小青竜湯等の漢方製剤は対象外(マオウは化学成分外で規制対象外)。",
    "パイロンPL錠(無印)": "対比: PL錠・PL錠Pro・PL顆粒・PL顆粒Proは対象外/PL錠ゴールド・溶かしてのむかぜ薬は該当。",
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
fig.canvas.draw()
_renderer = fig.canvas.get_renderer()


def text_width(text, fontsize, weight="normal"):
    """論理座標での文字列の幅（並べて描く要素の位置計算用）。"""
    t = ax.text(0, -50, text, fontsize=fontsize, fontweight=weight)
    w = t.get_window_extent(renderer=_renderer).width / fig.bbox.width * LOGICAL_W
    t.remove()
    return w


def text_run(x, y, parts, **common):
    """色や太さの違う文字列を、実測した幅で左から順に並べて描く。描き終わりのx座標を返す。"""
    for text, kw in parts:
        opts = dict(common)
        opts.update(kw)
        ax.text(x, y, text, ha="left", va="center", **opts)
        x += text_width(text, opts["fontsize"], opts.get("fontweight", "normal"))
    return x


def split_two_lines(text, fontsize, max_w, sep):
    """1行に収まらない場合だけ、区切り文字で2行に分ける（文字を縮めずに収めるため）。"""
    if text_width(text, fontsize) <= max_w or sep not in text:
        return [text]
    tokens = text.split(sep)
    best = None
    for k in range(1, len(tokens)):
        a, b = sep.join(tokens[:k]), sep.join(tokens[k:])
        score = max(text_width(a, fontsize), text_width(b, fontsize))
        if best is None or score < best[0]:
            best = (score, [a.strip(), b.strip()])
    return best[1]

COL_NAME_X = 2.0
COL_INGR_X = 26.5
COL_DOSE_X = 49.0
COL_MULT_X = 55.0
COL_SMALL_X = 61.0
COL_BOUND_X = 71.0
COL_LARGE_X = 80.5
FLOW_X = 92.5

# --- タイトル ---
current_y = LOGICAL_H - 1.7
ax.text(LOGICAL_W / 2, current_y, "薬剤別 包装区分 早見表", fontsize=18.91, fontweight="bold", ha="center", va="center")
today_str = datetime.date.today().strftime("%Y/%m/%d")
ax.text(LOGICAL_W - 0.6, current_y + 0.75, f"作成日: {today_str}", fontsize=7.93, ha="right", va="center", color="#888888")
ax.text(LOGICAL_W - 0.6, current_y - 0.45, "※AIによる試作品/使用前に最新の添付文書等を確認",
        fontsize=MIN_FS, ha="right", va="center", color="#888888")

# --- 確認順ガイド（解釈層）：実務での確認の流れを、タイトル左の余白に先に示す ---
ax.text(0.6, current_y + 0.75, "確認順：①成分判別→②年齢確認", fontsize=MIN_FS, fontweight="bold",
        fontstyle="italic", ha="left", va="center", color=BLUE)
ax.text(0.6, current_y - 0.45, "　　　→③包装確認→④レジ確認", fontsize=MIN_FS, fontweight="bold",
        fontstyle="italic", ha="left", va="center", color=BLUE)

# --- 法解釈・実務鉄則（最重要の注意事項として最上部に明記） ---
current_y -= 1.95
rule_box_h = 4.0
ax.add_patch(patches.FancyBboxPatch((COL_NAME_X - 1.0, current_y - rule_box_h + 0.75),
                                     LOGICAL_W - 2 * (COL_NAME_X - 1.0), rule_box_h,
                                     boxstyle="round,pad=0.12", linewidth=1.4, edgecolor=RED,
                                     facecolor="#fff5f5", zorder=6))
ax.text(COL_NAME_X + 0.3, current_y,
        "【法解釈・実務鉄則】小容量1個の販売時であっても、18歳未満には「氏名・年齢の確認」、成人には「他店での直近購入状況の確認」が法令上必須となります。",
        fontsize=MIN_FS, fontweight="bold", ha="left", va="center", color=DARKRED, zorder=7)
current_y -= 1.25
ax.text(COL_NAME_X + 0.3, current_y,
        "※1日量は「適宜増減」や小児用量に関わらず、成人の1日最大服用量で計算。「就寝前にも服用可」「頓服可」で回数が増える場合は、その分も足した最大量で計算します。",
        fontsize=MIN_FS, ha="left", va="center", color=DARKRED, zorder=7)
current_y -= 1.25
text_run(COL_NAME_X + 0.3, current_y, [
    ("★前提：新しい包装なら、まずパッケージの「要」の囲み（大容量の目印）を見る。", {"fontweight": "bold", "color": INK}),
    ("囲みのない旧包装の判断や、お客様からの質問対応にこの表を使います。", {"color": "#333333"}),
], fontsize=MIN_FS, zorder=7)
current_y -= 1.15

# --- ① 成分判別（本当にこの表の対象品かどうかの一番最初の確認として最上部に配置） ---
current_y -= 1.55
ax.text(COL_NAME_X, current_y, "① 成分判別:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=INK)
ING_X = COL_NAME_X + 9.6
ING_LH = 1.3
ing_lines = [
    (RED, [("対象(指定8成分)＝", {"color": GRAY}),
           ("エフェドリン類3種：エフェドリン/メチルエフェドリン/プソイドエフェドリン", {"fontweight": "bold", "color": INK})]),
    (None, [("　　　　　　　　 ＋", {"color": GRAY}),
            ("その他5種：コデイン/ジヒドロコデイン/デキストロメトルファン(DXM)/ジフェンヒドラミン/ブロモバレリル尿素",
             {"fontweight": "bold", "color": INK})]),
    (GREEN, [("対象外(紛らわしい)＝", {"color": GRAY}),
             ("生薬マオウ（エフェドリンを含むが生薬主体の製剤は通知で除外）／無水カフェイン／プロメタジン等の他の抗ヒス／"
              "アリルイソプロピルアセチル尿素（8成分外）", {"color": GRAY})]),
    (GREEN, [("対象外(外用剤)＝", {"color": GRAY}),
             ("トローチ・舌下錠などの口腔用錠剤、含嗽剤、口腔用スプレー、軟膏、目薬等（通知で外用剤と明記。8成分はすべて外用剤を除く）",
              {"color": GRAY})]),
    (RED, [("要注意(のど飴)＝", {"color": GRAY}),
           ("医薬品のドロップはトローチと違い内服扱い。成分で判定（例：ルルメディカルドロップ＝メチルエフェドリン配合）",
            {"fontweight": "bold", "color": INK}),
           ("（医薬部外品・食品ののど飴は対象外）", {"color": GRAY})]),
]
for mcolor, parts in ing_lines:
    if mcolor:
        marker(ax, ING_X - 0.75, current_y, mcolor, "circle", 0.38)
    text_run(ING_X, current_y, parts, fontsize=MIN_FS)
    current_y -= ING_LH
current_y -= 0.15

# --- 使い方・販売可否（②③を年齢・包装規制＝この表の根幹に。ルール未経験者でもこの1枚で可否判断できるよう上部に配置） ---
ROW_LH = 1.38
BODY_X = COL_NAME_X + 12.0
ax.hlines(current_y + 0.75, 0, LOGICAL_W, colors=INK, linewidth=1.2)
current_y -= 0.15
ax.text(COL_NAME_X, current_y, "18歳未満:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=INK)
ax.text(BODY_X, current_y,
        "小容量1個のみ販売可。大容量・複数個(種類違いの対象薬も合算)は家族用でも理由問わず一律禁止（販売不可）",
        fontsize=MIN_FS, ha="left", va="center", color="#333333", fontweight="bold")
current_y -= ROW_LH
ax.text(COL_NAME_X, current_y, "18歳以上:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=INK)
ax.text(BODY_X, current_y,
        "小容量は通常販売可。成人であれば購入個数の制限はないが、大容量・複数個の購入は理由確認が必須（正当な理由がなければ販売不可）",
        fontsize=MIN_FS, ha="left", va="center", color="#333333")
current_y -= ROW_LH
ax.text(COL_NAME_X, current_y, "② 年齢確認:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=INK)
ax.text(BODY_X, current_y,
        "見た目で18歳以上と判断できない場合、学生証・健康保険証・マイナンバーカード・運転免許証等の身分証で氏名・年齢を確認",
        fontsize=MIN_FS, ha="left", va="center", color="#333333")
current_y -= ROW_LH * 0.95
ax.text(BODY_X, current_y,
        "※見た目の判断には個人差があります。確認漏れは店舗の法令上の遵守事項違反になりうるため、迷ったら確認する",
        fontsize=MIN_FS, ha="left", va="center", color=DARKRED)
current_y -= ROW_LH
ax.text(COL_NAME_X, current_y, "③ 包装制限の確認:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=INK)
text_run(BODY_X, current_y, [
    ("下表で商品名を検索し「小包装/大包装」どちらの区分か確認（", {}),
    ("×7", {"fontsize": 7.6, "fontweight": "bold", "color": BLUE}),
    ("＝かぜ薬・解熱鎮痛薬・鼻炎用内服薬／", {}),
    ("×5", {"fontsize": 7.6, "fontweight": "bold", "color": ORANGE}),
    ("＝それ以外）", {}),
], fontsize=MIN_FS, color="#333333")
current_y -= ROW_LH * 0.95
ax.text(BODY_X, current_y,
        "※×7区分は、風邪の諸症状や長引く頭痛・鼻炎など症状が1週間程度続くことが臨床上多いための設定です",
        fontsize=MIN_FS, ha="left", va="center", color=LGRAY)
current_y -= ROW_LH * 0.95
ax.text(BODY_X, current_y, "※表にない商品は、KEGG_OTC検索欄で成分・用量を見て、下の計算ドリルの手順で判定できます",
        fontsize=MIN_FS, ha="left", va="center", color=LGRAY)
current_y -= ROW_LH
ax.text(COL_NAME_X, current_y, "よくある質問:", fontsize=7.4, fontweight="bold", ha="left", va="center", color=INK)
ax.text(BODY_X, current_y,
        "対象薬を種類違いで1個ずつ購入→複数個扱いで販売不可/身分証の提示が難しい→年齢・氏名を確認できる方法がないか丁寧に確認",
        fontsize=MIN_FS, ha="left", va="center", color="#333333")
current_y -= 1.35
ax.hlines(current_y, 0, LOGICAL_W, colors=INK, linewidth=1.2)
current_y -= 0.35

# --- 計算ドリル（3つのステップカードを横に並べ、左から順に読めば判定できる形にする） ---
current_y -= 1.45
ax.text(COL_NAME_X, current_y, "計算ドリル", fontsize=8.6, fontweight="bold", ha="left", va="center", color=INK)
ax.text(COL_NAME_X + 8.6, current_y, "表にない商品も、この3ステップで小容量／大容量を判定できます", fontsize=MIN_FS,
        ha="left", va="center", color=LGRAY)
current_y -= 1.0
CARD_GAP = 1.6
CARD_W = (LOGICAL_W - 2 * COL_NAME_X - 2 * CARD_GAP) / 3
CARD_H = 5.6
CARD_FS = 8.0
card_top = current_y
DRILL_CARDS = [
    ("1", "基準日数を決める", [
        [("かぜ薬・解熱鎮痛薬・鼻炎用内服薬 → ", {}), ("×7（7日）", {"fontweight": "bold", "color": BLUE})],
        [("それ以外（せき止め・乗り物酔い薬等） → ", {}), ("×5（5日）", {"fontweight": "bold", "color": ORANGE})],
    ]),
    ("2", "消費日数を計算する", [
        [("包装数量 ÷ 1日量 ＝ 消費日数", {"fontweight": "bold", "fontsize": CARD_FS + 0.6})],
        [("1日量＝成人(15歳以上)の最大量（就寝前・頓服も足す）", {"fontsize": MIN_FS, "color": "#555555"})],
    ]),
    ("3", "基準日数と比べる", [
        [("消費日数 ≦ 基準日数 → ", {}), ("小容量", {"fontweight": "bold", "color": BLUE})],
        [("消費日数 ＞ 基準日数 → ", {}), ("大容量", {"fontweight": "bold", "color": ORANGE}),
         ("（同日数は小容量）", {"fontsize": MIN_FS, "color": "#555555"})],
    ]),
]
for ci, (num, title, lines) in enumerate(DRILL_CARDS):
    cx = COL_NAME_X + ci * (CARD_W + CARD_GAP)
    ax.add_patch(patches.FancyBboxPatch((cx, card_top - CARD_H), CARD_W, CARD_H, boxstyle="round,pad=0.2",
                                         linewidth=1.0, edgecolor="#bbbbbb", facecolor="#fafafa", zorder=5))
    ty = card_top - 1.0
    ax.add_patch(patches.Circle((cx + 1.0, ty), 0.75, facecolor=INK, edgecolor="none", zorder=6))
    ax.text(cx + 1.0, ty, num, fontsize=CARD_FS, fontweight="bold", ha="center", va="center", color="white", zorder=7)
    ax.text(cx + 2.2, ty, title, fontsize=CARD_FS + 0.4, fontweight="bold", ha="left", va="center", color=INK, zorder=7)
    ly = ty - 1.75
    for parts in lines:
        text_run(cx + 0.8, ly, parts, fontsize=CARD_FS, color="#222222", zorder=7)
        ly -= 1.45
    if ci < len(DRILL_CARDS) - 1:
        ax.annotate("", xy=(cx + CARD_W + CARD_GAP - 0.15, card_top - CARD_H / 2),
                    xytext=(cx + CARD_W + 0.15, card_top - CARD_H / 2),
                    arrowprops=dict(arrowstyle="-|>", color="#888888", lw=1.4), zorder=8)
current_y = card_top - CARD_H - 1.05
text_run(COL_NAME_X, current_y, [
    ("例）改源 26包：", {"fontweight": "bold", "color": INK}),
    ("かぜ薬 → ×7（7日）／ 26包 ÷ 3包 ＝ 8.7日 ＞ 7日 → ", {"color": "#333333"}),
    ("大容量", {"fontweight": "bold", "color": ORANGE}),
], fontsize=MIN_FS)
current_y -= 1.3
WATERMARK_GRAY = "#999999"  # alpha合成は印刷時に消えることがあるため、不透明なグレー+斜体で「参考情報」を表現（6pt印刷でも読める濃さ）
ax.text(COL_NAME_X, current_y, "ブランド速断:", fontsize=MIN_FS, fontweight="bold", fontstyle="italic",
        ha="left", va="center", color=WATERMARK_GRAY)
ax.text(COL_NAME_X + text_width("ブランド速断:", MIN_FS, "bold") + 0.6, current_y,
        "原則対象:ルル・パブロン(50除く)・ベンザブロック｜対象外:セデス・ノーシン・バファリン・イブ"
        "　※表の作成時に調べた範囲の目安。新発売品は反映されていないため、迷ったら成分で確認",
        fontsize=MIN_FS, fontstyle="italic", ha="left", va="center", color=WATERMARK_GRAY)
current_y -= 1.3
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

current_y -= 1.6
ax.text(COL_NAME_X, current_y, "小包装＝単品1個は18歳未満も可／大包装＝18歳未満へ不可",
        fontsize=MIN_FS, ha="left", va="center", color="#555555")
text_run(46.5, current_y, [("×7", {"fontweight": "bold", "color": BLUE}), ("＝かぜ薬等", {"color": "#555555"})],
         fontsize=MIN_FS)
current_y -= 1.15
ax.text(COL_NAME_X, current_y, "1日量＝成人(15歳以上)の1日最大服用量（18歳未満の購入者でも、常にこの量で計算）",
        fontsize=MIN_FS, ha="left", va="center", color="#555555")
text_run(46.5, current_y, [("×5", {"fontweight": "bold", "color": ORANGE}), ("＝それ以外", {"color": "#555555"})],
         fontsize=MIN_FS)

current_y -= 0.3
current_y -= 1.1
ax.hlines(current_y, 0, LOGICAL_W, linewidth=1.6)
current_y -= 1.6

main_rows = len(mart)
row_height = 1.95
ROW_H_TWO_LINES = 2.45  # 成分名が2行になる行だけ少し高くする
INGR_X_GAP = 0.7


def clean_ingredients(ingr):
    return re.sub(r'(塩酸塩|リン酸塩|硫酸塩|臭化水素酸塩|マレイン酸塩|酒石酸塩|フマル酸塩)', '', reorder_ingredients(ingr))


def ingr_max_w(daily):
    """成分名に使える幅＝1日量の文字の左端まで（1日量の文字幅は行ごとに違う）。"""
    return COL_DOSE_X - text_width(daily, 10.3) / 2 - INGR_X_GAP - COL_INGR_X


mart["ingr_lines"] = [split_two_lines(clean_ingredients(r["ingredients"]), MIN_FS, ingr_max_w(r["daily"]), ",")
                      if r["ingredients"] else [] for _, r in mart.iterrows()]
mart["row_h"] = [ROW_H_TWO_LINES if len(v) > 1 else row_height for v in mart["ingr_lines"]]
rows_top_y = current_y
rows_bottom_y = current_y - (mart["row_h"].sum() - mart["row_h"].iloc[-1] / 2 - mart["row_h"].iloc[0] / 2)

# --- レジ確認フロー（本体テーブル右の空きスペースに縦長ミニフローチャート） ---
#     表の1行目〜最終行の高さに合わせて配置する（上の計算ドリルと重ならないよう、位置は表から算出）
FLOW_HALF_W = 7.0
FLOW_FS = MIN_FS
flow_nodes = [
    (["18歳未満の疑い", "→身分証等で", "氏名・年齢を確認"], INK, "#f2f2f2", 1.3),
    (["小容量1個のみ", "の購入？"], INK, "#f2f2f2", 1.3),
    (["【いいえ】", "大容量/複数個", "18歳未満→一律禁止", "18歳以上→理由確認"], INK, "#e2e2e2", 2.0),
    (["【はい】小容量1個", "18歳未満→氏名＋", "周辺状況確認", "18歳以上→周辺状況確認"], INK, "#f2f2f2", 1.3),
    (["条件を満たせば", "販売可"], INK, "#e8e8e8", 1.6),
]
n = len(flow_nodes)
FLOW_ARROW_GAP = 1.9
flow_region_top = rows_top_y + 0.9
flow_region_bottom = rows_bottom_y - 0.9
flow_box_h = (flow_region_top - flow_region_bottom - (n - 1) * FLOW_ARROW_GAP) / n
flow_gap = flow_box_h + FLOW_ARROW_GAP
flow_top = flow_region_top - flow_box_h / 2
prev_y = None
for idx, (lines, edge_color, fill_color, edge_w) in enumerate(flow_nodes):
    yc = flow_top - idx * flow_gap
    box = patches.FancyBboxPatch((FLOW_X - FLOW_HALF_W, yc - flow_box_h / 2), FLOW_HALF_W * 2, flow_box_h,
                                  boxstyle="round,pad=0.3", linewidth=edge_w, edgecolor=edge_color,
                                  facecolor=fill_color, zorder=3)
    ax.add_patch(box)
    n_lines = len(lines)
    line_h = 1.3
    start_y = yc + (n_lines - 1) * line_h / 2
    is_warning = edge_w > 1.5
    for li, line in enumerate(lines):
        ax.text(FLOW_X, start_y - li * line_h, line, fontsize=FLOW_FS, fontweight="bold" if is_warning else "normal",
                ha="center", va="center", color="#222222" if is_warning else "#333333", zorder=4)
    if prev_y is not None:
        ax.annotate("", xy=(FLOW_X, yc + flow_box_h / 2 + 0.2), xytext=(FLOW_X, prev_y - flow_box_h / 2 - 0.2),
                    arrowprops=dict(arrowstyle="-|>", color="#999999", lw=1.3))
    prev_y = yc

# 1行に収まらない成分名・包装規格は、文字を縮めずに2行へ分ける（印刷6pt未満にしないため）
SMALL_MAX_W = 2 * min(COL_SMALL_X - (COL_MULT_X + 1.2), (COL_BOUND_X - 2.2) - COL_SMALL_X)
LARGE_MAX_W = 2 * min(COL_LARGE_X - (COL_BOUND_X + 2.4), (FLOW_X - FLOW_HALF_W - 0.5) - COL_LARGE_X)
TWO_LINE_OFFSET = 0.52


def draw_cell(x, y, lines, ha, **kw):
    if len(lines) == 1:
        ax.text(x, y, lines[0], ha=ha, va="center", **kw)
    else:
        ax.text(x, y + TWO_LINE_OFFSET, lines[0], ha=ha, va="center", **kw)
        ax.text(x, y - TWO_LINE_OFFSET, lines[1], ha=ha, va="center", **kw)


def pack_fontsize(text):
    # 包装が複数個(カプセル等の長い単位が連なる場合)は小さめに。ただし印刷6pt(MIN_FS)は下回らない
    return 8.9 if len(text) <= 6 else (7.6 if len(text) <= 11 else MIN_FS)


prev_h = None
for i, row in mart.iterrows():
    rh = row["row_h"]
    if prev_h is not None:
        current_y -= (prev_h + rh) / 2
    prev_h = rh
    if i % 2 == 0:
        ax.add_patch(patches.Rectangle((0, current_y - rh / 2), LOGICAL_W, rh, facecolor="#f5f5f5", edgecolor="none", zorder=0))

    display_name = DISPLAY_NAME_OVERRIDE.get(row["product"], row["product"])
    name_len = len(display_name)
    name_fontsize = 9.6 if name_len <= 8 else (8.7 if name_len <= 12 else (7.8 if name_len <= 18 else MIN_FS))
    name_text = display_name + ("※" if row["is_caplet"] else "")
    ax.text(COL_NAME_X, current_y, name_text, fontsize=name_fontsize, fontweight="bold", ha="left", va="center")

    if row["ingr_lines"]:
        draw_cell(COL_INGR_X, current_y, row["ingr_lines"], "left", fontsize=MIN_FS, color="#555555")
    else:
        ax.text(COL_INGR_X, current_y, "-", fontsize=7.8, ha="left", va="center", color="#aaaaaa")

    ax.text(COL_DOSE_X, current_y, row["daily"], fontsize=10.3, ha="center", va="center")

    mult_color = "#1565c0" if row["limit"] == 7 else "#e65100"
    ax.text(COL_MULT_X, current_y, f"×{row['limit']}", fontsize=8.6, ha="center", va="center",
            color=mult_color, fontweight="bold")

    if row["small"] != "-":
        fs = pack_fontsize(row["small"])
        draw_cell(COL_SMALL_X, current_y, split_two_lines(row["small"], fs, SMALL_MAX_W, " "), "center",
                  fontsize=fs, fontweight="bold")

    ax.vlines(COL_BOUND_X, current_y - 0.85, current_y + 0.85, color="#bbbbbb", linewidth=1.0, zorder=1)
    ax.text(COL_BOUND_X, current_y, row["boundary"], fontsize=7.5, ha="center", va="center", color=GRAY, zorder=2)

    if row["large"] != "-":
        fs = pack_fontsize(row["large"])
        draw_cell(COL_LARGE_X, current_y, split_two_lines(row["large"], fs, LARGE_MAX_W, " "), "center",
                  fontsize=fs, fontweight="bold", color="#444444")

current_y -= prev_h

current_y -= 1.35
ax.text(COL_NAME_X, current_y,
        "※＝カプレット表記（ベンザブロック◯◯/末尾「錠」なし）。1日成分量は「◯◯錠」と同一ですが服用粒数が異なります。",
        fontsize=MIN_FS, ha="left", va="center", color="#888888")

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
    ax.text(COL_NAME_X + 11.2, current_y, "※該当はまれです", fontsize=MIN_FS, fontstyle="italic",
            ha="left", va="center", color=LGRAY)
    ax.text(28.0, current_y, "指定濫用判定", fontsize=8.54, fontweight="bold", ha="center", va="center")
    ax.text(41.0, current_y, "同ブランド内比較・注釈（「対比:」＝取り違え注意ポイント）", fontsize=8.54, fontweight="bold", ha="left", va="center")

    current_y -= 1.4
    ax.hlines(current_y, 0, LOGICAL_W, colors="#cccccc", linewidth=0.8)
    current_y -= 2.0

    ref_row_h = 2.65
    for j, (_, row) in enumerate(reference.iterrows()):
        if j % 2 == 0:
            ax.add_patch(patches.Rectangle((0, current_y - 1.55), LOGICAL_W, ref_row_h, facecolor="#fafafa", edgecolor="none"))
        ax.text(COL_NAME_X, current_y, row["product"], fontsize=8.42, fontweight="bold", ha="left", va="center")
        ax.text(28.0, current_y, row["status_text"], fontsize=8.42, fontweight="bold", ha="center", va="center", color=row["status_color"])
        is_taichi = row["note"].startswith("対比")
        ax.text(41.0, current_y, row["note"], fontsize=7.34, fontweight="bold" if is_taichi else "normal",
                ha="left", va="center", color=INK if is_taichi else GRAY)
        if row["ingr_detail"]:
            # 成分詳細は商品名・判定の下の行に全幅で書く（同じ高さに他の文字がないため省略せずに載せられる）
            ax.text(COL_NAME_X, current_y - 1.25, row["ingr_detail"], fontsize=MIN_FS, ha="left", va="center", color="#777777")
        current_y -= ref_row_h

current_y -= 0.65
ax.hlines(current_y, 0, LOGICAL_W, colors="#dddddd", linewidth=0.7)
current_y -= 1.08

# --- フッター：左に免責・出典・アプリURL、右にQR（横並び） ---
detail_top = current_y
ax.hlines(detail_top, 0, LOGICAL_W, colors="#999999", linewidth=1.0)

qr_size = 5.6
QR_X1, QR_X2 = 85.0, 94.0  # キャプション(印刷6pt)同士が重ならない間隔
qr_top = detail_top - 0.6
qr_center_y = qr_top - qr_size / 2
for qx, path in ((QR_X1, QR_APP_PATH), (QR_X2, QR_FORM_PATH)):
    try:
        ax.imshow(mpimg.imread(path), extent=[qx - qr_size / 2, qx + qr_size / 2,
                                              qr_center_y - qr_size / 2, qr_center_y + qr_size / 2], zorder=3)
    except Exception:
        ax.add_patch(patches.Rectangle((qx - qr_size / 2, qr_center_y - qr_size / 2), qr_size, qr_size,
                                       fill=False, edgecolor="#cccccc", zorder=3))
qr_y = qr_center_y - qr_size / 2 - 0.45
ax.text(QR_X1, qr_y, "参考：商品検索", fontsize=MIN_FS, ha="center", va="top", color=INK, fontweight="bold")
ax.text(QR_X2, qr_y, "ご意見・改善案", fontsize=MIN_FS, ha="center", va="top", color="#555555", fontweight="bold")

FOOT_LH = 1.2
y = detail_top - 1.6
ax.text(COL_NAME_X, y, "免責: 過去に用法用量超過の自己判断服用で重篤な健康被害が生じた事例を踏まえた確認です。意図的な過量服薬は保証・救済制度の対象外です。",
        fontsize=MIN_FS, ha="left", va="center", color=LGRAY)
y -= FOOT_LH
text_run(COL_NAME_X, y, [("参考：商品検索（表にない商品はこちら）　", {"fontweight": "bold", "color": "#555555"}),
                         (APP_URL.replace("https://", ""), {"color": "#555555"})], fontsize=MIN_FS)
y -= FOOT_LH
ax.text(COL_NAME_X, y, "準拠: 厚生労働省 局長通知「指定濫用防止医薬品の指定について」・厚生労働大臣が定める数量（告示）",
        fontsize=MIN_FS, ha="left", va="center", color="#999999")
y -= FOOT_LH
ax.text(COL_NAME_X, y, "　　　JSMI「指定濫用防止医薬品の販売制度について」／兵庫県 薬務課 制度改正資料",
        fontsize=MIN_FS, ha="left", va="center", color="#999999")
y = min(y, qr_y - 1.0)

check_min_font(fig, "1枚目")
plt.savefig(OUTPUT_PNG, dpi=300)
plt.savefig(OUTPUT_PDF)
plt.close()

print("==========================================")
print("v13【1枚目】A4 早見表生成完了")
print(f"出力ファイル: {OUTPUT_PNG}")
print(f"フッター最下端y(0.6以上で用紙内): {y:.2f}")
print("==========================================")
