import matplotlib.pyplot as plt
import matplotlib.patches as patches
import japanize_matplotlib

OUTPUT_PNG = "atomic_card_table_v13_page2.png"

LOGICAL_W, LOGICAL_H = 100.0, 141.4
fig, ax = plt.subplots(figsize=(10, 14.14))
ax.set_position([0, 0, 1, 1])
ax.set_xlim(0, LOGICAL_W)
ax.set_ylim(0, LOGICAL_H)
ax.axis("off")
fig.canvas.draw()

BLUE, RED, ORANGE, GREEN, GRAY, DARKRED = "#1565c0", "#d32f2f", "#e65100", "#2e7d32", "#555555", "#8e0000"
INK = "#1a1a1a"
LGRAY = "#888888"

_meas_fig, _meas_ax = plt.subplots(figsize=(10, 14.14))
_meas_ax.set_xlim(0, LOGICAL_W)
_meas_ax.set_ylim(0, LOGICAL_H)
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


COL_NAME_X = 2.0

# --- タイトル ---
ax.text(LOGICAL_W / 2, LOGICAL_H - 2.4, "【2枚目】販売判断の表現案", fontsize=14, fontweight="bold",
        ha="center", va="center", color="#222222")
ax.text(LOGICAL_W / 2, LOGICAL_H - 4.1, "（上段＝レジでの確認事項　／　下段＝状況別対応のポイント）",
        fontsize=6.6, ha="center", va="center", color="#777777")
ax.hlines(LOGICAL_H - 5.3, 2.0, 98.0, colors="#999999", linewidth=1.2)

PAGE_TOP = LOGICAL_H - 6.3
PAGE_BOTTOM = 2.0

# ==========================================================
# 上段：④ レジでの確認事項
# ==========================================================
box_top = PAGE_TOP
box_h = 62.0
ax.add_patch(patches.FancyBboxPatch((COL_NAME_X - 0.5, box_top - box_h), LOGICAL_W - 2 * (COL_NAME_X - 0.5), box_h,
                                     boxstyle="round,pad=0.2", linewidth=1.4, edgecolor=INK, facecolor="#f7f7f7", zorder=2))
ax.add_patch(patches.FancyBboxPatch((COL_NAME_X - 0.5, box_top - 2.6), LOGICAL_W - 2 * (COL_NAME_X - 0.5), 2.6,
                                     boxstyle="round,pad=0.2", linewidth=0, facecolor=INK, zorder=2))
ax.text(LOGICAL_W / 2, box_top - 1.3, "④ レジでの確認事項　※該当する場合は下段「状況別対応のポイント」を参照",
        fontsize=10.5, fontweight="bold", ha="center", va="center", color="white", zorder=3)

qy = box_top - 6.0
Q_FS_MAIN, Q_FS_SUB, Q_LH = 12.0, 11.0, 3.85
ax.text(COL_NAME_X + 1.5, qy, "＋【使用者】今回のお薬は、どなた（ご本人様／12歳未満の小児等）が使われますか？",
        fontsize=Q_FS_SUB, fontweight="bold", ha="left", va="center", color="#222222", zorder=3)
qy -= Q_LH
ax.text(COL_NAME_X + 1.5, qy, "＋ いつから、どの程度の症状ですか？（適正な使用期間の確認、長引く場合は受診勧奨を判断します）",
        fontsize=Q_FS_SUB, ha="left", va="center", color=GRAY, zorder=3)
qy -= Q_LH
ax.text(COL_NAME_X + 1.5, qy, "＋ すでに受診・服薬を開始していますか？（重複投与や飲み合わせ確認のため）",
        fontsize=Q_FS_SUB, ha="left", va="center", color=GRAY, zorder=3)
qy -= Q_LH * 1.15
ax.text(COL_NAME_X + 1.5, qy, "①【年齢・氏名】18歳未満ですか？",
        fontsize=Q_FS_MAIN, fontweight="bold", ha="left", va="center", color="#222222", zorder=3)
