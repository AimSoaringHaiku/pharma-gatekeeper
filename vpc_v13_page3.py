import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import japanize_matplotlib
from print_style import MIN_FS, BODY_FS, SOURCE_TEXT, check_min_font, wrap_fill

OUTPUT_PNG = "atomic_card_table_v13_page3.png"
OUTPUT_PDF = "atomic_card_table_v13_page3.pdf"
IMG_POSTER1 = "ref_poster_kounyusha.png"   # 「指定濫用防止医薬品をご購入時フリップ」
IMG_POSTER2 = "ref_poster_oshirase.png"    # 「大切なお知らせ」販売方法の変更
IMG_FLOWCHART = "ref_flowchart.png"        # 「販売可否判断フローチャート」OTCマニュアル(第2版)

# A4縦相当の比率レイアウト（表面と用紙を揃え、両面印刷での取り扱いを統一）
LOGICAL_W, LOGICAL_H = 100.0, 141.4
fig, ax = plt.subplots(figsize=(10, 14.14))
ax.set_position([0, 0, 1, 1])  # savefigでbbox_inches="tight"を使わず全面を使う（比率固定のため必須）
ax.set_xlim(0, LOGICAL_W)
ax.set_ylim(0, LOGICAL_H)
ax.axis("off")
fig.canvas.draw()  # テキスト幅計測のため、先に一度描画してレンダラーを確保

BLUE, RED, ORANGE, GREEN, GRAY, DARKRED = "#1565c0", "#d32f2f", "#e65100", "#2e7d32", "#555555", "#8e0000"
INK = "#1a1a1a"  # 白黒印刷を基本とし、解釈層(☞)と赤字指定の禁忌系のみ色を残す


# テキスト幅測定専用の figure（本体 fig とは別）。
_meas_fig, _meas_ax = plt.subplots(figsize=(10, 14.14))
_meas_ax.set_position([0, 0, 1, 1])  # 本体と同じ全面配置にしないと、文字幅を約1.3倍に見積もってしまう
_meas_ax.set_xlim(0, 100.0)
_meas_ax.set_ylim(0, 141.4)
_meas_ax.axis("off")
_meas_fig.canvas.draw()


def text_width(text, fontsize, weight="normal", style="normal"):
    t = _meas_ax.text(0, -200, text, fontsize=fontsize, fontweight=weight, fontstyle=style, ha="left", va="center")
    bbox = t.get_window_extent(renderer=_meas_fig.canvas.get_renderer())
    inv = _meas_ax.transData.inverted()
    (x0, _), (x1, _) = inv.transform([[bbox.x0, bbox.y0], [bbox.x1, bbox.y1]])
    t.remove()
    return x1 - x0


def _split_chars(text, fontsize, max_width):
    lines, cur = [], ""
    for ch in text:
        trial = cur + ch
        if cur and text_width(trial, fontsize) > max_width:
            lines.append(cur)
            cur = ch
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def wrap_to_width(text, fontsize, max_width):
    """句読点等の直後を優先的な改行位置とし、意味のまとまりで行分割する。"""
    tokens, cur_token = [], ""
    for ch in text:
        cur_token += ch
        if ch in "。、）)」":
            tokens.append(cur_token)
            cur_token = ""
    if cur_token:
        tokens.append(cur_token)

    lines, cur = [], ""
    for token in tokens:
        trial = cur + token
        if cur and text_width(trial, fontsize) > max_width:
            lines.append(cur)
            cur = token
        else:
            cur = trial
    if cur:
        lines.append(cur)

    final_lines = []
    for line in lines:
        if text_width(line, fontsize) <= max_width:
            final_lines.append(line)
        else:
            final_lines.extend(_split_chars(line, fontsize, max_width))

    merged = []
    for line in final_lines:
        if merged and len(line) <= 2 and all(c in "。、）)」" for c in line):
            merged[-1] += line
        else:
            merged.append(line)
    return merged


# --- タイトル（上部余白は廃止。表面と同じ密度感で4分割へ） ---
ax.text(LOGICAL_W / 2, LOGICAL_H - 2.4, "【3枚目】社内マニュアル参考資料集", fontsize=14, fontweight="bold",
        ha="center", va="center", color="#222222")
ax.text(LOGICAL_W / 2, LOGICAL_H - 4.1, "（厚労省・薬局配布資料の要点を再構成　／　右下＝赤枠のふり番・脚注）",
        fontsize=MIN_FS, ha="center", va="center", color="#777777")
ax.hlines(LOGICAL_H - 5.3, 2.0, 98.0, colors="#999999", linewidth=1.2)

