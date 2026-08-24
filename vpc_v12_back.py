import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import japanize_matplotlib

OUTPUT_PNG = "atomic_card_table_v12_back.png"
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


# テキスト幅測定専用の figure（本体 fig とは別）。
_meas_fig, _meas_ax = plt.subplots(figsize=(10, 14.14))
_meas_ax.set_xlim(0, 100.0)
_meas_ax.set_ylim(0, 141.4)
_meas_ax.axis("off")
_meas_fig.canvas.draw()


def text_width(text, fontsize, weight="normal", style="normal"):
    t = _meas_ax.text(0, -200, text, fontsize=fontsize, fontweight=weight, fontstyle=style, ha="left", va="center")
    _meas_fig.canvas.draw()
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
        if ch in "。、）)":
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
        if merged and len(line) <= 2 and all(c in "。、）)" for c in line):
            merged[-1] += line
        else:
            merged.append(line)
    return merged


# --- タイトル（上部余白は廃止。表面と同じ密度感で4分割へ） ---
ax.text(LOGICAL_W / 2, LOGICAL_H - 2.4, "【裏面】指定濫用防止医薬品 参考資料集", fontsize=14, fontweight="bold",
        ha="center", va="center", color="#222222")
ax.text(LOGICAL_W / 2, LOGICAL_H - 4.1, "（厚労省・薬局配布資料の要点を再構成　／　右下＝状況別対応のポイント）",
        fontsize=6.6, ha="center", va="center", color="#777777")
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
    sub_fs = 3.9
    sub_lines = wrap_to_width(subtitle, sub_fs, w - 2.0) if subtitle else []
    bar_h = 2.2 + (0.8 * len(sub_lines) if sub_lines else 0)
    ax.add_patch(patches.FancyBboxPatch((x, y_top - bar_h), w, bar_h, boxstyle="round,pad=0.12",
                                         linewidth=0, facecolor=color, zorder=2))
    title_y = y_top - (1.1 if sub_lines else bar_h / 2)
    ax.text(x + w / 2, title_y, title, fontsize=6.4, fontweight="bold",
            ha="center", va="center", color="white", zorder=3)
    sy = title_y - 1.0
    for line in sub_lines:
        ax.text(x + w / 2, sy, line, fontsize=sub_fs, ha="center", va="center", color="#eef4fb", zorder=3)
        sy -= 0.8
    return y_top - bar_h - 0.7