qy -= Q_LH * 0.85
ax.text(COL_NAME_X + 3.0, qy, "（※18歳未満への大容量・複数個は理由問わず一律販売不可。小容量1個のみ可。氏名・年齢の記録が必須）",
        fontsize=Q_FS_SUB - 1.2, ha="left", va="center", color=GRAY, zorder=3)
qy -= Q_LH * 1.15
ax.text(COL_NAME_X + 1.5, qy, "②【重複】他店や他のレジで同じお薬（風邪薬、咳止め等）のご購入はありませんか？（譲り受けも含みます）",
        fontsize=Q_FS_MAIN, fontweight="bold", ha="left", va="center", color="#222222", zorder=3)
qy -= Q_LH * 1.15
ax.text(COL_NAME_X + 1.5, qy, "以下は、お薬の安全な選択に関わります。", fontsize=9.0, fontstyle="italic",
        ha="left", va="center", color=LGRAY, zorder=3)
qy -= Q_LH
ax.text(COL_NAME_X + 1.5, qy, "③【体質】アレルギー歴（アスピリン喘息等）や、喘息、不整脈、緑内障、前立腺肥大の持病はありますか？",
        fontsize=Q_FS_MAIN, fontweight="bold", ha="left", va="center", color="#222222", zorder=3)
qy -= Q_LH * 1.15
ax.text(COL_NAME_X + 1.5, qy, "④【併用】現在、病院で処方されたお薬や、他のお薬を飲まれていますか？（SSRI等との重複防止）",
        fontsize=Q_FS_MAIN, fontweight="bold", ha="left", va="center", color="#222222", zorder=3)
qy -= Q_LH * 1.15
ax.text(COL_NAME_X + 1.5, qy, "⑤【妊婦】妊娠中、または授乳中ではありませんか？（妊娠後期のNSAIDs禁忌、授乳中のコデイン避止）",
        fontsize=Q_FS_MAIN, fontweight="bold", ha="left", va="center", color="#222222", zorder=3)
qy -= Q_LH * 1.15
ax.text(COL_NAME_X + 1.5, qy, "＋【大容量・複数個（成人）】",
        fontsize=Q_FS_SUB, fontweight="bold", ha="left", va="center", color="#222222", zorder=3)
qy -= Q_LH * 0.85
ax.text(COL_NAME_X + 3.0, qy, "（※18歳以上であれば購入個数の制限はございませんが、ご理由を伺わなければならない厚労省の規則がございます）",
        fontsize=Q_FS_SUB - 1.2, ha="left", va="center", color=GRAY, zorder=3)
qy -= Q_LH * 1.3
ax.text(COL_NAME_X + 1.5, qy, "免責: 過去に用法用量超過の自己判断服用で重篤な健康被害が生じた事例を踏まえた確認です。意図的な過量服薬は保証・救済制度の対象外です。",
        fontsize=7.4, ha="left", va="center", color=LGRAY, zorder=3)

# ==========================================================
# 下段：④ 状況別対応のポイント（全幅を使い、文字サイズは内容量から自動算出）
# ==========================================================
SEC_TOP = box_top - box_h - 2.2
SEC_BOTTOM = PAGE_BOTTOM + 2.2
SEC_LEFT, SEC_RIGHT = COL_NAME_X, LOGICAL_W - COL_NAME_X