# --- 2x2グリッド配置 ---
GRID_LEFT, GRID_RIGHT = 2.0, 98.0
GRID_TOP = LOGICAL_H - 6.3
GRID_BOTTOM = 3.0
GUTTER = 2.0
COL_W = (GRID_RIGHT - GRID_LEFT - GUTTER) / 2
ROW_H = (GRID_TOP - GRID_BOTTOM - GUTTER) / 2

Q1_X, Q2_X = GRID_LEFT, GRID_LEFT + COL_W + GUTTER
ROW1_TOP = GRID_TOP
ROW2_TOP = GRID_TOP - ROW_H - GUTTER


def panel_frame(x, y_top, w, h, title, color, subtitle=None):
    """タイトルバー＋元資料名の副題（任意）付きのパネル枠。中身の描画開始y座標を返す。"""
    y_bottom = y_top - h
    ax.add_patch(patches.FancyBboxPatch((x, y_bottom), w, h, boxstyle="round,pad=0.12",
                                         linewidth=1.2, edgecolor=color, facecolor="white", zorder=1))
    sub_fs = MIN_FS
    sub_lines = wrap_to_width(subtitle, sub_fs, w - 2.0) if subtitle else []
    bar_h = 2.6 + (1.25 * len(sub_lines) if sub_lines else 0)
    ax.add_patch(patches.FancyBboxPatch((x, y_top - bar_h), w, bar_h, boxstyle="round,pad=0.12",
                                         linewidth=0, facecolor=color, zorder=2))
    title_y = y_top - (1.35 if sub_lines else bar_h / 2)
    ax.text(x + w / 2, title_y, title, fontsize=BODY_FS, fontweight="bold",
            ha="center", va="center", color="white", zorder=3)
    sy = title_y - 1.45
    for line in sub_lines:
        ax.text(x + w / 2, sy, line, fontsize=sub_fs, ha="center", va="center", color="#eef4fb", zorder=3)
        sy -= 1.25
    return y_top - bar_h - 0.7


def draw_magnifier_icon(cx, cy, r, handle_len, color, angle_deg=-40):
    """虫眼鏡アイコン：レンズ(円)＋斜めの持ち手。持ち手の先端座標を返す（そこから説明文を続ける）。"""
    import math
    rad = math.radians(angle_deg)
    dx, dy = math.cos(rad), math.sin(rad)
    edge_x, edge_y = cx + r * dx, cy + r * dy
    tip_x, tip_y = cx + (r + handle_len) * dx, cy + (r + handle_len) * dy
    ax.add_patch(patches.Circle((cx, cy), r, facecolor="none", edgecolor=color, linewidth=1.3, zorder=5))
    ax.plot([edge_x, tip_x], [edge_y, tip_y], color=color, linewidth=1.5, solid_capstyle="round", zorder=5)
    return tip_x, tip_y


def draw_focus_footnote(focus_x, focus_y, lens_r, foot_x, foot_y, text, w, fontsize=MIN_FS, line_h=1.5,
                         color=RED, halign="left"):
    """元資料の言及箇所に虫眼鏡のレンズを重ね、持ち手を脚注ボックスまで伸ばして「」付きで説明する。
    レンズ＝該当箇所に直接かぶせる円。脚注＝余白にボックスで独立配置。"""
    import math
    text = text.lstrip("☞")
    ax.add_patch(patches.Circle((focus_x, focus_y), lens_r, facecolor="none", edgecolor=color, linewidth=1.4, zorder=6))
    dx, dy = foot_x - focus_x, foot_y - focus_y
    dist = math.hypot(dx, dy) or 1.0
    ux, uy = dx / dist, dy / dist
    edge_x, edge_y = focus_x + lens_r * ux, focus_y + lens_r * uy
    ax.plot([edge_x, foot_x], [edge_y, foot_y], color=color, linewidth=1.2, linestyle=(0, (3, 2)), zorder=6)
    lines = wrap_to_width(f"「{text}」", fontsize, w - 1.0)
    for i, line in enumerate(lines):
        ax.text(foot_x, foot_y - i * line_h, line, fontsize=fontsize, fontweight="bold",
                ha=halign, va="center", color=color, fontstyle="italic", zorder=7,
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor=color, linewidth=0.9, alpha=0.96))
    return foot_y - len(lines) * line_h


