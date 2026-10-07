import matplotlib.pyplot as plt
import matplotlib.patches as patches
import japanize_matplotlib

# 5枚目：新商品 判定ワークシート（穴埋め式・印刷して手書きで使う）
# 1〜4枚目と同じ判定ロジック（区分 → 指定8成分 → 基準日数 → 1日量 → 消費日数）を、上から埋めれば結論が出る形にしたもの。
# 印刷はA4（幅10in→8.27inに縮小）想定のため、本文は fontsize 10 以上・注記も 9 以上（印刷時およそ7.5pt以上）にしている。

OUTPUT_PNG = "atomic_card_table_v13_page5.png"
OUTPUT_PDF = "atomic_card_table_v13_page5.pdf"

LOGICAL_W, LOGICAL_H = 100.0, 141.4
fig, ax = plt.subplots(figsize=(10, 14.14))
ax.set_position([0, 0, 1, 1])
ax.set_xlim(0, LOGICAL_W)
ax.set_ylim(0, LOGICAL_H)
ax.axis("off")

BLUE, RED, ORANGE, GREEN = "#1565c0", "#d32f2f", "#e65100", "#2e7d32"
INK = "#1a1a1a"
BODY = "#333333"
NOTE = "#666666"
EXAMPLE = "#8a8a8a"

FS_TITLE = 15.0
FS_STEP = 11.5
FS_BODY = 10.2
FS_NOTE = 9.0

LEFT, RIGHT = 2.5, 97.5


def text(x, y, s, fs=FS_BODY, color=BODY, weight="normal", ha="left", **kw):
    ax.text(x, y, s, fontsize=fs, color=color, fontweight=weight, ha=ha, va="center", **kw)


def checkbox(x, y, label, fs=FS_BODY, color=BODY, weight="normal", size=1.25):
    ax.add_patch(patches.Rectangle((x, y - size / 2), size, size, linewidth=1.0, edgecolor=INK, facecolor="white", zorder=3))
    text(x + size + 0.7, y, label, fs=fs, color=color, weight=weight)


def blank(x, y, w, unit=""):
    ax.hlines(y - 0.9, x, x + w, colors=INK, linewidth=0.9)
    if unit:
        text(x + w + 0.4, y, unit)


def step_frame(top, h, num, title, verdict=None):
    """STEP枠を描き、内容の開始y座標を返す"""
    ax.add_patch(patches.FancyBboxPatch((LEFT, top - h), RIGHT - LEFT, h, boxstyle="round,pad=0.15",
                                         linewidth=1.2, edgecolor=INK, facecolor="#fafafa", zorder=1))
    r = 1.6
    ax.add_patch(patches.Circle((LEFT + 0.9 + r, top - 2.2), r, facecolor=INK, edgecolor="none", zorder=3))
    text(LEFT + 0.9 + r, top - 2.2, str(num), fs=13, color="white", weight="bold", ha="center", zorder=4)
    text(LEFT + 0.9 + 2 * r + 1.2, top - 2.2, title, fs=FS_STEP, color=INK, weight="bold")
    if verdict:
        text(RIGHT - 1.2, top - 2.2, verdict, fs=FS_BODY, color=GREEN, weight="bold", ha="right")
    return top - 5.0


CONTENT_X = LEFT + 6.6

# --- タイトル ---
text(LOGICAL_W / 2, LOGICAL_H - 2.6, "【5枚目】新商品 判定ワークシート（穴埋め式）", fs=FS_TITLE, color="#222222",
     weight="bold", ha="center")
text(LOGICAL_W / 2, LOGICAL_H - 5.0, "早見表にない商品は、KEGG等で添付文書を開き ①→⑤ を上から埋めてください。最後の枠で判定と対応が決まります。",
     fs=FS_NOTE, color=NOTE, ha="center")
ax.hlines(LOGICAL_H - 6.4, LEFT, RIGHT, colors="#999999", linewidth=1.2)

