import matplotlib.pyplot as plt
import matplotlib.patches as patches
import japanize_matplotlib

OUTPUT_PNG = "atomic_card_table_v11_back.png"

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
# 同じ fig 上で毎回 fig.canvas.draw() すると、それまでに配置した全テキストを
# 毎回再描画するため要素数が増えるほど遅くなる(O(n^2))。専用の軽量 figure で
# 測定することで、本体の描画量に関係なく高速に保つ。
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
    """1文字ずつ幅を測りながら折り返す（フォールバック用）"""
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
    """句読点等の直後を優先的な改行位置とし、意味のまとまりで行分割する。
    「。」だけが次行に孤立する等の不自然な折り返しを避けるため、1文字単位ではなく
    句読点区切りのトークン単位で貪欲に詰める（トークル自体が幅を超える場合のみ
    文字単位にフォールバック）。"""
    tokens, cur_token = [], ""
    for ch in text:
        cur_token += ch
        if ch in "。、）":
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

    # 「）」の直後に「。」が続く場合など、句読点だけの短い行が孤立することがあるため、
    # そのような行は前の行へ統合する。
    merged = []
    for line in final_lines:
        if merged and len(line) <= 2 and all(c in "。、）" for c in line):
            merged[-1] += line
        else:
            merged.append(line)
    return merged


# --- 上部余白（約10cm）。物理A4縦(297mm)に対する比率で確保 ---
TOP_BLANK_MM = 100.0
TOP_BLANK_UNITS = LOGICAL_H * (TOP_BLANK_MM / 297.0)
content_top = LOGICAL_H - TOP_BLANK_UNITS

ax.text(LOGICAL_W / 2, content_top - 1.3, "【裏面】指定濫用防止医薬品 参考資料集", fontsize=13, fontweight="bold",
        ha="center", va="center", color="#333333")
ax.text(LOGICAL_W / 2, content_top - 3.0, "（厚労省・薬局配布資料の要点を再構成　／　下段＝状況別対応のポイント）",
        fontsize=6.4, ha="center", va="center", color="#888888")
ax.hlines(content_top - 4.1, 2.0, 98.0, colors="#999999", linewidth=1.2)

GRID_LEFT, GRID_RIGHT = 2.0, 98.0
GRID_TOP = content_top - 5.0
GRID_BOTTOM = 3.0
GUTTER = 2.0


def panel_frame(x, y_top, w, h, title, color, subtitle=None):
    """イラスト無し・テキストのみのパネル枠。色付きタイトルバー＋元資料名の副題（任意）。"""
    y_bottom = y_top - h
    ax.add_patch(patches.FancyBboxPatch((x, y_bottom), w, h, boxstyle="round,pad=0.12",
                                         linewidth=1.2, edgecolor=color, facecolor="white", zorder=1))
    sub_fs = 4.0
    sub_lines = wrap_to_width(subtitle, sub_fs, w - 2.0) if subtitle else []
    bar_h = 2.3 + (0.85 * len(sub_lines) if sub_lines else 0)
    ax.add_patch(patches.FancyBboxPatch((x, y_top - bar_h), w, bar_h, boxstyle="round,pad=0.12",
                                         linewidth=0, facecolor=color, zorder=2))
    title_y = y_top - (1.15 if sub_lines else bar_h / 2)
    ax.text(x + w / 2, title_y, title, fontsize=6.6, fontweight="bold",
            ha="center", va="center", color="white", zorder=3)
    sy = title_y - 1.05
    for line in sub_lines:
        ax.text(x + w / 2, sy, line, fontsize=sub_fs, ha="center", va="center", color="#eef4fb", zorder=3)
        sy -= 0.85
    return y_top - bar_h - 0.9


