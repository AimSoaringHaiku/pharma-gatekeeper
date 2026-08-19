import matplotlib.pyplot as plt
import matplotlib.patches as patches
import japanize_matplotlib

OUTPUT_PNG = "atomic_card_table_v11_back.png"

# A5横相当の比率レイアウト
LOGICAL_W, LOGICAL_H = 100.0, 70.0
fig, ax = plt.subplots(figsize=(10, 7.0))
ax.set_position([0, 0, 1, 1])  # savefigでbbox_inches="tight"を使わず全面を使う（比率固定のため必須）
ax.set_xlim(0, LOGICAL_W)
ax.set_ylim(0, LOGICAL_H)
ax.axis("off")
fig.canvas.draw()  # テキスト幅計測のため、先に一度描画してレンダラーを確保

BLUE, RED, ORANGE, GREEN, GRAY, DARKRED = "#1565c0", "#d32f2f", "#e65100", "#2e7d32", "#555555", "#8e0000"


def text_width(text, fontsize, weight="normal", style="normal"):
    t = ax.text(0, -100, text, fontsize=fontsize, fontweight=weight, fontstyle=style, ha="left", va="center")
    fig.canvas.draw()
    bbox = t.get_window_extent(renderer=fig.canvas.get_renderer())
    inv = ax.transData.inverted()
    (x0, _), (x1, _) = inv.transform([[bbox.x0, bbox.y0], [bbox.x1, bbox.y1]])
    t.remove()
    return x1 - x0


# --- 全体枠とタイトル ---
ax.text(LOGICAL_W / 2, 68.0, "【裏面】状況別対応のポイント（想定ケースと臨床エビデンス）", fontsize=13, fontweight="bold", ha="center", va="center", color=GRAY)
ax.hlines(66.2, 2.0, 98.0, colors="#999999", linewidth=1.2)

TITLE_FS, BODY_FS, LINE_H = 8.2, 7.2, 1.75


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


def draw_case(ax, x, y, col_w, q_num, category, condition, action_lines):
    """タイトルの右に1点目の内容を続け、2点目以降はタイトル下に列挙。縦スペースを節約する。"""
    header = f"{q_num}［{category}］{condition}"
    ax.text(x, y, header, fontsize=TITLE_FS, fontweight="bold", ha="left", va="center", color=BLUE)
    header_w = text_width(header, TITLE_FS, "bold")
    remaining_w = col_w - header_w - 1.5

    bullets = list(action_lines)
    first_on_same_line = False
    if bullets:
        first_w = text_width(bullets[0], BODY_FS)
        if remaining_w >= first_w + 1.0 and remaining_w >= 15.0:
            first_on_same_line = True

    if first_on_same_line:
        first = bullets.pop(0)
        is_alert = ("禁忌" in first) or ("一律" in first) or ("不可" in first)
        ax.text(x + header_w + 1.5, y, first, fontsize=BODY_FS, ha="left", va="center",
                color=RED if is_alert else "#333333", fontweight="bold" if is_alert else "normal")
    text_y = y - LINE_H

    for bullet in bullets:
        is_alert = ("禁忌" in bullet) or ("一律" in bullet) or ("不可" in bullet)
        color = RED if is_alert else "#333333"
        weight = "bold" if is_alert else "normal"
        wrapped = wrap_to_width(bullet, BODY_FS, col_w - 1.2)
        for wi, wline in enumerate(wrapped):
            indent = x + 1.2 if wi == 0 else x + 3.0
            ax.text(indent, text_y, wline, fontsize=BODY_FS, ha="left", va="center", color=color, fontweight=weight)
            text_y -= LINE_H

    return text_y - 0.55


