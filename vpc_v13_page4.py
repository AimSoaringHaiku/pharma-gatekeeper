import matplotlib.pyplot as plt
import matplotlib.patches as patches
import japanize_matplotlib

OUTPUT_PNG = "atomic_card_table_v13_page4.png"
OUTPUT_PDF = "atomic_card_table_v13_page4.pdf"

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
ax.text(LOGICAL_W / 2, LOGICAL_H - 2.4, "【4枚目】社内限定・データ整備リファレンス", fontsize=13.5, fontweight="bold",
        ha="center", va="center", color="#222222")
ax.text(LOGICAL_W / 2, LOGICAL_H - 4.1, "（上段＝新商品採用時チェックリスト　／　下段＝剤形・医薬品区分の基礎知識）",
        fontsize=6.6, ha="center", va="center", color="#777777")
ax.hlines(LOGICAL_H - 5.3, 2.0, 98.0, colors="#999999", linewidth=1.2)

PAGE_TOP = LOGICAL_H - 6.3
PAGE_BOTTOM = 2.0

# ==========================================================
# 上段：新商品採用時チェックリスト
# ==========================================================
box_top = PAGE_TOP
box_h = 47.0
ax.add_patch(patches.FancyBboxPatch((COL_NAME_X - 0.5, box_top - box_h), LOGICAL_W - 2 * (COL_NAME_X - 0.5), box_h,
                                     boxstyle="round,pad=0.2", linewidth=1.4, edgecolor=INK, facecolor="#f7f7f7", zorder=2))
ax.add_patch(patches.FancyBboxPatch((COL_NAME_X - 0.5, box_top - 2.6), LOGICAL_W - 2 * (COL_NAME_X - 0.5), 2.6,
                                     boxstyle="round,pad=0.2", linewidth=0, facecolor=INK, zorder=2))
ax.text(LOGICAL_W / 2, box_top - 1.3, "新商品採用時チェックリスト　※package_verification.csvへの追加担当者向け",
        fontsize=9.6, fontweight="bold", ha="center", va="center", color="white", zorder=3)


def draw_step(x, y, w, num, title, lines, fs_title=9.6, fs_body=8.2, line_h=2.4):
    badge_r = 1.15
    ax.add_patch(patches.Circle((x + badge_r, y), badge_r, facecolor=INK, edgecolor="none", zorder=3))
    ax.text(x + badge_r, y, f"STEP{num}", fontsize=5.0, fontweight="bold", ha="center", va="center",
            color="white", zorder=4)
    tx = x + badge_r * 2 + 1.2
    ax.text(tx, y, title, fontsize=fs_title, fontweight="bold", ha="left", va="center", color=INK)
    y -= line_h * 1.05
    for line in lines:
        for wline in wrap_to_width(line, fs_body, w - (badge_r * 2 + 1.2) - 0.5):
            ax.text(tx, y, wline, fontsize=fs_body, ha="left", va="center", color="#333333")
            y -= line_h * 0.82
        y -= line_h * 0.18
    return y - 0.3


qy = box_top - 5.5
STEP_W = LOGICAL_W - 2 * (COL_NAME_X + 1.0)
qy = draw_step(COL_NAME_X + 1.0, qy, STEP_W, 1, "OTC添付文書の「成分欄」を確認",
               ["「成分（N錠中）」の表記は、成人の1日量とみなしてよい。",
                "＊ただし、毎食後に加えて就寝前も服用可等、1日の服用回数が前提と異なる場合は、実際の1日服用回数分で計算し直す。"])
qy -= 1.7
qy = draw_step(COL_NAME_X + 1.0, qy, STEP_W, 2, "OTC添付文書の「用法用量欄」を確認",
               ["指定濫用防止医薬品の判定は、15歳以上の用量を基準とする（小児用量・「適宜増減」は使わない）。"])