# ==========================================================
# 参考① 購入者への掲示例（イラスト・ロゴを省き、文章構成のみ再現）
# ==========================================================
def draw_poster1(x, y_top, w, h):
    fs_h, fs_b, fs_s = 5.4, 4.7, 4.3
    lh = 1.0
    y = panel_frame(x, y_top, w, h, "参考① 購入者への掲示例", BLUE,
                     subtitle="元資料：指定濫用防止医薬品をご購入時フリップ")

    for line in wrap_to_width("指定濫用防止医薬品の濫用をした場合、保健衛生上の危害が発生するおそれがあります。", fs_h, w - 2.0):
        ax.text(x + 1.0, y, line, fontsize=fs_h, fontweight="bold", ha="left", va="center", color=RED)
        y -= lh
    y -= 0.3

    for line in wrap_to_width("販売にあたり、OTC医薬品の各区分で確認する事項に加え、以下を確認させていただきます。", fs_b, w - 2.0):
        ax.text(x + 1.0, y, line, fontsize=fs_b, ha="left", va="center", color="#333333")
        y -= lh
    y -= 0.5
    # ※「18歳未満は複数個/大容量不可」の赤枠は表面①と重複するため削除し、
    #   この掲示物特有の法的根拠一覧（チェックリスト）に絞る。

    ax.text(x + 1.0, y, "＜確認事項＞", fontsize=fs_b, fontweight="bold", ha="left", va="center", color=GRAY)
    y -= lh
    checklist = ["年齢", "18歳未満の場合は当該者の氏名", "他の薬剤・医薬品の使用状況",
                 "当該製品/他の指定濫用防止医薬品の購入・譲り受け状況", "大容量・複数個購入の場合、その理由",
                 "適正な使用であることを確認するために必要な事項", "その他、情報提供に必要な事項"]
    for item in checklist:
        for i, line in enumerate(wrap_to_width(f"□ {item}", fs_s, w - 3.0)):
            indent = x + 1.0 if i == 0 else x + 2.6
            ax.text(indent, y, line, fontsize=fs_s, ha="left", va="center", color="#333333")
            y -= 0.95
    y -= 0.3

    ax.text(x + 1.0, y, "＜情報提供内容＞", fontsize=fs_b, fontweight="bold", ha="left", va="center", color=GRAY)
    y -= lh
    for line in wrap_to_width("①名称②有効成分と分量③用法用量④効能効果⑤その他薬剤師が適正使用に必要と判断する事項",
                               fs_s, w - 2.0):
        ax.text(x + 1.0, y, line, fontsize=fs_s, ha="left", va="center", color="#333333")
        y -= 0.95
    y -= 0.3
    for line in wrap_to_width("※適正な使用を確保できないと判断した場合は販売を行いません。", fs_s, w - 2.0):
        ax.text(x + 1.0, y, line, fontsize=fs_s, ha="left", va="center", color=GRAY)
        y -= 0.95
    return y