def draw_quadrant(ax, x, y, w, h, title, color, fill, cases):
    """2x2グリッドの1マスを描画。角丸枠＋色付きヘッダー＋ケース一覧。"""
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                                         linewidth=1.4, edgecolor=color, facecolor=fill, zorder=1))
    header_h = 3.3
    ax.add_patch(patches.FancyBboxPatch((x, y + h - header_h), w, header_h, boxstyle="round,pad=0.15",
                                         linewidth=0, facecolor=color, zorder=2))
    ax.text(x + w / 2, y + h - header_h / 2, title, fontsize=9.2, fontweight="bold",
            ha="center", va="center", color="white", zorder=3)

    content_x = x + 1.8
    content_w = w - 3.4
    cy = y + h - header_h - 2.1
    for item in cases:
        if item[0] == "case":
            _, q_num, category, condition, bullets = item
            cy = draw_case(ax, content_x, cy, content_w, q_num, category, condition, bullets)
        elif item[0] == "note":
            _, text = item
            wrapped = wrap_to_width(text, 6.2, content_w)
            for wline in wrapped:
                ax.text(content_x, cy, wline, fontsize=6.2, fontstyle="italic", ha="left", va="center", color=GRAY)
                cy -= 1.3
            cy -= 0.1
        elif item[0] == "marker_list":
            _, rows = item
            for mcolor, mshape, tag, ingr in rows:
                if mshape == "circle":
                    ax.add_patch(patches.Circle((content_x + 0.5, cy), 0.4, facecolor=mcolor, edgecolor="none", zorder=3))
                else:
                    ax.add_patch(patches.Rectangle((content_x + 0.1, cy - 0.4), 0.8, 0.8, facecolor=mcolor, edgecolor="none", zorder=3))
                wrapped = wrap_to_width(ingr, 6.1, content_w - 2.2)
                ax.text(content_x + 1.5, cy, wrapped[0], fontsize=6.1, fontweight="bold", ha="left", va="center", color="#333333")
                cy -= LINE_H * 0.85
                ax.text(content_x + 1.5, cy, "→ " + tag, fontsize=6.2, fontweight="bold", ha="left", va="center", color=mcolor)
                cy -= LINE_H * 0.95
    return cy


# --- 2x2グリッド配置 ---
GRID_LEFT, GRID_RIGHT = 2.0, 98.0
GRID_TOP, GRID_BOTTOM = 64.3, 4.0
GUTTER = 2.0
COL_W = (GRID_RIGHT - GRID_LEFT - GUTTER) / 2
ROW_H = (GRID_TOP - GRID_BOTTOM - GUTTER) / 2

Q1_X, Q2_X = GRID_LEFT, GRID_LEFT + COL_W + GUTTER
ROW1_Y, ROW2_Y = GRID_BOTTOM + ROW_H + GUTTER, GRID_BOTTOM

# --- Q1: 年齢・重複購入・併用 ---
draw_quadrant(ax, Q1_X, ROW1_Y, COL_W, ROW_H, "①②④ 年齢・重複・併用", BLUE, "#f7fafd", [
    ("case", "①②", "年齢・重複", "18歳未満、または複数個(他店合算)を希望されたら", [
        "▶ 18歳未満への大容量・複数個(種類違い含む)は理由問わず一律禁止（販売不可）。家族用でも例外なし。",
        "▶ 12歳未満はコデイン系(ジヒドロコデイン含む)が処方・市販とも絶対禁忌。他成分の咳止めへ。",
        "▶ 身分証の提示を拒否されたら、年齢確認不能のため販売不可。",
    ]),
    ("case", "④", "併用", "SSRI服用中、または他の薬との併用を聞かれたら", [
        "▶ DXM×SSRIはセロトニン症候群のリスク（濫用防止領域で最も急性致死率が高い相互作用）。慎重に対応。",
        "▶ グレープフルーツジュースはDXMの血中濃度を上昇。マクロライド系/アゾール系薬はQT延長・心室頻拍に注意。",
    ]),
])

# --- Q2: 体質・持病・外用薬 ---
draw_quadrant(ax, Q2_X, ROW1_Y, COL_W, ROW_H, "③ 体質・持病", ORANGE, "#fff8f0", [
    ("case", "③", "体質(アレルギー)", "解熱鎮痛薬でアレルギー歴があると聞いたら", [
        "▶ ピリン疹ならNSAIDs（ロキソプロフェン等）へ代替可。",
        "▶ アスピリン喘息はNSAIDs全般（ロキソプロフェン/イブプロフェン/アスピリン等）に100%交差耐性があり全てNG→AAP単剤のみ提案。",
    ]),
    ("case", "③", "体質(喘息・不整脈等)", "喘息・不整脈・緑内障・前立腺肥大の既往を聞いたら", [
        "▶ 抗コリン薬/第一世代抗ヒスタミン薬は、喘息で痰の粘稠化・排痰困難、不整脈で頻脈・QT延長のリスク。",
        "▶ 緑内障は眼圧上昇、前立腺肥大は尿閉のリスクがあり要注意。単一成分薬を推奨。",
    ]),
    ("case", "※", "外用薬・アンナカ", "外用薬や無水カフェインについて聞かれたら", [
        "▶ 軟膏・クリーム・目薬等の外用剤は規制対象成分が入っていても対象外。",
        "▶ アンナカ（無水カフェイン）はお茶・コーヒー等にも大量に含まれ、医薬品だけの一律規制が非現実的なため対象外。",
    ]),
])