qy -= 1.7
qy = draw_step(COL_NAME_X + 1.0, qy, STEP_W, 3, "消費日数を計算し、小容量/大容量を判定",
               ["包装数量 ÷ 1日量 ＝ 消費日数。消費日数が基準日数（×7または×5）以下なら小容量、超過なら大容量（1枚目のドリルと同じ計算式）。"])
qy -= 1.7
qy = draw_step(COL_NAME_X + 1.0, qy, STEP_W, 4, "管理表の作成",
               ["（例）package_verification.csv",
                "列の意味：product=商品名／kubun=区分記号(〇:対象品)／package=包装規格／days=消費日数(日)／judgment=容量判定(小容量,大容量)／"
                "limit=基準日数(7日 or 5日)／note=備考／ingredients=対象成分／daily_dose=1日量(錠・包等)",
                "入力例（改源 26包）：product=改源, kubun=〇, package=26包, days=8.7, judgment=大容量, limit=7, ingredients=メチルエフェドリン, daily_dose=3"])

# ==========================================================
# 下段：剤形・医薬品区分の基礎知識
# ==========================================================
SEC_TOP = box_top - box_h - 2.2
SEC_BOTTOM = PAGE_BOTTOM + 2.2
SEC_LEFT, SEC_RIGHT = COL_NAME_X, LOGICAL_W - COL_NAME_X
SEC_HEADER_H = 3.2


def draw_block(x, y, w, title, lines, fs_title, fs_body, line_h, title_color=INK):
    ax.text(x, y, f"■ {title}", fontsize=fs_title, fontweight="bold", ha="left", va="center", color=title_color)
    y -= line_h * 1.1
    for line in lines:
        for wline in wrap_to_width(line, fs_body, w - 1.0):
            ax.text(x + 0.8, y, wline, fontsize=fs_body, ha="left", va="center", color="#333333")
            y -= line_h
    y -= 0.3
    ax.hlines(y, x, x + w, colors="#dddddd", linewidth=0.6)
    return y - 0.45


SHAPE_BLOCKS = [
    ("トローチ剤／含嗽剤／口腔用スプレー＝「外用剤」（耳鼻咽喉科用剤）", [
        "のど粘膜への局所作用が目的のため「外用」扱いとなり、規制から除外される（参考：医療用ニトロスプレー・アフタッチも外用扱い）。",
    ], BLUE),
    ("ドロップ剤・舌下錠＝「内服剤」（経口投与される製剤）", [
        "糖をベースに作られ、唾液とともに胃や腸へ流れ込み全身（脳の咳中枢や気管支等）に作用させる目的も併せ持つため、液体・錠剤と同じ「内服薬」に分類される。指定成分が入っていれば販売制限の対象。舌下錠も同グループ（参考：医療用ニトロ舌下錠は錠剤形状のため内服扱い）。",
        "例：「ルルメディカルドロップ」のようなドロップ剤は製法が飴に近いが、全身に成分が回るため内服薬分類。濫用成分を含めば販売制限の対象。",
    ], RED),
]

CANDY_ROWS = [
    ("医薬品ドロップ（内服）", "浅田飴、ルルメディカルドロップ等", "指定成分があれば規制対象", RED),
    ("指定医薬部外品（のど飴）", "ヴィックスメディケイテッドドロップ、ルルのど飴等", "強い指定成分（メチルエフェドリン等）を配合できないルールのため100%対象外", GRAY),
    ("食品（普通の飴）", "龍角散ののど飴、カンロのど飴等", "お菓子のため100%対象外", GRAY),
]

CLASS_ROWS = [
    ("要指導医薬品", "薬剤師による対面販売必須。ネット通販不可。購入時に書面での説明と確認がある最上位規制。", False),
    ("第1類医薬品", "薬剤師による販売必須。ネット通販は可能だが、購入前にメール等での確認ステップがある。", False),
    ("指定第2類医薬品", "登録販売者でも販売可能。禁忌の確認が推奨される（妊婦・ぜんそく既往・依存リスク等）。", False),
    ("＝＝＝ここまでが「指定濫用防止成分を配合できる」区分＝＝＝", "", None),
    ("第2類医薬品", "強い禁忌や深刻な依存性はない成分。多くの漢方薬・胃腸薬・一部の目薬等が該当。", True),
    ("第3類医薬品", "購入時の法的制限が最も緩い、副作用リスクが低い日常的なお薬（ビタミン剤等）。", True),
    ("指定医薬部外品／医薬部外品／食品", "指定濫用防止成分は配合不可（指定医薬部外品はコンビニ販売可、「殺菌・消毒／声がれ」等の文言が可）。", True),
]