# ==========================================================
# 参考② 制度改正のお知らせ（イラスト・写真を省き、文章構成のみ再現）
# ==========================================================
def draw_poster2(x, y_top, w, h):
    fs_h, fs_b, fs_s = 5.4, 4.7, 4.3
    lh = 1.0
    y = panel_frame(x, y_top, w, h, "参考② 制度改正のお知らせ", ORANGE,
                     subtitle="元資料：薬物濫用ポスター「大切なお知らせ」販売方法の変更")

    for line in wrap_to_width("2026.5/1から、法律で「指定濫用防止医薬品」と定められた製品は販売方法が変わります。",
                               fs_h, w - 2.0):
        ax.text(x + 1.0, y, line, fontsize=fs_h, fontweight="bold", ha="left", va="center", color=ORANGE)
        y -= lh
    for line in wrap_to_width("※市販薬の不適正使用による健康被害が報告されています。", fs_s, w - 2.0):
        ax.text(x + 1.0, y, line, fontsize=fs_s, ha="left", va="center", color=GRAY)
        y -= 0.95
    y -= 0.3

    box_h = 1.9
    ax.add_patch(patches.FancyBboxPatch((x + 0.8, y - box_h), w - 1.6, box_h, boxstyle="round,pad=0.1",
                                         linewidth=1.0, edgecolor=ORANGE, facecolor="#fff3e6", zorder=2))
    ax.text(x + w / 2, y - box_h / 2, "購入時に確認・説明があります（原則、使用者本人への販売）",
            fontsize=fs_s, fontweight="bold", ha="center", va="center", color=ORANGE, zorder=3)
    y -= box_h + 0.7

    # ※確認項目1〜4の詳細(年齢・重複・理由確認等)は表面の必須質問①〜⑤と重複するため、
    #   見出しのみの1行要約に圧縮する。
    ax.text(x + 1.0, y, "確認の流れ：①購入数→②年齢確認→③使用状況→④販売可否",
            fontsize=fs_b, fontweight="bold", ha="left", va="center", color=ORANGE)
    y -= lh
    for line in wrap_to_width("（詳細は表面「レジでの必須確認事項」を参照）", fs_s, w - 2.0):
        ax.text(x + 1.0, y, line, fontsize=fs_s, ha="left", va="center", color=GRAY)
        y -= 0.9
    y -= 0.4

    for line in wrap_to_width("対象商品には「要確認」等の表示がある場合があります（不明な点は薬剤師・登録販売者へ）。",
                               fs_s, w - 2.0):
        ax.text(x + 1.0, y, line, fontsize=fs_s, ha="left", va="center", color=GRAY)
        y -= 0.9
    y -= 0.3
    ax.text(x + 1.0, y, "＜対象8成分＞", fontsize=fs_s, fontweight="bold", ha="left", va="center", color=GRAY)
    y -= 0.9
    for line in wrap_to_width("エフェドリン/コデイン/ジヒドロコデイン/ジフェンヒドラミン/デキストロメトルファン/"
                               "プソイドエフェドリン/ブロムワレリル尿素/メチルエフェドリン", fs_s, w - 2.0):
        ax.text(x + 1.0, y, line, fontsize=fs_s, ha="left", va="center", color="#333333")
        y -= 0.9
    return y


# ==========================================================
# 参考③ 来店〜販売可否フロー（簡略版・箱＋矢印で骨格のみ再現）
# ==========================================================
def draw_poster3_flow(x, y_top, w, h):
    y = panel_frame(x, y_top, w, h, "参考③ 来店〜販売可否フロー", GREEN,
                     subtitle="元資料：「販売可否判断フローチャート」OTCマニュアル(第2版)")
    fs = 4.5
    nodes = [
        ["来店・購入の意思表示", "（陳列品を持参／声かけ）"],
        ["購入者の様子を確認", "（年齢確認が必要そうか等）"],
        ["年齢確認（身分証等）", "18歳未満／18歳以上で分岐"],
        ["確認・情報提供", "（詳細は表面フローを参照）"],
        ["販売の可否判断", "（説明の理解度・懸念の有無等）"],
        ["販売せず／販売実施", "懸念があれば理由等を記録・申し送り"],
    ]
    box_w = w - 4.0
    lh = 0.92
    for i, lines in enumerate(nodes):
        box_h = 0.7 + lh * len(lines)
        ax.add_patch(patches.FancyBboxPatch((x + 2.0, y - box_h), box_w, box_h, boxstyle="round,pad=0.1",
                                             linewidth=1.0, edgecolor=GREEN, facecolor="#eaf5ea", zorder=2))
        ly = y - 0.55
        for line in lines:
            for wline in wrap_to_width(line, fs, box_w - 1.2):
                ax.text(x + w / 2, ly, wline, fontsize=fs, ha="center", va="center", color="#2e5e2e", zorder=3)
                ly -= lh
        y -= box_h
        if i < len(nodes) - 1:
            y -= 0.5
            ax.annotate("", xy=(x + w / 2, y), xytext=(x + w / 2, y + 0.5),
                        arrowprops=dict(arrowstyle="-|>", color="#7a9d7a", lw=1.1))
            y -= 0.1
    return y


COL_W3 = (GRID_RIGHT - GRID_LEFT - 2 * GUTTER) / 3
P1_X = GRID_LEFT
P2_X = GRID_LEFT + COL_W3 + GUTTER
P3_X = GRID_LEFT + 2 * (COL_W3 + GUTTER)