# --- Q3: 妊娠・授乳中（授乳婦指導を統合） ---
draw_quadrant(ax, Q1_X, ROW2_Y, COL_W, ROW_H, "⑤ 妊娠・授乳中", RED, "#fdf5f5", [
    ("case", "⑤", "妊婦・授乳", "妊娠中、または授乳中と分かったら", [
        "▶ 妊娠後期のコデイン系（パブロン/ルル等）は禁忌（新生児呼吸抑制）→メジコン等単剤（デキストロメトルファン）を提案。",
        "▶ 抗コリン薬（ブスコパン等）はOTCでは一律禁忌（処方箋なら有益性投与可）。授乳中は母乳分泌低下・乳児頻脈のリスクで中断。",
    ]),
    ("note", "授乳婦指導（成分別の目安）:"),
    ("marker_list", [
        (GREEN, "circle", "通常授乳可", "アセトアミノフェン/イブプロフェン/無水カフェイン(通常量)"),
        (ORANGE, "circle", "服薬後2-4h授乳回避", "デキストロメトルファン/ジフェンヒドラミン(短期)"),
        (RED, "circle", "搾乳破棄(半減期×3-4h)", "クロルフェニラミン(長期)/プロメタジン/ブロモバレリル尿素"),
        (DARKRED, "square", "代替薬へ変更提案", "コデイン/ジヒドロコデイン(乳児モルヒネ代謝リスク)"),
    ]),
])

# --- Q4: その他の注意点（過量服薬リスクを成分の落とし穴に統合） ---
draw_quadrant(ax, Q2_X, ROW2_Y, COL_W, ROW_H, "その他の注意点", GREEN, "#f3f9f3", [
    ("case", "※", "成分の落とし穴・過量服薬", "長期連用・依存や過量服薬が疑われたら", [
        "▶ ブロモバレリル尿素等ウレイド系は長期乱用で臭素蓄積→歩行困難・幻覚（慢性臭素中毒）。高齢者はせん妄・認知機能低下も。",
        "▶ 月15日以上頭痛がある環境で複合鎮痛薬を月10日超・3ヶ月超服用→薬剤乱用頭痛（MOH）に進展。",
        "▶ 過量服薬は初日=急性心毒性(無水カフェイン等)、3日目以降=劇症肝不全(アセトアミノフェン)が急速進行。NSAIDsは自覚症状ありだがAAPは無症状のまま進行するため特に注意。",
    ]),
    ("case", "※", "運転", "運転前後の服用を心配されたら", [
        "▶ 最も排泄が遅い成分を基準に判断。経口・dl体クロルフェニラミン（アネトン/パブロンゴールドA等）の半減期は12〜15h",
        "  →服用当日〜翌朝は運転を避けるよう案内。",
    ]),
])

# --- 下部免責・出典 ---
ax.text(LOGICAL_W / 2, 2.6, "※本マニュアルは一次的対応の目安であり、個別の診断を行うものではありません。最終判断は薬剤師・登録販売者の専門的知見に基づき実施してください。",
        fontsize=5.6, ha="center", va="center", color=GRAY)
ax.text(LOGICAL_W / 2, 1.3,
        "準拠: 厚生労働省 局長通知「指定濫用防止医薬品の指定について」/JSMI「指定濫用防止医薬品の販売制度について」/兵庫県 薬務課 制度改正資料",
        fontsize=4.4, ha="center", va="center", color="#aaaaaa")

plt.savefig(OUTPUT_PNG, dpi=300)  # bbox_inches="tight"を使わない（比率固定のため）
plt.close()
print(f"v11【裏面】出力完了: {OUTPUT_PNG}")