def render_lower(fs_h, fs_title, fs_body, fs_tbl, line_h):
    y = SEC_TOP - SEC_HEADER_H - line_h * 0.9

    # --- 剤形の基本ルール（外用/内服の分岐） ---
    ax.text(SEC_LEFT + 0.8, y, "剤形の基本ルール：トローチと「内服のドロップ」は扱いが異なります",
            fontsize=fs_h, fontweight="bold", ha="left", va="center", color=INK)
    y -= line_h * 1.3
    for title, lines, tcolor in SHAPE_BLOCKS:
        y = draw_block(SEC_LEFT + 0.8, y, SEC_RIGHT - SEC_LEFT - 1.6, title, lines, fs_title, fs_body, line_h, tcolor)

    # --- のど飴3グラデーション ---
    y -= 0.2
    ax.text(SEC_LEFT + 0.8, y, "「市販ののど飴」の3つのグラデーション",
            fontsize=fs_h, fontweight="bold", ha="left", va="center", color=INK)
    y -= line_h * 1.3
    tag_w = max(text_width(t, fs_tbl, "bold") for t, _, _, _ in CANDY_ROWS) + 1.6
    for name, examples, rule, tcolor in CANDY_ROWS:
        tag_h = line_h * 0.95
        ax.add_patch(patches.FancyBboxPatch((SEC_LEFT + 0.8, y - tag_h / 2), tag_w, tag_h, boxstyle="round,pad=0.06",
                                             linewidth=0.8, edgecolor=tcolor, facecolor="white", zorder=2))
        ax.text(SEC_LEFT + 0.8 + tag_w / 2, y, name, fontsize=fs_tbl, fontweight="bold", ha="center", va="center",
                color=tcolor, zorder=3)
        body_x = SEC_LEFT + 0.8 + tag_w + 1.0
        body_w = SEC_RIGHT - body_x - 0.8
        wrapped = wrap_to_width(f"{examples}⇒{rule}", fs_body, body_w)
        for wi, wline in enumerate(wrapped):
            ax.text(body_x, y - wi * line_h * 0.85, wline, fontsize=fs_body, ha="left", va="center", color="#333333")
        y -= max(tag_h, len(wrapped) * line_h * 0.85) + 0.35
    y -= 0.1
    for wline in wrap_to_width(
            "＊店頭で「ドロップ・のど飴」を見るときは、パッケージに「第2類医薬品」（または指定第2類医薬品）と書かれているものだけ、"
            "内服ルールの網を被せて成分チェックすればOK。",
            fs_body, SEC_RIGHT - SEC_LEFT - 1.6):
        ax.text(SEC_LEFT + 0.8, y, wline, fontsize=fs_body, fontstyle="italic", ha="left", va="center", color=LGRAY)
        y -= line_h * 0.85
    y -= 0.35
    ax.hlines(y, SEC_LEFT, SEC_RIGHT, colors="#dddddd", linewidth=0.6)
    y -= 0.45

    # --- 医薬品区分（参考） ---
    ax.text(SEC_LEFT + 0.8, y, "医薬品の区分（参考）　※新成分は原則3年間の監視期間で区分見直しの可能性あり",
            fontsize=fs_h, fontweight="bold", ha="left", va="center", color=INK)
    y -= line_h * 1.3
    for name, body, below_line in CLASS_ROWS:
        if below_line is None:
            ax.text((SEC_LEFT + SEC_RIGHT) / 2, y, name,
                    fontsize=fs_tbl, fontweight="bold", ha="center", va="center", color=RED)
            y -= line_h * 1.1
            continue
        name_w = 22.0
        ax.text(SEC_LEFT + 0.8, y, name, fontsize=fs_tbl, fontweight="bold", ha="left", va="center",
                color=GRAY if below_line else INK)
        wrapped = wrap_to_width(body, fs_body, SEC_RIGHT - SEC_LEFT - name_w - 1.6)
        for wi, wline in enumerate(wrapped):
            ax.text(SEC_LEFT + 0.8 + name_w, y - wi * line_h * 0.85, wline, fontsize=fs_body,
                    ha="left", va="center", color="#333333" if not below_line else "#888888")
        y -= max(line_h, len(wrapped) * line_h * 0.85) + 0.25
    return y