# 各パネルの実際の内容量に合わせて枠の高さを決める（固定高だと中に無駄な余白が残るため）。
# パネル内のコンテンツ位置は panel_frame の h に依存しないので、まず使い捨ての
# scratch axes に描いて必要な高さだけを測り、そのあと本番の ax に正しい高さで描き直す。
_dry_fig, _dry_ax = plt.subplots(figsize=(10, 14.14))
_dry_ax.set_xlim(0, LOGICAL_W)
_dry_ax.set_ylim(0, LOGICAL_H)
_dry_ax.axis("off")

_PAD_BOTTOM = 1.0


def _measure_and_draw(draw_fn, x, w):
    global ax
    real_ax = ax
    ax = _dry_ax
    probe_end = draw_fn(x, GRID_TOP, w, 999)
    ax = real_ax
    _dry_ax.cla()
    _dry_ax.axis("off")
    needed_h = (GRID_TOP - probe_end) + _PAD_BOTTOM
    return draw_fn(x, GRID_TOP, w, needed_h)


end1 = _measure_and_draw(draw_poster1, P1_X, COL_W3)
end2 = _measure_and_draw(draw_poster2, P2_X, COL_W3)
end3 = _measure_and_draw(draw_poster3_flow, P3_X, COL_W3)
plt.close(_dry_fig)
ROW1_BOTTOM = min(end1, end2, end3) - 0.6

# ==========================================================
# ④ 状況別対応のポイント（キーワード先頭・情報量を落とさず密に配置）
# 余った縦スペースを使ってフォントを拡大し、枠は実際の分量に合わせて後から
# ぴったりのサイズで描く（無駄な余白を残さないため）。
# ==========================================================
FONT_SCALE = 1.35
TITLE_FS, BODY_FS, LINE_H = 6.0 * FONT_SCALE, 5.3 * FONT_SCALE, 1.06 * FONT_SCALE

header_h = 2.6

CONTENT_LEFT = GRID_LEFT + 1.4
CONTENT_W_FULL = GRID_RIGHT - GRID_LEFT - 2.8
Q_COL_GUTTER = 3.0
Q_COL_W = (CONTENT_W_FULL - Q_COL_GUTTER) / 2
QA_X = CONTENT_LEFT
QB_X = CONTENT_LEFT + Q_COL_W + Q_COL_GUTTER
cy_top = ROW1_BOTTOM - header_h - 2.3


def draw_dense_case(x, y, w, q_num, category, condition, bullets):
    """カテゴリを色付きバッジで強調し、条件文・弾丸を列挙。末尾に薄い罫線で区切る。"""
    tag = f"{q_num}{category}"
    tag_w = text_width(tag, TITLE_FS, "bold") + 1.4
    tag_h = LINE_H * 0.95
    ax.add_patch(patches.FancyBboxPatch((x, y - tag_h / 2), tag_w, tag_h, boxstyle="round,pad=0.06",
                                         linewidth=0, facecolor=BLUE, zorder=2))
    ax.text(x + tag_w / 2, y, tag, fontsize=TITLE_FS, fontweight="bold", ha="center", va="center",
            color="white", zorder=3)

    cond_x = x + tag_w + 1.0
    wrapped_cond = wrap_to_width(condition, TITLE_FS, w - tag_w - 1.0)
    if wrapped_cond:
        ax.text(cond_x, y, wrapped_cond[0], fontsize=TITLE_FS, fontweight="bold", ha="left", va="center", color="#222222")
    y -= LINE_H
    for line in wrapped_cond[1:]:
        ax.text(x, y, line, fontsize=TITLE_FS, fontweight="bold", ha="left", va="center", color="#222222")
        y -= LINE_H

    for bullet in bullets:
        bullet = bullet.replace("→", "⇒")  # 行動指示の矢印を強調（➡は和文フォントで欠字するため⇒を使用）
        is_alert = ("禁忌" in bullet) or ("一律" in bullet) or ("不可" in bullet)
        color = RED if is_alert else "#333333"
        weight = "bold" if is_alert else "normal"
        wrapped = wrap_to_width(bullet, BODY_FS, w - 1.0)
        for wi, wline in enumerate(wrapped):
            indent = x + 1.0 if wi == 0 else x + 2.2
            ax.text(indent, y, wline, fontsize=BODY_FS, ha="left", va="center", color=color, fontweight=weight)
            y -= LINE_H
    y -= 0.15
    ax.hlines(y, x, x + w, colors="#e8b8b8", linewidth=0.6)
    return y - 0.35