# --- 商品情報 ---
y = LOGICAL_H - 9.0
text(LEFT, y, "商品名", weight="bold", color=INK)
blank(LEFT + 6.5, y, 40)
text(LEFT + 50, y, "確認日", weight="bold", color=INK)
blank(LEFT + 56, y, 14)
text(LEFT + 73, y, "確認者", weight="bold", color=INK)
blank(LEFT + 79, y, 16)
y -= 3.4
text(LEFT, y, "参照先", weight="bold", color=INK)
checkbox(LEFT + 6.5, y, "KEGG（一般用医薬品）")
checkbox(LEFT + 27, y, "添付文書・外箱")
checkbox(LEFT + 44, y, "その他")
blank(LEFT + 53.5, y, 41.5)

# --- ① 区分 ---
top = y - 2.6
cy = step_frame(top, 12.0, 1, "医薬品の区分を確認（外箱・添付文書の「第○類医薬品」表記）",
                verdict="医薬部外品・食品 → ここで【対象外】")
checkbox(CONTENT_X, cy, "要指導医薬品")
checkbox(CONTENT_X + 17, cy, "第1類医薬品")
checkbox(CONTENT_X + 33, cy, "指定第2類医薬品")
checkbox(CONTENT_X + 52, cy, "第2類医薬品")
checkbox(CONTENT_X + 68, cy, "第3類医薬品")
cy -= 2.8
text(CONTENT_X + 1.95, cy, "↑ いずれかに該当 → ②へ", color=INK, weight="bold")
checkbox(CONTENT_X + 33, cy, "指定医薬部外品・医薬部外品・食品（のど飴等）→【対象外】", color=GREEN, weight="bold")
cy -= 2.6
text(CONTENT_X, cy, "※第2類・第3類でも成分次第で対象になり得るため、医薬品なら区分に関係なく②へ進む。", fs=FS_NOTE, color=NOTE)

# --- ② 成分 ---
top = top - 12.0 - 1.2
h2 = 26.0
cy = step_frame(top, h2, 2, "KEGGの「成分」欄で指定濫用防止成分（8成分）を探す",
                verdict="1つもなければ → ここで【対象外】")
INGREDIENTS = [
    ("エフェドリン", "エフェドリン塩酸塩"),
    ("メチルエフェドリン", "dl-メチルエフェドリン塩酸塩／サッカリン塩"),
    ("プソイドエフェドリン", "プソイドエフェドリン塩酸塩／硫酸塩"),
    ("コデイン", "コデインリン酸塩水和物（＝リン酸コデイン）"),
    ("ジヒドロコデイン", "ジヒドロコデインリン酸塩"),
    ("デキストロメトルファン", "デキストロメトルファン臭化水素酸塩水和物 等"),
    ("ジフェンヒドラミン", "ジフェンヒドラミン塩酸塩／サリチル酸塩 等"),
    ("ブロモバレリル尿素", "（表記はそのまま）"),
]
col_w = (RIGHT - CONTENT_X) / 2
for i, (name, alias) in enumerate(INGREDIENTS):
    col, row = i % 2, i // 2
    x = CONTENT_X + col * col_w
    yy = cy - row * 3.5
    checkbox(x, yy, name, color=RED, weight="bold")
    text(x + 2.0, yy - 1.55, f"KEGG表記例：{alias}", fs=FS_NOTE, color=NOTE)
cy -= 4 * 3.5 + 0.3
text(CONTENT_X, cy, "→ 1つでもチェックがあれば【対象品】として③へ。", color=INK, weight="bold")
cy -= 2.6
text(CONTENT_X, cy, "※剤形では判断しない：トローチ・のど飴・ドロップ・液剤・カプセルも、医薬品で成分に上記があれば③へ進む。",
     fs=FS_NOTE, color=RED)
cy -= 2.1
text(CONTENT_X, cy, "※紛らわしい対象外：生薬のマオウ／無水カフェイン／プロメタジン等ほかの抗ヒスタミン薬／アリルイソプロピルアセチル尿素",
     fs=FS_NOTE, color=NOTE)