def draw_callout_note(cx, cy, text, w, fontsize=3.5, line_h=1.3, color=RED, halign="left"):
    """元資料の画像上の余白に直接書き込む、手書きメモ風の短い注釈（☞＋断定しすぎない一言）。
    白黒印刷でも判別できるよう、枠線付きの吹き出し（fill無し）にする。"""
    lines = wrap_to_width(text, fontsize, w)
    for i, line in enumerate(lines):
        ax.text(cx, cy - i * line_h, line, fontsize=fontsize, fontweight="bold",
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
    y = panel_frame(x, y_top, w, h, "参考① 購入者への掲示例", BLUE,
                     subtitle="元資料：指定濫用防止医薬品をご購入時フリップ")
    img_x0, img_y1, img_w, img_h = draw_poster_image_fit(x, y, w, y - (y_top - h) - 0.3, IMG_POSTER1)
    draw_callout_note(img_x0 + img_w * 0.35, img_y1 - 0.370 * img_h,
                       "☞理由確認は成人(18歳以上)のみ対象", img_w * 0.62, fontsize=3.3)


# ==========================================================
# 参考② 制度改正のお知らせ
# ==========================================================
def draw_poster2(x, y_top, w, h):
    y = panel_frame(x, y_top, w, h, "参考② 制度改正のお知らせ", ORANGE,
                     subtitle="元資料：薬物濫用ポスター「大切なお知らせ」")
    frame_bottom = y_top - h
    img_x0, img_y1, img_w, img_h = draw_poster_image_fit(x, y, w, y - frame_bottom - 4.4, IMG_POSTER2)
    yy = img_y1 - img_h - 1.1
    yy = draw_callout_note(x + 0.4, yy,
                            "☞目印の傾向：小容量は「要確認」全体を、大容量は「要」の一文字だけを枠で囲むことが多い",
                            w - 0.8, fontsize=3.3, line_h=1.35, color=RED)
    yy -= 0.25
    yy = draw_callout_note(x + 0.4, yy,
                            "パッケージ表記は数年かけて順次変更される予定。変更後もお客様へ正しくご案内できるよう、"
                            "情報にアンテナを張っておきましょう（村松早織先生／cheer-job.comコラム）",
                            w - 0.8, fontsize=3.0, line_h=1.25, color="#666666")


# ==========================================================
# 参考③ 来店〜販売可否フロー
# ==========================================================
def draw_poster3_flow(x, y_top, w, h):
    y = panel_frame(x, y_top, w, h, "参考③ 来店〜販売可否フロー", GREEN,
                     subtitle="元資料：販売可否判断フローチャート")
    frame_bottom = y_top - h
    img_x0, img_y1, img_w, img_h = draw_poster_image_fit(x, y, w, y - frame_bottom - 0.3, IMG_FLOWCHART)
    draw_callout_note(img_x0 + img_w * 0.68, img_y1 - 0.838 * img_h,
                       "☞販売しても「申し送り」が必要な場合あり", img_w * 0.30, fontsize=3.1, line_h=1.2)


draw_poster1(Q1_X, ROW1_TOP, COL_W, ROW_H)
draw_poster2(Q2_X, ROW1_TOP, COL_W, ROW_H)
draw_poster3_flow(Q1_X, ROW2_TOP, COL_W, ROW_H)

# ==========================================================
# ④ 状況別対応のポイント（右下1マスに集約。文字サイズは内容量から自動算出）
# ==========================================================
Q4_X, Q4_TOP, Q4_W, Q4_H = Q2_X, ROW2_TOP, COL_W, ROW_H


def draw_alert_bullet(x, y, w, text, fontsize, line_h):
    """禁忌・一律不可等の重要事項は「■」＋太字＋赤で強調（色が飛ぶ白黒印刷でも■と太字で判別可）。"""
    is_alert = ("禁忌" in text) or ("一律" in text) or ("不可" in text) or ("NG" in text)
    mark = "■" if is_alert else "▶"
    color = RED if is_alert else "#222222"
    weight = "bold" if is_alert else "normal"
    wrapped = wrap_to_width(f"{mark}{text}", fontsize, w - 1.0)
    for wi, wline in enumerate(wrapped):
        indent = x if wi == 0 else x + 1.4
        ax.text(indent, y, wline, fontsize=fontsize, ha="left", va="center", color=color, fontweight=weight)
        y -= line_h
    return y


def draw_case(x, y, w, q_num, category, condition, bullets, fs_tag, fs_body, line_h):
    tag = f"{q_num}{category}"
    tag_w = text_width(tag, fs_tag, "bold") + 1.2
    tag_h = line_h * 0.92
    ax.add_patch(patches.FancyBboxPatch((x, y - tag_h / 2), tag_w, tag_h, boxstyle="round,pad=0.05",
                                         linewidth=0.6, edgecolor=BLUE, facecolor=BLUE, zorder=2))
    ax.text(x + tag_w / 2, y, tag, fontsize=fs_tag, fontweight="bold", ha="center", va="center",
            color="white", zorder=3)
    cond_x = x + tag_w + 0.9
    wrapped_cond = wrap_to_width(condition, fs_tag, w - tag_w - 0.9)
    if wrapped_cond:
        ax.text(cond_x, y, wrapped_cond[0], fontsize=fs_tag, fontweight="bold", ha="left", va="center", color="#222222")
    y -= line_h
    for line in wrapped_cond[1:]:
        ax.text(x, y, line, fontsize=fs_tag, fontweight="bold", ha="left", va="center", color="#222222")
        y -= line_h
    for bullet in bullets:
        y = draw_alert_bullet(x + 0.3, y, w, bullet, fs_body, line_h)
    y -= 0.12
    ax.hlines(y, x, x + w, colors="#cccccc", linewidth=0.6)
    return y - 0.3


CASES = [
    ("①②", "年齢・重複", "18歳未満/複数個(他店合算)希望", [
        "18歳未満：大容量・複数個は理由不問で一律不可(家族用も例外なし)。",
        "12歳未満：コデイン系(ジヒドロコデイン含)絶対禁忌⇒他成分の咳止めへ。",
        "身分証拒否：年齢確認不能のため販売不可。",
    ]),
    ("③", "体質(アレルギー)", "解熱鎮痛薬でアレルギー歴", [
        "ピリン疹：NSAIDs(ロキソプロフェン等)へ代替可。",
        "アスピリン喘息：NSAIDs全般に交差耐性で全てNG⇒AAP単剤のみ提案。",
    ]),
    ("③", "体質(喘息・不整脈等)", "喘息/不整脈/緑内障/前立腺肥大/高血圧・糖尿病", [
        "抗コリン薬・第一世代抗ヒス：喘息=痰粘稠化、不整脈=頻脈・QT延長。",
        "緑内障=眼圧上昇、前立腺肥大=尿閉⇒単一成分薬を推奨。",
        "プソイドエフェドリン：上記に加え高血圧・心疾患・糖尿病・甲状腺機能亢進も対象。",
    ]),
    ("④", "併用", "SSRI服用中/他剤併用", [
        "最重要：DXM×SSRIはセロトニン症候群リスク(致死率最高クラスの相互作用)。",
        "GFJでDXM血中濃度↑。マクロライド系/アゾール系はQT延長・心室頻拍に注意。",
    ]),
    ("⑤", "妊婦・授乳", "妊娠中/授乳中と判明", [
        "禁忌：妊娠後期のコデイン系⇒新生児呼吸抑制。メジコン等単剤(DXM)を提案。",
        "抗コリン薬(ブスコパン等)はOTC一律不可。授乳中は母乳分泌↓・乳児頻脈で中断。",
        "コンタック鼻炎Z(セチリジン)は妊婦投与禁忌。第1世代クロルフェニラミンは比較的安全。",
    ]),
    ("※", "成分の落とし穴・過量服薬", "長期連用・依存・過量服薬の疑い", [
        "ウレイド系(ブロモバレリル尿素等)：長期乱用⇒臭素蓄積で歩行困難・幻覚(高齢者はせん妄も)。",
        "MOH：複合鎮痛薬を月10日超×3ヶ月超服用⇒薬剤乱用頭痛に進展。",
        "過量服薬：初日=急性心毒性、3日目以降=劇症肝不全(AAP)。AAPは無症状のまま進行。",
    ]),
    ("※", "外用薬・アンナカ", "外用薬/無水カフェインの質問", [
        "対象外：軟膏・クリーム・目薬等の外用剤(成分含有でも規制対象外)。",
        "対象外：トローチ・のど飴も「口腔内用剤」のため対象外。",
        "対象外：アンナカ(無水カフェイン)。お茶等にも含有、一律規制が非現実的。",
    ]),
]

# 運転回避目安：成分名を短縮し、半減期→回避目安の1行3列を最小文言で表示
DRIVING_ROWS = [
    ("クロルフェニラミン(1)", "12〜24h", "翌日まで"),
    ("プロメタジン(1)", "10〜14h", "12〜24h"),
    ("ブロモバレリル尿素", "約15h", "翌日まで"),
    ("ジフェンヒドラミン(1)", "約9h", "当日NG"),
    ("セチリジン(2)", "7〜10h", "当日NG"),
    ("ベポタスチン(2)", "約2.4h", "当日禁止"),
    ("アゼラスチン(2)", "約24h", "当日禁止"),
    ("ブチルスコポラミン(抗コ)", "約1.5h", "5〜6h控"),
    ("dl-メチルエフェドリン", "約5〜6h", "8〜12h"),
    ("デキストロメトルファン", "約3.5h", "6〜8h"),
]

NURSING_ROWS = [
    (GREEN, "circle", "通常授乳可", "AAP/イブプロフェン/無水カフェイン(通常量)"),
    (ORANGE, "circle", "服薬後2-4h回避", "DXM/ジフェンヒドラミン(短期)"),
    (RED, "circle", "搾乳破棄(半減期×3-4h)", "クロルフェニラミン(長期)/プロメタジン/ブロモバレリル尿素"),
    (DARKRED, "square", "代替薬へ変更", "コデイン/ジヒドロコデイン(乳児モルヒネ代謝リスク)"),
]


def draw_driving_table(x, y, w, rows, fs_tag, fs_tbl, line_h):
    tag = "※運転"
    tag_w = text_width(tag, fs_tag, "bold") + 1.2
    tag_h = line_h * 0.92
    ax.add_patch(patches.FancyBboxPatch((x, y - tag_h / 2), tag_w, tag_h, boxstyle="round,pad=0.05",
                                         linewidth=0.6, edgecolor=BLUE, facecolor=BLUE, zorder=2))
    ax.text(x + tag_w / 2, y, tag, fontsize=fs_tag, fontweight="bold", ha="center", va="center", color="white", zorder=3)
    ax.text(x + tag_w + 0.9, y, "運転前後の服用を心配されたら(半減期の長い成分ほど翌日に持ち越しやすい)",
            fontsize=fs_tag - 0.3, fontweight="bold", ha="left", va="center", color="#222222")
    y -= line_h
    tbl_lh = line_h * 0.82
    col1_x, col2_x, col3_x = x + 0.3, x + w * 0.52, x + w * 0.76
    ax.text(col1_x, y, "成分(世代)", fontsize=fs_tbl, fontweight="bold", ha="left", va="center", color=GRAY)
    ax.text(col2_x, y, "半減期", fontsize=fs_tbl, fontweight="bold", ha="left", va="center", color=GRAY)
    ax.text(col3_x, y, "⇒回避目安", fontsize=fs_tbl, fontweight="bold", ha="left", va="center", color=GRAY)
    y -= tbl_lh
    ax.hlines(y + tbl_lh * 0.55, x + 0.3, x + w - 0.3, colors="#dddddd", linewidth=0.5)
    for name, half, avoid in rows:
        ax.text(col1_x, y, name, fontsize=fs_tbl, ha="left", va="center", color="#333333")
        ax.text(col2_x, y, half, fontsize=fs_tbl, ha="left", va="center", color="#666666")
        ax.text(col3_x, y, avoid, fontsize=fs_tbl, fontweight="bold", ha="left", va="center", color=RED)
        y -= tbl_lh
    y -= 0.12
    ax.hlines(y, x, x + w, colors="#cccccc", linewidth=0.6)
    return y - 0.3


def draw_nursing(x, y, w, rows, fs_tag, fs_body, line_h):
    ax.text(x, y, "授乳婦指導(成分別の目安)：", fontsize=fs_tag - 0.2, fontstyle="italic", ha="left", va="center", color=GRAY)
    y -= line_h
    for mcolor, mshape, tag, ingr in rows:
        msize = 0.24
        if mshape == "circle":
            ax.add_patch(patches.Circle((x + 0.3, y), msize, facecolor=mcolor, edgecolor="black", linewidth=0.3, zorder=3))
        else:
            ax.add_patch(patches.Rectangle((x + 0.06, y - msize), msize * 2, msize * 2,
                                            facecolor=mcolor, edgecolor="black", linewidth=0.3, zorder=3))
        wrapped = wrap_to_width(f"{ingr}⇒{tag}", fs_body, w - 1.3)
        for wi, wline in enumerate(wrapped):
            ax.text(x + 0.9, y, wline, fontsize=fs_body, fontweight="bold" if wi == 0 else "normal",
                    ha="left", va="center", color=mcolor if wi == 0 else "#333333")
            y -= line_h
    return y


HEADER_H = 2.5
DISCLAIMER_FS = 3.6


def render_q4(fs_tag, fs_body, fs_tbl, line_h):
    """④パネル全体を指定フォントサイズで描画し、最終y座標（下端）を返す。"""
    y = Q4_TOP - HEADER_H - line_h * 0.9
    for q_num, category, condition, bullets in CASES:
        y = draw_case(Q4_X + 0.6, y, Q4_W - 1.2, q_num, category, condition, bullets, fs_tag, fs_body, line_h)
    y = draw_driving_table(Q4_X + 0.6, y, Q4_W - 1.2, DRIVING_ROWS, fs_tag, fs_tbl, line_h)
    y = draw_nursing(Q4_X + 0.6, y, Q4_W - 1.2, NURSING_ROWS, fs_tag, fs_body, line_h)
    return y


# --- 内容量から文字サイズを自動算出（1/4スペースでも改行が破綻しないよう先に高さを測る） ---
_dry_fig, _dry_ax = plt.subplots(figsize=(10, 14.14))
_dry_ax.set_xlim(0, LOGICAL_W)
_dry_ax.set_ylim(0, LOGICAL_H)
_dry_ax.axis("off")

_real_ax = ax
ax = _dry_ax
BASE_TAG, BASE_BODY, BASE_TBL, BASE_LH = 5.4, 4.8, 4.0, 1.0
avail_h = Q4_TOP - HEADER_H - (Q4_TOP - Q4_H) - 0.4

# フォントを大きくするほど折り返し行数が非線形に増えるため、単純な線形外挿ではなく
# 実際に描画してみて収まるサイズを二分探索で求める（改行が破綻しないことを実測で保証）。
lo, hi = 0.62, 1.4
for _ in range(14):
    mid = (lo + hi) / 2
    _dry_ax.cla()
    _dry_ax.axis("off")
    probe_end = render_q4(BASE_TAG * mid, BASE_BODY * mid, BASE_TBL * mid, BASE_LH * mid)
    needed_h = (Q4_TOP - HEADER_H) - probe_end
    if needed_h <= avail_h:
        lo = mid
    else:
        hi = mid
SCALE = lo
ax = _real_ax
_dry_fig.clf()

FS_TAG, FS_BODY, FS_TBL, LINE_H = BASE_TAG * SCALE, BASE_BODY * SCALE, BASE_TBL * SCALE, BASE_LH * SCALE

# --- ④パネル枠とヘッダー（内容量に合わせたQ4_Hで確定） ---
ax.add_patch(patches.FancyBboxPatch((Q4_X, Q4_TOP - Q4_H), Q4_W, Q4_H,
                                     boxstyle="round,pad=0.12", linewidth=1.3, edgecolor=RED, facecolor="#fffbfb", zorder=0))
ax.add_patch(patches.FancyBboxPatch((Q4_X, Q4_TOP - HEADER_H), Q4_W, HEADER_H,
                                     boxstyle="round,pad=0.12", linewidth=0, facecolor=RED, zorder=1))
ax.text(Q4_X + Q4_W / 2, Q4_TOP - HEADER_H / 2, "④ 状況別対応のポイント", fontsize=6.4, fontweight="bold",
        ha="center", va="center", color="white", zorder=3)

q4_end = render_q4(FS_TAG, FS_BODY, FS_TBL, LINE_H)
ax.text(Q4_X + Q4_W / 2, Q4_TOP - Q4_H + 0.55,
        "※現場で遭遇しやすい主要な注意点の抜粋。全てを網羅するものではありません。",
        fontsize=DISCLAIMER_FS, fontstyle="italic", ha="center", va="center", color=GRAY, zorder=3)

# --- 下部免責・出典 ---
ax.text(LOGICAL_W / 2, 1.9, "※本マニュアルは一次的対応の目安であり、個別の診断を行うものではありません。最終判断は薬剤師・登録販売者の専門的知見に基づき実施してください。",
        fontsize=5.0, ha="center", va="center", color=GRAY)
ax.text(LOGICAL_W / 2, 0.9,
        "準拠: 厚生労働省 局長通知「指定濫用防止医薬品の指定について」/JSMI「指定濫用防止医薬品の販売制度について」/兵庫県 薬務課 制度改正資料",
        fontsize=4.0, ha="center", va="center", color="#aaaaaa")

fig.savefig(OUTPUT_PNG, dpi=300)
plt.close(fig)
plt.close(_meas_fig)
print(f"v12【裏面】出力完了: {OUTPUT_PNG}")
print(f"4分割グリッド: COL_W={COL_W:.2f} ROW_H={ROW_H:.2f}")
print(f"④文字スケール: {SCALE:.3f} (fs_tag={FS_TAG:.2f} fs_body={FS_BODY:.2f} fs_tbl={FS_TBL:.2f})")
print(f"④最終y: {q4_end:.2f}  枠下端: {Q4_TOP - Q4_H:.2f}  余白: {q4_end - (Q4_TOP - Q4_H):.2f}")