CASES_A = [
    ("①②", "年齢・重複", "18歳未満/複数個(他店合算)を希望", [
        "▶一律禁止：18歳未満への大容量・複数個(種類違い含む)は理由問わず販売不可。家族用でも例外なし。",
        "▶絶対禁忌：12歳未満はコデイン系(ジヒドロコデイン含む)。処方・市販とも不可、他成分の咳止めへ。",
        "▶身分証拒否：年齢確認不能のため販売不可。",
    ]),
    ("③", "体質(アレルギー)", "解熱鎮痛薬でアレルギー歴", [
        "▶ピリン疹：NSAIDs（ロキソプロフェン等）へ代替可。",
        "▶アスピリン喘息：NSAIDs全般に100%交差耐性で全てNG→AAP単剤のみ提案。",
    ]),
    ("③", "体質(喘息・不整脈等)", "喘息/不整脈/緑内障/前立腺肥大/高血圧・糖尿病等", [
        "▶抗コリン薬・第一世代抗ヒスタミン：喘息=痰粘稠化・排痰困難、不整脈=頻脈・QT延長。",
        "▶緑内障=眼圧上昇、前立腺肥大=尿閉リスク。単一成分薬を推奨。",
        "▶禁忌・要注意：プソイドエフェドリンは交感神経刺激作用が強く、前立腺肥大・緑内障に加え高血圧症・心疾患(不整脈/虚血性心疾患)・糖尿病・甲状腺機能亢進症も対象（抗コリン作用とは別ルート）。",
    ]),
    ("④", "併用", "SSRI服用中/他剤併用", [
        "▶最重要：DXM×SSRIはセロトニン症候群リスク（濫用防止領域で最も急性致死率が高い相互作用）。",
        "▶GFJはDXM血中濃度上昇。マクロライド系/アゾール系薬はQT延長・心室頻拍に注意。",
    ]),
]

CASES_B = [
    ("⑤", "妊婦・授乳", "妊娠中/授乳中と判明", [
        "▶禁忌：妊娠後期のコデイン系（パブロン/ルル等）は新生児呼吸抑制→メジコン等単剤(DXM)を提案。",
        "▶一律禁忌：抗コリン薬（ブスコパン等）はOTCで一律不可（処方箋なら有益性投与可）。授乳中は母乳分泌低下・乳児頻脈で中断。",
        "▶禁忌：コンタック鼻炎Z(セチリジン/第2世代)は動物実験で胎児毒性報告あり添付文書上「妊婦投与禁忌」。第1世代クロルフェニラミンは比較的安全。",
    ]),
    ("※", "成分の落とし穴・過量服薬", "長期連用・依存・過量服薬の疑い", [
        "▶ウレイド系（ブロモバレリル尿素等）：長期乱用で臭素蓄積→歩行困難・幻覚。高齢者はせん妄・認知低下も。",
        "▶MOH：月15日以上頭痛の環境で複合鎮痛薬を月10日超・3ヶ月超服用→薬剤乱用頭痛に進展。",
        "▶過量服薬：初日=急性心毒性(無水カフェイン等)、3日目以降=劇症肝不全(AAP)が急速進行。NSAIDsは自覚症状ありだがAAPは無症状のまま進行。",
    ]),
    ("※", "外用薬・アンナカ", "外用薬/無水カフェインの質問", [
        "▶対象外：軟膏・クリーム・目薬等の外用剤は成分含有でも規制対象外。",
        "▶対象外：アンナカ(無水カフェイン)はお茶・コーヒー等にも含まれ一律規制が非現実的（危険性は認識）。",
    ]),
]