def draw_numbered_box(cx, cy, w, h, number, color=RED):
    """元資料の該当箇所を赤枠で囲み、隅に丸数字バッジを付ける（脚注はQ4に別記）。"""
    x0, y0 = cx - w / 2, cy - h / 2
    ax.add_patch(patches.Rectangle((x0, y0), w, h, fill=False, edgecolor=color, linewidth=1.7, zorder=6))
    badge_r = 0.95  # ふり番の数字を印刷6pt以上で読めるよう、枠の大きさによらず一定サイズにする
    bx, by = x0, y0 + h
    ax.add_patch(patches.Circle((bx, by), badge_r, facecolor=color, edgecolor="white", linewidth=0.8, zorder=7))
    ax.text(bx, by, str(number), fontsize=MIN_FS, fontweight="bold", ha="center", va="center",
            color="white", zorder=8)


def draw_callout_note(cx, cy, text, w, fontsize=MIN_FS, line_h=1.5, color=RED, halign="left"):
    """元資料の画像上の余白に直接書き込む、手書きメモ風の短い注釈（虫眼鏡アイコン＋断定しすぎない一言）。
    白黒印刷でも判別できるよう、枠線付きの吹き出し（fill無し）にする。"""
    text = text.lstrip("☞")
    icon_r = fontsize * 0.15
    icon_cx = cx + icon_r * 1.3 if halign == "left" else cx - icon_r * 1.3
    tip_x, _ = draw_magnifier_icon(icon_cx, cy + icon_r * 0.7, icon_r, icon_r * 1.5, color,
                                    angle_deg=-40 if halign == "left" else -140)
    text_x = tip_x + icon_r * 0.5 if halign == "left" else tip_x - icon_r * 0.5
    lines = wrap_to_width(text, fontsize, w)
    for i, line in enumerate(lines):
        ax.text(text_x, cy - i * line_h, line, fontsize=fontsize, fontweight="bold",
                ha=halign, va="center", color=color, fontstyle="italic", zorder=4,
                bbox=dict(boxstyle="round,pad=0.08", facecolor="white", edgecolor=color, linewidth=0.5, alpha=0.92))
    return cy - len(lines) * line_h


def draw_poster_image_fit(x, y_top, w, h_avail, img_path):
    """元資料の画像を、幅・高さ両方の制約に収まるようセンタリング表示する（記述層）。"""
    img = mpimg.imread(img_path)
    img_h_px, img_w_px = img.shape[0], img.shape[1]
    aspect = img_w_px / img_h_px
    target_w, target_h = w, w / aspect
    if target_h > h_avail:
        target_h = h_avail
        target_w = target_h * aspect
    img_x0 = x + (w - target_w) / 2
    img_y1 = y_top
    img_y0 = img_y1 - target_h
    ax.imshow(img, extent=[img_x0, img_x0 + target_w, img_y0, img_y1], zorder=2)
    ax.add_patch(patches.Rectangle((img_x0, img_y0), target_w, target_h, fill=False,
                                    edgecolor="#cccccc", linewidth=0.5, zorder=3))
    return img_x0, img_y1, target_w, target_h


# ==========================================================
# 参考① 購入者への掲示例
# ==========================================================
def draw_poster1(x, y_top, w, h):
    y = panel_frame(x, y_top, w, h, "参考① 購入者への掲示例", INK,
                     subtitle="元資料：指定濫用防止医薬品をご購入時フリップ")
    img_x0, img_y1, img_w, img_h = draw_poster_image_fit(x, y, w, y - (y_top - h) - 0.3, IMG_POSTER1)
    focus_y = img_y1 - 0.485 * img_h
    draw_numbered_box(img_x0 + img_w * 0.42, focus_y, img_w * 0.72, img_w * 0.045, 1)


# ==========================================================
# 参考② 制度改正のお知らせ
# ==========================================================
def draw_poster2(x, y_top, w, h):
    y = panel_frame(x, y_top, w, h, "参考② 制度改正のお知らせ", INK,
                     subtitle="元資料：薬物濫用ポスター「大切なお知らせ」")
    frame_bottom = y_top - h
    img_x0, img_y1, img_w, img_h = draw_poster_image_fit(x, y, w, y - frame_bottom - 0.3, IMG_POSTER2)
    focus_x, focus_y = img_x0 + img_w * 0.64, img_y1 - 0.843 * img_h
    draw_numbered_box(focus_x, focus_y, img_w * 0.10, img_w * 0.055, 2)