# --- ③ 基準日数 ---
top = top - h2 - 1.2
h3 = 10.0
cy = step_frame(top, h3, 3, "薬効分類から「基準日数」を決める（KEGGの薬効分類・外箱の効能）")
checkbox(CONTENT_X, cy, "かぜ薬　　", color=BLUE, weight="bold")
checkbox(CONTENT_X + 13, cy, "解熱鎮痛薬", color=BLUE, weight="bold")
checkbox(CONTENT_X + 28, cy, "鼻炎用内服薬", color=BLUE, weight="bold")
text(CONTENT_X + 45, cy, "→ 基準 ×7（7日）", color=BLUE, weight="bold")
cy -= 2.8
checkbox(CONTENT_X, cy, "上記以外（鎮咳去痰薬・睡眠改善薬・鎮静薬・乗物酔い薬 など）", color=ORANGE, weight="bold")
text(CONTENT_X + 59, cy, "→ 基準 ×5（5日）", color=ORANGE, weight="bold")
text(CONTENT_X + 79, cy + 1.4, "基準日数", fs=FS_NOTE, color=INK, weight="bold")
blank(CONTENT_X + 79, cy - 0.4, 6, "日")

# --- ④ 1日量 ---
top = top - h3 - 1.2
h4 = 11.8
cy = step_frame(top, h4, 4, "「用法・用量」欄で成人（15歳以上）の1日最大量を出す")
text(CONTENT_X, cy, "1回", color=INK, weight="bold")
blank(CONTENT_X + 3.2, cy, 8, "（錠・包・mL・カプセル）")
text(CONTENT_X + 31, cy, "×　1日", color=INK, weight="bold")
blank(CONTENT_X + 37, cy, 6, "回")
text(CONTENT_X + 47, cy, "＝　1日量", color=INK, weight="bold")
blank(CONTENT_X + 55, cy, 10)
cy -= 2.8
text(CONTENT_X, cy, "※小児量・「適宜増減」は使わず、15歳以上の最大量で計算する（18歳未満が買う場合も同じ）。", fs=FS_NOTE, color=NOTE)
cy -= 2.1
text(CONTENT_X, cy, "※成分欄の「成分（N錠中）」は1日量とみなしてよい。就寝前追加などで回数が多い場合は、その回数で数え直す。",
     fs=FS_NOTE, color=NOTE)

# --- ⑤ 消費日数 ---
top = top - h4 - 1.2
h5 = 19.0
cy = step_frame(top, h5, 5, "包装ごとに消費日数を計算して小容量／大容量を判定")
cols = [("包装規格（例：24錠）", 0), ("包装数量", 17), ("1日量（④）", 30), ("消費日数", 43), ("基準日数（③）", 56), ("判定（どちらかに○）", 70)]
for label, dx in cols:
    text(CONTENT_X + dx, cy, label, fs=FS_NOTE, color=INK, weight="bold")
for r in range(3):
    ry = cy - 3.4 - r * 3.4
    blank(CONTENT_X, ry, 14)
    blank(CONTENT_X + 17, ry, 9)
    text(CONTENT_X + 27.2, ry, "÷", color=INK, weight="bold")
    blank(CONTENT_X + 30, ry, 9)
    text(CONTENT_X + 40.2, ry, "＝", color=INK, weight="bold")
    blank(CONTENT_X + 43, ry, 7, "日")
    text(CONTENT_X + 53.0, ry, "vs", color=INK)
    blank(CONTENT_X + 56, ry, 6, "日")
    text(CONTENT_X + 70, ry, "小容量　・　大容量", color=INK)
cy -= 3 * 3.4 + 2.8
text(CONTENT_X, cy, "消費日数 ≦ 基準日数 → 小容量　／　消費日数 ＞ 基準日数 → 大容量", color=INK, weight="bold")
text(CONTENT_X + 66, cy, "（小数点以下は切り捨てない）", fs=FS_NOTE, color=NOTE)