DRIVING_ROWS = [
    ("クロルフェニラミン(第1)", "24h(翌日まで)", "12〜24h"),
    ("プロメタジン(第1)", "12〜24h", "10〜14h"),
    ("ブロモバレリル尿素", "24h(翌日まで)", "約15h"),
    ("ジフェンヒドラミン(第1)", "12h(当日NG)", "約9h"),
    ("セチリジン(第2)", "当日NG", "7〜10h"),
    ("ベポタスチン(第2)", "当日中禁止", "約2.4h"),
    ("アゼラスチン(第2)", "当日中禁止", "約24h"),
    ("ブチルスコポラミン(抗コリン)", "5〜6h(当日中控)", "約1.5h"),
    ("dl-メチルエフェドリン", "8〜12h", "約5〜6h"),
    ("デキストロメトルファン", "6〜8h", "約3.5h"),
]


def draw_driving_table(x, y, w, rows):
    """運転回避目安を表形式で密に列挙（プロース箇条書きより省スペース）。"""
    tag = "※運転"
    tag_w = text_width(tag, TITLE_FS, "bold") + 1.4
    tag_h = LINE_H * 0.95
    ax.add_patch(patches.FancyBboxPatch((x, y - tag_h / 2), tag_w, tag_h, boxstyle="round,pad=0.06",
                                         linewidth=0, facecolor=BLUE, zorder=2))
    ax.text(x + tag_w / 2, y, tag, fontsize=TITLE_FS, fontweight="bold", ha="center", va="center",
            color="white", zorder=3)
    cond_x = x + tag_w + 1.0
    wrapped_cond = wrap_to_width("運転前後の服用を心配されたら", TITLE_FS, w - tag_w - 1.0)
    if wrapped_cond:
        ax.text(cond_x, y, wrapped_cond[0], fontsize=TITLE_FS, fontweight="bold", ha="left", va="center", color="#222222")
    y -= LINE_H
    for line in wrapped_cond[1:]:
        ax.text(x, y, line, fontsize=TITLE_FS, fontweight="bold", ha="left", va="center", color="#222222")
        y -= LINE_H
    ax.text(x + 1.0, y, "▶最も排泄が遅い成分を基準に判断（半減期の長い成分ほど翌日に持ち越しやすい）",
            fontsize=BODY_FS - 0.3, ha="left", va="center", color="#333333")
    y -= LINE_H * 0.95
    tbl_fs = 4.5 * FONT_SCALE
    tbl_lh = 0.88 * FONT_SCALE
    # 「半減期→回避目安」の因果関係が伝わるよう、半減期を先に置く
    col1_x, col2_x, col3_x = x + 1.0, x + w * 0.46, x + w * 0.68
    ax.text(col1_x, y, "成分（世代/分類）", fontsize=tbl_fs, fontweight="bold", ha="left", va="center", color=GRAY)
    ax.text(col2_x, y, "半減期", fontsize=tbl_fs, fontweight="bold", ha="left", va="center", color=GRAY)
    ax.text(col3_x, y, "⇒ 回避目安", fontsize=tbl_fs, fontweight="bold", ha="left", va="center", color=GRAY)
    y -= tbl_lh
    ax.hlines(y + tbl_lh * 0.55, x + 1.0, x + w - 1.0, colors="#dddddd", linewidth=0.5)
    for name, avoid, half in rows:
        ax.text(col1_x, y, name, fontsize=tbl_fs, ha="left", va="center", color="#333333")
        ax.text(col2_x, y, half, fontsize=tbl_fs, ha="left", va="center", color="#666666")
        ax.text(col3_x, y, avoid, fontsize=tbl_fs, fontweight="bold", ha="left", va="center", color=RED)
        y -= tbl_lh
    y -= 0.15
    ax.hlines(y, x, x + w, colors="#e8b8b8", linewidth=0.6)
    return y - 0.35