# ==========================================================
# 参考③ 来店〜販売可否フロー
# ==========================================================
def draw_poster3_flow(x, y_top, w, h):
    y = panel_frame(x, y_top, w, h, "参考③ 来店〜販売可否フロー", INK,
                     subtitle="元資料：販売可否判断フローチャート")
    frame_bottom = y_top - h
    img_x0, img_y1, img_w, img_h = draw_poster_image_fit(x, y, w, y - frame_bottom - 0.3, IMG_FLOWCHART)
    focus_y = img_y1 - 0.803 * img_h
    draw_numbered_box(img_x0 + img_w * 0.70, focus_y, img_w * 0.15, img_w * 0.045, 3)
    focus_y2 = img_y1 - 0.514 * img_h
    draw_numbered_box(img_x0 + img_w * 0.29, focus_y2, img_w * 0.26, img_w * 0.032, 4)


draw_poster1(Q1_X, ROW1_TOP, COL_W, ROW_H)
draw_poster2(Q2_X, ROW1_TOP, COL_W, ROW_H)
draw_poster3_flow(Q1_X, ROW2_TOP, COL_W, ROW_H)


# ==========================================================
# ④ 脚注（右下1マス。赤枠＋ふり番を付けた箇所の説明を番号順に記載）
# ==========================================================
Q4_X, Q4_TOP, Q4_W, Q4_H = Q2_X, ROW2_TOP, COL_W, ROW_H

FOOTNOTES = [
    (1, "参考①", "「理由確認」欄は成人（18歳以上）のみが対象です",
     "赤枠の「大容量製品又は複数個の購入に該当する場合、その理由」は、18歳以上の購入者様にのみご確認いただく項目です。"
     "18歳未満の方は、理由の如何を問わず一律で販売不可となりますので、あわせてご留意ください。"),
    (2, "参考②", "「大容量」の目印について",
     "外枠の「要確認」という表示自体は、小容量・大容量どちらの商品にも共通して付いています。違いは「要」の文字にさらに丸い囲みが付くかどうかで、"
     "大容量側のみ追加の囲みが付いていることが多いです（表示は製品や年代により異なり、旧い包装には記載がない場合もございますので、あわせてご確認ください）。"),
    (3, "参考③", "「販売実施」の後も、申し送りが必要な場合がございます",
     "「販売実施」で対応完了のように見えますが、実際には販売後も、購入者様のご様子や理由のご説明状況によっては、"
     "「申し送り対応の実施」（購入者様の特徴・来店日時・購入商品等を帳簿等にご記載いただくこと）が必要になる場合がございます。"),
    (4, "参考③", "赤枠「18歳以上への販売」について",
     "大容量・複数個の購入理由を確認するのは、この「18歳以上への販売」の分岐に進んだ場合のみです。18歳未満は年齢確認の時点で一律に大容量・複数個が販売不可となるため、"
     "理由確認はこの分岐に該当する成人のみが対象です。"),
]

NOTES = [
    ("身分証明書提示について（自店ルール）",
     "法律や国の通知に「学生証を提示させる」といった具体的な書類名の規定はありませんが、現場でのトラブルを防ぎ確実な確認を行うため、"
     "当店では必ず「公的な身分証明書」（学生証・健康保険証・マイナンバーカード・運転免許証等）の提示をお願いするルールとしています。"),
    ("この規制がある理由（免責事項の根拠）",
     "かつて安全確認が不十分なまま販売され、規定量を上回る自己判断の服用により重篤な健康被害に至った事例がありました。今回の確認は個人ではなく社会構造的な問題として、"
     "同じ事象を繰り返さないための取り組みです。市販薬は厳格な配合・最大量のルールの下で設計されており、用法用量を守ることで最大の効果と安全性が得られます。"
     "意図的な過量服薬による健康被害は保証・救済制度の対象外となるため、複数の薬の同時服用についてもあわせてご確認をお願いしています。"),
]

header_h4 = 2.6
ax.add_patch(patches.FancyBboxPatch((Q4_X, Q4_TOP - Q4_H), Q4_W, Q4_H,
                                     boxstyle="round,pad=0.12", linewidth=1.3, edgecolor=INK, facecolor="#fbfbfb", zorder=0))
ax.add_patch(patches.FancyBboxPatch((Q4_X, Q4_TOP - header_h4), Q4_W, header_h4,
                                     boxstyle="round,pad=0.12", linewidth=0, facecolor=INK, zorder=1))
ax.text(Q4_X + Q4_W / 2, Q4_TOP - header_h4 / 2, "④ 赤枠のふり番・脚注／確認業務の補足", fontsize=BODY_FS, fontweight="bold",
        ha="center", va="center", color="white", zorder=3)