def draw_alert_bullet(x, y, w, text, fontsize, line_h):
    ALERT_KEYWORDS = ["禁忌", "禁止", "NG", "搾乳破棄", "回避", "家族用も例外なし", "アスピリン喘息",
                       "劇症肝不全", "OTC一律不可", "プソイドエフェドリン："]
    is_alert = any(kw in text for kw in ALERT_KEYWORDS)
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
    tag_w = text_width(tag, fs_tag, "bold") + 1.4
    tag_h = line_h * 0.92
    ax.add_patch(patches.FancyBboxPatch((x, y - tag_h / 2), tag_w, tag_h, boxstyle="round,pad=0.06",
                                         linewidth=0.7, edgecolor=INK, facecolor=INK, zorder=2))
    ax.text(x + tag_w / 2, y, tag, fontsize=fs_tag, fontweight="bold", ha="center", va="center",
            color="white", zorder=3)
    cond_x = x + tag_w + 1.0
    wrapped_cond = wrap_to_width(condition, fs_tag, w - tag_w - 1.0)
    if wrapped_cond:
        ax.text(cond_x, y, wrapped_cond[0], fontsize=fs_tag, fontweight="bold", ha="left", va="center", color="#222222")
    y -= line_h
    for line in wrapped_cond[1:]:
        ax.text(x, y, line, fontsize=fs_tag, fontweight="bold", ha="left", va="center", color="#222222")
        y -= line_h
    for bullet in bullets:
        y = draw_alert_bullet(x + 0.4, y, w, bullet, fs_body, line_h)
    y -= 0.15
    ax.hlines(y, x, x + w, colors="#cccccc", linewidth=0.7)
    return y - 0.4


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
    ("※", "強心薬(センソ含有)", "救心・六神丸等の購入/併用歴の確認", [
        "併用禁忌：センソ含有薬(救心・六神丸等)と医療用強心薬(ジゴキシン等ジギタリス製剤)は併用禁忌⇒不整脈・中毒のおそれ。",
        "妊婦は特に注意：センソ・ブシ(附子)は妊娠中の使用に注意を要する成分⇒購入前に必ず確認。",
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
    ("circle", "通常授乳可", "AAP/イブプロフェン/無水カフェイン(通常量)"),
    ("circle", "服薬後2-4h回避", "DXM/ジフェンヒドラミン(短期)"),
    ("circle", "搾乳破棄(半減期×3-4h)", "クロルフェニラミン(長期)/プロメタジン/ブロモバレリル尿素"),
    ("square", "代替薬へ変更", "コデイン/ジヒドロコデイン(乳児モルヒネ代謝リスク)"),
]


def draw_driving_table(x, y, w, rows, fs_tag, fs_tbl, line_h):
    tag = "※運転"
    tag_w = text_width(tag, fs_tag, "bold") + 1.4
    tag_h = line_h * 0.92
    ax.add_patch(patches.FancyBboxPatch((x, y - tag_h / 2), tag_w, tag_h, boxstyle="round,pad=0.06",
                                         linewidth=0.7, edgecolor=INK, facecolor=INK, zorder=2))
    ax.text(x + tag_w / 2, y, tag, fontsize=fs_tag, fontweight="bold", ha="center", va="center", color="white", zorder=3)
    ax.text(x + tag_w + 1.0, y, "運転前後の服用を心配されたら(半減期の長い成分ほど翌日に持ち越しやすい)",
            fontsize=fs_tag - 0.3, fontweight="bold", ha="left", va="center", color="#222222")
    y -= line_h
    tbl_lh = line_h * 0.85
    col1_x, col2_x, col3_x, col4_x = x + 0.4, x + w * 0.30, x + w * 0.52, x + w * 0.68
    col5_x, col6_x = x + w * 0.79, x + w * 0.90

    def is_avoid(avoid):
        return ("NG" in avoid) or ("禁止" in avoid)

    # 運転制限（当日NG/禁止）の成分を右側に縦でまとめ、一目で分かるようにする
    left_rows = [r for r in rows if not is_avoid(r[2])]
    right_rows = [r for r in rows if is_avoid(r[2])]
    ax.text(col4_x, y, "■当日は運転を避ける成分", fontsize=fs_tbl, fontweight="bold", ha="left", va="center", color=RED)
    y -= tbl_lh
    ax.text(col1_x, y, "成分(世代)", fontsize=fs_tbl, fontweight="bold", ha="left", va="center", color=GRAY)
    ax.text(col2_x, y, "半減期", fontsize=fs_tbl, fontweight="bold", ha="left", va="center", color=GRAY)
    ax.text(col3_x, y, "⇒回避目安", fontsize=fs_tbl, fontweight="bold", ha="left", va="center", color=GRAY)
    ax.text(col4_x, y, "成分(世代)", fontsize=fs_tbl, fontweight="bold", ha="left", va="center", color=GRAY)
    ax.text(col5_x, y, "半減期", fontsize=fs_tbl, fontweight="bold", ha="left", va="center", color=GRAY)
    ax.text(col6_x, y, "⇒回避目安", fontsize=fs_tbl, fontweight="bold", ha="left", va="center", color=GRAY)
    y -= tbl_lh
    ax.hlines(y + tbl_lh * 0.55, x + 0.4, x + w - 0.4, colors="#dddddd", linewidth=0.5)
    yy = y
    for name, half_life, avoid in left_rows:
        avoid_alert = ("NG" in avoid) or ("禁止" in avoid)
        ax.text(col1_x, yy, name, fontsize=fs_tbl, ha="left", va="center", color="#333333")
        ax.text(col2_x, yy, half_life, fontsize=fs_tbl, ha="left", va="center", color="#666666")
        ax.text(col3_x, yy, avoid, fontsize=fs_tbl, fontweight="bold", ha="left", va="center",
                color=RED if avoid_alert else "#222222")
        yy -= tbl_lh
    yy2 = y
    for name, half_life, avoid in right_rows:
        avoid_alert = ("NG" in avoid) or ("禁止" in avoid)
        ax.text(col4_x, yy2, name, fontsize=fs_tbl, ha="left", va="center", color="#333333")
        ax.text(col5_x, yy2, half_life, fontsize=fs_tbl, ha="left", va="center", color="#666666")
        ax.text(col6_x, yy2, avoid, fontsize=fs_tbl, fontweight="bold", ha="left", va="center",
                color=RED if avoid_alert else "#222222")
        yy2 -= tbl_lh
    y = min(yy, yy2)
    y -= 0.15
    ax.hlines(y, x, x + w, colors="#cccccc", linewidth=0.7)
    return y - 0.4


def draw_nursing(x, y, w, rows, fs_tag, fs_body, line_h):
    ax.text(x, y, "授乳婦指導(成分別の目安)：", fontsize=fs_tag - 0.2, fontstyle="italic", ha="left", va="center", color=GRAY)
    y -= line_h
    col_w = w / 2 - 1.0
    for i, (mshape, tag, ingr) in enumerate(rows):
        col = i % 2
        row = i // 2
        cx = x + col * (col_w + 2.0)
        cy = y - row * (line_h * 1.9)
        is_alert = any(kw in tag for kw in ("搾乳破棄", "回避"))
        tcolor = RED if is_alert else "#222222"
        msize = 0.28
        if mshape == "circle":
            ax.add_patch(patches.Circle((cx + 0.3, cy), msize, facecolor=tcolor, edgecolor="black", linewidth=0.3, zorder=3))
        else:
            ax.add_patch(patches.Rectangle((cx + 0.02, cy - msize), msize * 2, msize * 2,
                                            facecolor=tcolor, edgecolor="black", linewidth=0.3, zorder=3))
        wrapped = wrap_to_width(f"{ingr}⇒{tag}", fs_body, col_w - 1.3)
        for wi, wline in enumerate(wrapped):
            ax.text(cx + 1.0, cy - wi * line_h, wline, fontsize=fs_body, fontweight="bold" if wi == 0 else "normal",
                    ha="left", va="center", color=tcolor if wi == 0 else "#333333")
    n_rows = (len(rows) + 1) // 2
    return y - n_rows * (line_h * 1.9) - line_h * 0.3


SEC_HEADER_H = 3.2
DISCLAIMER_FS = 4.2


def render_section(fs_tag, fs_body, fs_tbl, line_h):
    y = SEC_TOP - SEC_HEADER_H - line_h * 0.9
    for q_num, category, condition, bullets in CASES:
        y = draw_case(SEC_LEFT + 0.8, y, SEC_RIGHT - SEC_LEFT - 1.6, q_num, category, condition, bullets, fs_tag, fs_body, line_h)
    y = draw_driving_table(SEC_LEFT + 0.8, y, SEC_RIGHT - SEC_LEFT - 1.6, DRIVING_ROWS, fs_tag, fs_tbl, line_h)
    y = draw_nursing(SEC_LEFT + 0.8, y, SEC_RIGHT - SEC_LEFT - 1.6, NURSING_ROWS, fs_tag, fs_body, line_h)
    return y


_dry_fig, _dry_ax = plt.subplots(figsize=(10, 14.14))
_dry_ax.set_xlim(0, LOGICAL_W)
_dry_ax.set_ylim(0, LOGICAL_H)
_dry_ax.axis("off")

_real_ax = ax
ax = _dry_ax
BASE_TAG, BASE_BODY, BASE_TBL, BASE_LH = 5.4, 4.8, 4.0, 1.0
avail_h = SEC_TOP - SEC_HEADER_H - SEC_BOTTOM - 0.6

lo, hi = 0.62, 2.4
for _ in range(16):
    mid = (lo + hi) / 2
    _dry_ax.cla()
    _dry_ax.axis("off")
    probe_end = render_section(BASE_TAG * mid, BASE_BODY * mid, BASE_TBL * mid, BASE_LH * mid)
    needed_h = (SEC_TOP - SEC_HEADER_H) - probe_end
    if needed_h <= avail_h:
        lo = mid
    else:
        hi = mid
SCALE = lo
ax = _real_ax
_dry_fig.clf()

FS_TAG, FS_BODY, FS_TBL, LINE_H = BASE_TAG * SCALE, BASE_BODY * SCALE, BASE_TBL * SCALE, BASE_LH * SCALE

ax.add_patch(patches.FancyBboxPatch((SEC_LEFT, SEC_BOTTOM), SEC_RIGHT - SEC_LEFT, SEC_TOP - SEC_BOTTOM,
                                     boxstyle="round,pad=0.15", linewidth=1.6, edgecolor=INK, facecolor="#fbfbfb", zorder=0))
ax.add_patch(patches.FancyBboxPatch((SEC_LEFT, SEC_TOP - SEC_HEADER_H), SEC_RIGHT - SEC_LEFT, SEC_HEADER_H,
                                     boxstyle="round,pad=0.15", linewidth=0, facecolor=INK, zorder=1))
ax.text(LOGICAL_W / 2, SEC_TOP - SEC_HEADER_H / 2, "④ 状況別対応のポイント", fontsize=10.5, fontweight="bold",
        ha="center", va="center", color="white", zorder=3)

sec_end = render_section(FS_TAG, FS_BODY, FS_TBL, LINE_H)
ax.text(LOGICAL_W / 2, SEC_BOTTOM + 0.7,
        "※現場で遭遇しやすい主要な注意点の抜粋。全てを網羅するものではありません。",
        fontsize=DISCLAIMER_FS, fontstyle="italic", ha="center", va="center", color=GRAY, zorder=3)

# --- 下部出典 ---
ax.text(LOGICAL_W / 2, 1.1,
        "準拠: 厚生労働省 局長通知「指定濫用防止医薬品の指定について」/JSMI「指定濫用防止医薬品の販売制度について」/兵庫県 薬務課 制度改正資料",
        fontsize=4.4, ha="center", va="center", color="#aaaaaa")

fig.savefig(OUTPUT_PNG, dpi=300)
plt.close(fig)
plt.close(_meas_fig)
print(f"v13【2枚目】出力完了: {OUTPUT_PNG}")
print(f"④文字スケール: {SCALE:.3f} (fs_tag={FS_TAG:.2f} fs_body={FS_BODY:.2f} fs_tbl={FS_TBL:.2f})")
print(f"④最終y: {sec_end:.2f}  枠下端: {SEC_BOTTOM:.2f}")