def draw_nursing(x, y, w):
    ax.text(x, y, "授乳婦指導（成分別の目安）:", fontsize=5.5, fontstyle="italic", ha="left", va="center", color=GRAY)
    y -= LINE_H
    nursing_rows = [
        (GREEN, "circle", "通常授乳可", "AAP/イブプロフェン/無水カフェイン(通常量)"),
        (ORANGE, "circle", "服薬後2-4h授乳回避", "DXM/ジフェンヒドラミン(短期)"),
        (RED, "circle", "搾乳破棄(半減期×3-4h)", "クロルフェニラミン(長期)/プロメタジン/ブロモバレリル尿素"),
        (DARKRED, "square", "代替薬へ変更提案", "コデイン/ジヒドロコデイン(乳児モルヒネ代謝リスク)"),
    ]
    for mcolor, mshape, tag, ingr in nursing_rows:
        if mshape == "circle":
            ax.add_patch(patches.Circle((x + 0.35, y), 0.3, facecolor=mcolor, edgecolor="none", zorder=3))
        else:
            ax.add_patch(patches.Rectangle((x + 0.05, y - 0.3), 0.6, 0.6, facecolor=mcolor, edgecolor="none", zorder=3))
        wrapped = wrap_to_width(f"{ingr} ⇒ {tag}", BODY_FS, w - 1.6)
        for wi, wline in enumerate(wrapped):
            ax.text(x + 1.0, y, wline, fontsize=BODY_FS, fontweight="bold" if wi == 0 else "normal",
                    ha="left", va="center", color=mcolor if wi == 0 else "#333333")
            y -= LINE_H
    return y


cyA = cy_top
for q_num, category, condition, bullets in CASES_A:
    cyA = draw_dense_case(QA_X, cyA, Q_COL_W, q_num, category, condition, bullets)
cyA = draw_driving_table(QA_X, cyA, Q_COL_W, DRIVING_ROWS)

cyB = cy_top
for q_num, category, condition, bullets in CASES_B:
    cyB = draw_dense_case(QB_X, cyB, Q_COL_W, q_num, category, condition, bullets)
cyB = draw_nursing(QB_X, cyB, Q_COL_W)

q4_end = min(cyA, cyB)

# 内容量に合わせて枠を後から描く（zorderで文字の背面に回す）
Q4_BOTTOM = q4_end - 1.1
ax.add_patch(patches.FancyBboxPatch((GRID_LEFT, Q4_BOTTOM), GRID_RIGHT - GRID_LEFT, ROW1_BOTTOM - Q4_BOTTOM,
                                     boxstyle="round,pad=0.15", linewidth=1.3, edgecolor=RED, facecolor="#fffbfb", zorder=0))
ax.add_patch(patches.FancyBboxPatch((GRID_LEFT, ROW1_BOTTOM - header_h), GRID_RIGHT - GRID_LEFT, header_h,
                                     boxstyle="round,pad=0.15", linewidth=0, facecolor=RED, zorder=0.5))
ax.text(LOGICAL_W / 2, ROW1_BOTTOM - header_h / 2, "④ 状況別対応のポイント", fontsize=8.4, fontweight="bold",
        ha="center", va="center", color="white", zorder=3)
ax.text(LOGICAL_W / 2, ROW1_BOTTOM - header_h - 1.0,
        "※現場で遭遇しやすい主要な注意点の抜粋です。全てを網羅するものではありません。",
        fontsize=5.4, fontstyle="italic", ha="center", va="center", color=GRAY, zorder=3)

# --- 下部免責・出典 ---
ax.text(LOGICAL_W / 2, 1.9, "※本マニュアルは一次的対応の目安であり、個別の診断を行うものではありません。最終判断は薬剤師・登録販売者の専門的知見に基づき実施してください。",
        fontsize=5.2, ha="center", va="center", color=GRAY)
ax.text(LOGICAL_W / 2, 0.9,
        "準拠: 厚生労働省 局長通知「指定濫用防止医薬品の指定について」/JSMI「指定濫用防止医薬品の販売制度について」/兵庫県 薬務課 制度改正資料",
        fontsize=4.2, ha="center", va="center", color="#aaaaaa")

fig.savefig(OUTPUT_PNG, dpi=300)
plt.close(fig)
plt.close(_meas_fig)
print(f"v11【裏面】出力完了: {OUTPUT_PNG}")
print(f"上部余白: {TOP_BLANK_UNITS:.2f}units(={TOP_BLANK_MM}mm) / poster row bottom: {ROW1_BOTTOM:.2f}")
print(f"Q4列A最終y: {cyA:.2f}  Q4列B最終y: {cyB:.2f}  下限{GRID_BOTTOM:.2f}付近が理想  余白: {q4_end - GRID_BOTTOM:.2f}")
