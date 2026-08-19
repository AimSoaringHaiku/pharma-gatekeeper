import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import japanize_matplotlib

OUTPUT_PNG = "atomic_card_table_v11_back.png"
IMG_POSTER1 = "ref_poster_kounyusha.png"   # 「指定濫用防止医薬品をご購入の皆様へ」
IMG_POSTER2 = "ref_poster_oshirase.png"    # 「大切なお知らせ」
IMG_FLOWCHART = "ref_flowchart.png"        # 来店〜販売可否判断フローチャート

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
# 本体 fig に画像(imshow)を貼ると、以降 fig.canvas.draw() のたびに
# 高解像度画像まで毎回再ラスタライズされ、文字幅を1文字ずつ測る
# wrap_to_width が極端に遅くなる（実質フリーズ）ため、画像を含まない
# 軽量な figure で測定する。
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


def wrap_to_width(text, fontsize, max_width):
    """1文字ずつ幅を測りながら、max_widthに収まるように行分割する"""
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


# --- 全体枠とタイトル ---
ax.text(LOGICAL_W / 2, LOGICAL_H - 2.4, "【裏面】指定濫用防止医薬品 参考資料集", fontsize=15, fontweight="bold",
        ha="center", va="center", color="#333333")
ax.text(LOGICAL_W / 2, LOGICAL_H - 4.3, "（厚労省・薬局配布資料の抜粋　／　右下＝状況別対応のポイント）",
        fontsize=7.0, ha="center", va="center", color="#888888")
ax.hlines(LOGICAL_H - 5.6, 2.0, 98.0, colors="#999999", linewidth=1.2)

# --- 2x2グリッド配置 ---
GRID_LEFT, GRID_RIGHT = 2.0, 98.0
GRID_TOP, GRID_BOTTOM = LOGICAL_H - 6.6, 3.0
GUTTER = 2.0
COL_W = (GRID_RIGHT - GRID_LEFT - GUTTER) / 2
ROW_H = (GRID_TOP - GRID_BOTTOM - GUTTER) / 2

Q1_X, Q2_X = GRID_LEFT, GRID_LEFT + COL_W + GUTTER
ROW1_Y, ROW2_Y = GRID_BOTTOM + ROW_H + GUTTER, GRID_BOTTOM


def draw_frame(ax, x, y, w, h, title, color, fill):
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                                         linewidth=1.4, edgecolor=color, facecolor=fill, zorder=1))
    header_h = 3.1
    ax.add_patch(patches.FancyBboxPatch((x, y + h - header_h), w, header_h, boxstyle="round,pad=0.15",
                                         linewidth=0, facecolor=color, zorder=2))
    ax.text(x + w / 2, y + h - header_h / 2, title, fontsize=8.6, fontweight="bold",
            ha="center", va="center", color="white", zorder=3)
    return header_h


def draw_image_quadrant(ax, x, y, w, h, title, color, img_path):
    header_h = draw_frame(ax, x, y, w, h, title, color, "white")
    pad = 1.2
    avail_w = w - 2 * pad
    avail_h = h - header_h - 2 * pad
    img = mpimg.imread(img_path)
    img_h_px, img_w_px = img.shape[0], img.shape[1]
    aspect = img_w_px / img_h_px
    target_w = avail_w
    target_h = target_w / aspect
    if target_h > avail_h:
        target_h = avail_h
        target_w = target_h * aspect
    cx = x + w / 2
    cy = y + (h - header_h) / 2
    ax.imshow(img, extent=[cx - target_w / 2, cx + target_w / 2, cy - target_h / 2, cy + target_h / 2], zorder=2)


# --- Q1: 購入者への案内ポスター ---
draw_image_quadrant(ax, Q1_X, ROW1_Y, COL_W, ROW_H, "参考① 購入者への掲示例", BLUE, IMG_POSTER1)

# --- Q2: 制度改正のお知らせポスター ---
draw_image_quadrant(ax, Q2_X, ROW1_Y, COL_W, ROW_H, "参考② 制度改正のお知らせ", ORANGE, IMG_POSTER2)

# --- Q3: レジ対応フローチャート ---
draw_image_quadrant(ax, Q1_X, ROW2_Y, COL_W, ROW_H, "参考③ 来店〜販売可否フロー", GREEN, IMG_FLOWCHART)

# --- Q4: 状況別対応のポイント（キーワード先頭・情報量を落とさず密に配置） ---
TITLE_FS, KEY_FS, BODY_FS, LINE_H = 6.2, 5.9, 5.4, 1.1

header_h = draw_frame(ax, Q2_X, ROW2_Y, COL_W, ROW_H, "④ 状況別対応のポイント", RED, "#fffbfb")
content_x = Q2_X + 1.4
content_w = COL_W - 2.6
cy = ROW2_Y + ROW_H - header_h - 1.6


def draw_dense_case(x, y, w, q_num, category, condition, bullets):
    """タイトルを1行にまとめ、各弾丸の先頭語をキーワードとして太字強調しつつ密に列挙。"""
    header = f"{q_num}［{category}］{condition}"
    wrapped_header = wrap_to_width(header, TITLE_FS, w)
    for hi, hline in enumerate(wrapped_header):
        ax.text(x, y, hline, fontsize=TITLE_FS, fontweight="bold", ha="left", va="center", color=BLUE)
        y -= LINE_H
    for bullet in bullets:
        is_alert = ("禁忌" in bullet) or ("一律" in bullet) or ("不可" in bullet)
        color = RED if is_alert else "#333333"
        weight = "bold" if is_alert else "normal"
        wrapped = wrap_to_width(bullet, BODY_FS, w - 1.0)
        for wi, wline in enumerate(wrapped):
            indent = x + 1.0 if wi == 0 else x + 2.2
            ax.text(indent, y, wline, fontsize=BODY_FS, ha="left", va="center", color=color, fontweight=weight)
            y -= LINE_H
    return y - 0.28