def draw_footnote_entry(x, y, w, number, source, title, body, fs_num=6.5, fs_title=6.0, fs_body=5.3, line_h=1.4):
    badge_r = fs_num * 0.16
    ax.add_patch(patches.Circle((x + badge_r, y - badge_r * 0.2), badge_r, facecolor=RED, edgecolor="white",
                                 linewidth=0.7, zorder=4))
    ax.text(x + badge_r, y - badge_r * 0.2, str(number), fontsize=fs_num, fontweight="bold",
            ha="center", va="center", color="white", zorder=5)
    tx = x + badge_r * 2.6
    ax.text(tx, y, f"{source}／{title}", fontsize=fs_title, fontweight="bold", ha="left", va="center", color=INK)
    y -= line_h * 1.15
    for line in wrap_fill(body, fs_body, w - badge_r * 2.6 - 0.5, text_width):
        ax.text(tx, y, line, fontsize=fs_body, ha="left", va="center", color="#333333")
        y -= line_h
    y -= 0.35
    ax.hlines(y, x, x + w, colors="#dddddd", linewidth=0.6)
    return y - 0.5


def draw_note_entry(x, y, w, title, body, fs_title=6.0, fs_body=5.3, line_h=1.4):
    ax.text(x, y, f"■ {title}", fontsize=fs_title, fontweight="bold", ha="left", va="center", color=BLUE)
    y -= line_h * 1.15
    for line in wrap_fill(body, fs_body, w - 0.5, text_width):
        ax.text(x, y, line, fontsize=fs_body, ha="left", va="center", color="#333333")
        y -= line_h
    y -= 0.35
    ax.hlines(y, x, x + w, colors="#dddddd", linewidth=0.6)
    return y - 0.5


def render_footnotes(fs_num, fs_title, fs_body, line_h):
    y = Q4_TOP - header_h4 - line_h * 0.9
    for number, source, title, body in FOOTNOTES:
        y = draw_footnote_entry(Q4_X + 0.8, y, Q4_W - 1.6, number, source, title, body, fs_num, fs_title, fs_body, line_h)
    for title, body in NOTES:
        y = draw_note_entry(Q4_X + 0.8, y, Q4_W - 1.6, title, body, fs_title, fs_body, line_h)
    return y


_dry_fig, _dry_ax = plt.subplots(figsize=(10, 14.14))
_dry_ax.set_xlim(0, LOGICAL_W)
_dry_ax.set_ylim(0, LOGICAL_H)
_dry_ax.axis("off")

_real_ax = ax
ax = _dry_ax
# 本文は印刷6pt（MIN_FS）を下限に、行送りは本文の約1.45倍（1論理単位＝7.2pt）
BASE_NUM, BASE_TITLE, BASE_BODY = MIN_FS * 1.1, MIN_FS * 1.08, MIN_FS
BASE_LH = BASE_BODY * 1.45 / 7.2
avail_h4 = Q4_TOP - header_h4 - (Q4_TOP - Q4_H) - 0.4

lo, hi = 1.0, 1.35  # 下限1.0＝本文が印刷6pt未満にならない
for _ in range(16):
    mid = (lo + hi) / 2
    _dry_ax.cla()
    _dry_ax.axis("off")
    probe_end = render_footnotes(BASE_NUM * mid, BASE_TITLE * mid, BASE_BODY * mid, BASE_LH * mid)
    needed_h = (Q4_TOP - header_h4) - probe_end
    if needed_h <= avail_h4:
        lo = mid
    else:
        hi = mid
SCALE4 = lo
ax = _real_ax
_dry_fig.clf()

render_footnotes(BASE_NUM * SCALE4, BASE_TITLE * SCALE4, BASE_BODY * SCALE4, BASE_LH * SCALE4)

# --- 下部免責・出典 ---
ax.text(LOGICAL_W / 2, 2.15, "※本マニュアルは一次対応の目安であり、個別の診断ではありません。最終判断は薬剤師・登録販売者の専門的知見に基づき行ってください。",
        fontsize=MIN_FS, ha="center", va="center", color=GRAY)
ax.text(LOGICAL_W / 2, 0.95,
        SOURCE_TEXT,
        fontsize=MIN_FS, ha="center", va="center", color="#aaaaaa")

check_min_font(fig, "3枚目")
fig.savefig(OUTPUT_PNG, dpi=300)
fig.savefig(OUTPUT_PDF)
plt.close(fig)
plt.close(_meas_fig)
print(f"v13【3枚目】出力完了: {OUTPUT_PNG}")
print(f"4分割グリッド: COL_W={COL_W:.2f} ROW_H={ROW_H:.2f}")
print(f"④脚注文字スケール: {SCALE4:.3f}")