# --- 判定と対応 ---
top = top - h5 - 1.6
hr = 21.0
ax.add_patch(patches.FancyBboxPatch((LEFT, top - hr), RIGHT - LEFT, hr, boxstyle="round,pad=0.15",
                                     linewidth=1.6, edgecolor=INK, facecolor="white", zorder=1))
ax.add_patch(patches.Rectangle((LEFT, top - 3.0), RIGHT - LEFT, 3.0, facecolor=INK, edgecolor="none", zorder=2))
text(LOGICAL_W / 2, top - 1.5, "判定と販売時の対応（当てはまる枠に○）", fs=FS_STEP, color="white", weight="bold", ha="center", zorder=3)

RESULTS = [
    ("対象外", "①で医薬部外品・食品\nまたは ②で成分なし", GREEN,
     ["通常どおり販売可", "（年齢確認・理由確認は不要）"]),
    ("対象・小容量 1個", "②で成分あり\n⑤で小容量", BLUE,
     ["18歳未満：氏名・年齢を確認", "18歳以上：他店での直近の", "　購入状況を確認"]),
    ("対象・大容量／複数個", "⑤で大容量、または\n小容量を2個以上", ORANGE,
     ["18歳未満：販売不可", "18歳以上：購入理由を確認", "　（正当な理由なしは販売不可）"]),
]
rw = (RIGHT - LEFT - 4.0) / 3
for i, (head, cond, color, actions) in enumerate(RESULTS):
    bx = LEFT + 1.0 + i * (rw + 1.0)
    btop = top - 4.0
    bh = hr - 5.0
    ax.add_patch(patches.FancyBboxPatch((bx, btop - bh), rw, bh, boxstyle="round,pad=0.1",
                                         linewidth=1.4, edgecolor=color, facecolor="white", zorder=2))
    text(bx + rw / 2, btop - 1.8, head, fs=12, color=color, weight="bold", ha="center", zorder=3)
    for li, cl in enumerate(cond.split("\n")):
        text(bx + rw / 2, btop - 4.2 - li * 1.9, cl, fs=FS_NOTE, color=NOTE, ha="center", zorder=3)
    ax.hlines(btop - 7.6, bx + 1.0, bx + rw - 1.0, colors="#cccccc", linewidth=0.8, zorder=3)
    for ai, a in enumerate(actions):
        text(bx + 1.2, btop - 9.4 - ai * 2.0, a, fs=FS_BODY, color=INK, weight="bold" if ai == 0 else "normal", zorder=3)

# --- 記入例 ---
top = top - hr - 1.6
text(LEFT, top - 0.8, "記入例（改源 26包）", fs=FS_BODY, color=INK, weight="bold")
text(LEFT, top - 3.0, "① 医薬品の区分表記あり → ② メチルエフェドリンあり → ③ かぜ薬なので基準7日 → ④ 1回1包 × 1日3回 ＝ 3包",
     fs=FS_NOTE, color=EXAMPLE)
text(LEFT, top - 5.0, "→ ⑤ 26包 ÷ 3包 ＝ 8.7日 ＞ 7日 → 大容量（同じ改源でも 9包 は 3.0日 → 小容量）",
     fs=FS_NOTE, color=EXAMPLE)
text(LEFT, top - 7.2, "判定後は package_verification.csv に1包装＝1行で追記（product／kubun=〇／package／days／judgment／limit／ingredients／daily_dose）。",
     fs=FS_NOTE, color=NOTE)

text(LOGICAL_W / 2, 1.6, "準拠：厚生労働省 局長通知「指定濫用防止医薬品の指定について」／JSMI「指定濫用防止医薬品の販売制度について」",
     fs=7.0, color="#aaaaaa", ha="center")

fig.savefig(OUTPUT_PNG, dpi=300)
fig.savefig(OUTPUT_PDF)