_dry_fig, _dry_ax = plt.subplots(figsize=(10, 14.14))
_dry_ax.set_xlim(0, LOGICAL_W)
_dry_ax.set_ylim(0, LOGICAL_H)
_dry_ax.axis("off")

_real_ax = ax
ax = _dry_ax
BASE_H, BASE_TITLE, BASE_BODY, BASE_TBL, BASE_LH = 6.4, 6.0, 5.3, 5.3, 1.55
avail_h = SEC_TOP - SEC_HEADER_H - SEC_BOTTOM - 0.6

lo, hi = 0.5, 2.2
for _ in range(16):
    mid = (lo + hi) / 2
    _dry_ax.cla()
    _dry_ax.axis("off")
    probe_end = render_lower(BASE_H * mid, BASE_TITLE * mid, BASE_BODY * mid, BASE_TBL * mid, BASE_LH * mid)
    needed_h = (SEC_TOP - SEC_HEADER_H) - probe_end
    if needed_h <= avail_h:
        lo = mid
    else:
        hi = mid
SCALE = lo
ax = _real_ax
_dry_fig.clf()

FS_H, FS_TITLE, FS_BODY, FS_TBL, LINE_H = BASE_H * SCALE, BASE_TITLE * SCALE, BASE_BODY * SCALE, BASE_TBL * SCALE, BASE_LH * SCALE

ax.add_patch(patches.FancyBboxPatch((SEC_LEFT, SEC_BOTTOM), SEC_RIGHT - SEC_LEFT, SEC_TOP - SEC_BOTTOM,
                                     boxstyle="round,pad=0.15", linewidth=1.6, edgecolor=INK, facecolor="#fbfbfb", zorder=0))
ax.add_patch(patches.FancyBboxPatch((SEC_LEFT, SEC_TOP - SEC_HEADER_H), SEC_RIGHT - SEC_LEFT, SEC_HEADER_H,
                                     boxstyle="round,pad=0.15", linewidth=0, facecolor=INK, zorder=1))
ax.text(LOGICAL_W / 2, SEC_TOP - SEC_HEADER_H / 2, "剤形・医薬品区分の基礎知識", fontsize=10.5, fontweight="bold",
        ha="center", va="center", color="white", zorder=3)

sec_end = render_lower(FS_H, FS_TITLE, FS_BODY, FS_TBL, LINE_H)

# --- 下部出典 ---
ax.text(LOGICAL_W / 2, 1.1,
        "準拠: 厚生労働省 局長通知「指定濫用防止医薬品の指定について」/JSMI「指定濫用防止医薬品の販売制度について」/兵庫県 薬務課 制度改正資料",
        fontsize=4.4, ha="center", va="center", color="#aaaaaa")

fig.savefig(OUTPUT_PNG, dpi=300)
fig.savefig(OUTPUT_PDF)
plt.close(fig)
plt.close(_meas_fig)
print(f"v13【4枚目】出力完了: {OUTPUT_PNG}")
print(f"下段文字スケール: {SCALE:.3f}")
print(f"上段最終y: {qy:.2f}")
print(f"下段最終y: {sec_end:.2f}  枠下端: {SEC_BOTTOM:.2f}")