cases = [
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
    header = "※［運転］運転前後の服用を心配されたら"
    for hline in wrap_to_width(header, TITLE_FS, w):
        ax.text(x, y, hline, fontsize=TITLE_FS, fontweight="bold", ha="left", va="center", color=BLUE)
        y -= LINE_H
    ax.text(x + 1.0, y, "▶最も排泄が遅い成分を基準に判断（半減期の長い成分ほど翌日に持ち越しやすい）",
            fontsize=BODY_FS - 0.3, ha="left", va="center", color="#333333")
    y -= LINE_H * 0.95
    tbl_fs = 4.7
    tbl_lh = 0.92
    col1_x, col2_x, col3_x = x + 1.0, x + 21.0, x + 34.5
    ax.text(col1_x, y, "成分（世代/分類）", fontsize=tbl_fs, fontweight="bold", ha="left", va="center", color=GRAY)
    ax.text(col2_x, y, "回避目安", fontsize=tbl_fs, fontweight="bold", ha="left", va="center", color=GRAY)
    ax.text(col3_x, y, "半減期", fontsize=tbl_fs, fontweight="bold", ha="left", va="center", color=GRAY)
    y -= tbl_lh
    ax.hlines(y + tbl_lh * 0.55, x + 1.0, x + w - 1.0, colors="#dddddd", linewidth=0.5)
    for name, avoid, half in rows:
        ax.text(col1_x, y, name, fontsize=tbl_fs, ha="left", va="center", color="#333333")
        ax.text(col2_x, y, avoid, fontsize=tbl_fs, fontweight="bold", ha="left", va="center", color=RED)
        ax.text(col3_x, y, half, fontsize=tbl_fs, ha="left", va="center", color="#666666")
        y -= tbl_lh
    return y - 0.25


for q_num, category, condition, bullets in cases[:6]:
    cy = draw_dense_case(content_x, cy, content_w, q_num, category, condition, bullets)
cy = draw_driving_table(content_x, cy, content_w, DRIVING_ROWS)
for q_num, category, condition, bullets in cases[6:]:
    cy = draw_dense_case(content_x, cy, content_w, q_num, category, condition, bullets)

ax.text(content_x, cy, "授乳婦指導（成分別の目安）:", fontsize=5.9, fontstyle="italic", ha="left", va="center", color=GRAY)
cy -= LINE_H
nursing_rows = [
    (GREEN, "circle", "通常授乳可", "AAP/イブプロフェン/無水カフェイン(通常量)"),
    (ORANGE, "circle", "服薬後2-4h授乳回避", "DXM/ジフェンヒドラミン(短期)"),
    (RED, "circle", "搾乳破棄(半減期×3-4h)", "クロルフェニラミン(長期)/プロメタジン/ブロモバレリル尿素"),
    (DARKRED, "square", "代替薬へ変更提案", "コデイン/ジヒドロコデイン(乳児モルヒネ代謝リスク)"),
]
for mcolor, mshape, tag, ingr in nursing_rows:
    if mshape == "circle":
        ax.add_patch(patches.Circle((content_x + 0.35, cy), 0.32, facecolor=mcolor, edgecolor="none", zorder=3))
    else:
        ax.add_patch(patches.Rectangle((content_x + 0.03, cy - 0.32), 0.64, 0.64, facecolor=mcolor, edgecolor="none", zorder=3))
    wrapped = wrap_to_width(f"{ingr} → {tag}", BODY_FS, content_w - 1.6)
    for wi, wline in enumerate(wrapped):
        ax.text(content_x + 1.0, cy, wline, fontsize=BODY_FS, fontweight="bold" if wi == 0 else "normal",
                ha="left", va="center", color=mcolor if wi == 0 else "#333333")
        cy -= LINE_H

# --- 下部免責・出典 ---
ax.text(LOGICAL_W / 2, 1.9, "※本マニュアルは一次的対応の目安であり、個別の診断を行うものではありません。最終判断は薬剤師・登録販売者の専門的知見に基づき実施してください。",
        fontsize=5.2, ha="center", va="center", color=GRAY)
ax.text(LOGICAL_W / 2, 0.9,
        "準拠: 厚生労働省 局長通知「指定濫用防止医薬品の指定について」/JSMI「指定濫用防止医薬品の販売制度について」/兵庫県 薬務課 制度改正資料",
        fontsize=4.2, ha="center", va="center", color="#aaaaaa")

fig.savefig(OUTPUT_PNG, dpi=300)  # bbox_inches="tight"を使わない（比率固定のため）。
# plt.savefig()だと計測用の_meas_figが「カレント」を奪っているため必ずfig.savefig()を使う。
plt.close(fig)
plt.close(_meas_fig)
print(f"v11【裏面】出力完了: {OUTPUT_PNG}")
print(f"Q4最終y座標(下限{ROW2_Y:.2f}付近が理想): {cy:.2f}  余白: {cy - ROW2_Y:.2f}")
