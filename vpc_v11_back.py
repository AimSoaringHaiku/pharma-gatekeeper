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
renderer = fig.canvas.get_renderer()

BLUE, RED, ORANGE, GREEN, GRAY = "#1565c0", "#d32f2f", "#e65100", "#2e7d32", "#555555"

def text_width(text, fontsize, weight="normal"):
    t = ax.text(0, -100, text, fontsize=fontsize, fontweight=weight, ha="left", va="center")
    # fig.canvas.draw()  ← 【削除】毎回全体を再描画させない
    bbox = t.get_window_extent(renderer=renderer)  # ← 【変更】保存したレンダラーを使う
    inv = ax.transData.inverted()
    (x0, _), (x1, _) = inv.transform([[bbox.x0, bbox.y0], [bbox.x1, bbox.y1]])
    t.remove()
    return x1 - x0

# --- 全体枠とタイトル ---
ax.text(LOGICAL_W / 2, 68.0, "【裏面】状況別対応のポイント（想定ケースと臨床エビデンス）", fontsize=13, fontweight="bold", ha="center", va="center", color=GRAY)
ax.hlines(66.2, 2.0, 98.0, colors="#999999", linewidth=1.2)

COL1_X, COL2_X = 2.0, 51.0
COL_W = 47.0
TITLE_FS, BODY_FS, LINE_H = 7.6, 6.8, 1.5


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


def draw_case(ax, x, y, q_num, category, condition, action_lines):
    """タイトルの右に1点目の内容を続け、2点目以降はタイトル下に列挙。縦スペースを節約する。"""
    header = f"{q_num}［{category}］{condition}"
    ax.text(x, y, header, fontsize=TITLE_FS, fontweight="bold", ha="left", va="center", color=BLUE)
    header_w = text_width(header, TITLE_FS, "bold")
    remaining_w = COL_W - header_w - 1.5

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
        wrapped = wrap_to_width(bullet, BODY_FS, COL_W - 1.2)
        for wi, wline in enumerate(wrapped):
            indent = x + 1.2 if wi == 0 else x + 3.0
            ax.text(indent, text_y, wline, fontsize=BODY_FS, ha="left", va="center", color=color, fontweight=weight)
            text_y -= LINE_H

    sep_y = text_y + LINE_H * 0.35
    ax.hlines(sep_y, x, x + COL_W, colors="#e5e5e5", linewidth=0.7)
    return sep_y - 0.9


current_y_col1 = 63.5
current_y_col2 = 63.5

# --- 左カラム（年齢・重複・体質・成分の落とし穴） ---
current_y_col1 = draw_case(ax, COL1_X, current_y_col1, "①②", "年齢・重複",
    "18歳未満、または複数個(他店合算)を希望されたら", [
    "▶ 18歳未満への大容量・複数個(種類違い含む)は理由問わず一律禁止（販売不可）。家族用でも例外なし。",
    "▶ 12歳未満はコデイン系(ジヒドロコデイン含む)が処方・市販とも絶対禁忌。他成分の咳止めへ。",
    "▶ 身分証の提示を拒否されたら、年齢確認不能のため販売不可。",
])

current_y_col1 = draw_case(ax, COL1_X, current_y_col1, "③", "体質(アレルギー)",
    "解熱鎮痛薬でアレルギー歴があると聞いたら", [
    "▶ ピリン疹ならNSAIDs（ロキソプロフェン等）へ代替可。",
    "▶ アスピリン喘息はNSAIDs全般（ロキソプロフェン/イブプロフェン/アスピリン等）に100%交差耐性があり全てNG→AAP単剤のみ提案。",
])

current_y_col1 = draw_case(ax, COL1_X, current_y_col1, "③", "体質(喘息・不整脈等)",
    "喘息・不整脈・緑内障・前立腺肥大の既往を聞いたら", [
    "▶ 抗コリン薬/第一世代抗ヒスタミン薬は、喘息で痰の粘稠化・排痰困難、不整脈で頻脈・QT延長のリスク。",
    "▶ 緑内障は眼圧上昇、前立腺肥大は尿閉のリスクがあり要注意。単一成分薬を推奨。",
])

current_y_col1 = draw_case(ax, COL1_X, current_y_col1, "※", "成分の落とし穴",
    "長期連用・依存が疑われたら", [
    "▶ ブロモバレリル尿素等ウレイド系は長期乱用で臭素蓄積→歩行困難・幻覚（慢性臭素中毒）。高齢者はせん妄・認知機能低下も。",
    "▶ 月15日以上頭痛がある環境で複合鎮痛薬を月10日超・3ヶ月超服用→薬剤乱用頭痛（MOH）に進展。",
])

# --- 右カラム（併用・妊婦授乳・その他） ---
current_y_col2 = draw_case(ax, COL2_X, current_y_col2, "④", "併用",
    "SSRI服用中、または他の薬との併用を聞かれたら", [
    "▶ DXM×SSRIはセロトニン症候群のリスク（濫用防止領域で最も急性致死率が高い相互作用）。慎重に対応。",
    "▶ グレープフルーツジュースはDXMの血中濃度を上昇。高脂肪食後はウレイド系の吸収を促進。マクロライド系/アゾール系薬はQT延長・心室頻拍に注意。",
])

current_y_col2 = draw_case(ax, COL2_X, current_y_col2, "⑤", "妊婦・授乳",
    "妊娠中、または授乳中と分かったら", [
    "▶ 妊娠後期のコデイン系（パブロン/ルル等）は禁忌（新生児呼吸抑制）→メジコン等単剤（デキストロメトルファン）を提案。",
    "▶ 抗コリン薬（ブスコパン等）はOTCでは一律禁忌（処方箋なら有益性投与可）。授乳中は母乳分泌低下・乳児頻脈のリスクで中断。",
])

current_y_col2 = draw_case(ax, COL2_X, current_y_col2, "※", "運転",
    "運転前後の服用を心配されたら", [
    "▶ 最も排泄が遅い成分を基準に判断。経口・dl体クロルフェニラミン（アネトン/パブロンゴールドA等）の半減期は12〜15h",
    "  →服用当日〜翌朝は運転を避けるよう案内。",
])

current_y_col2 = draw_case(ax, COL2_X, current_y_col2, "※", "外用薬・アンナカ",
    "外用薬や無水カフェインについて聞かれたら", [
    "▶ 軟膏・クリーム・目薬等の外用剤は規制対象成分が入っていても対象外。",
    "▶ アンナカ（無水カフェイン）はお茶・コーヒー・エナジードリンク等にも大量に含まれ、医薬品だけの一律規制が非現実的なため対象外（危険性は認識されている）。",
])

# --- 中央区切り線 ---
ax.plot([49.5, 49.5], [4.0, 66.2], color="#dddddd", linewidth=1.0, linestyle="--")

# --- 下部免責・出典 ---
ax.text(LOGICAL_W / 2, 2.6, "※本マニュアルは一次的対応の目安であり、個別の診断を行うものではありません。最終判断は薬剤師・登録販売者の専門的知見に基づき実施してください。",
        fontsize=5.6, ha="center", va="center", color=GRAY)
ax.text(LOGICAL_W / 2, 1.3,
        "準拠: 厚生労働省 局長通知「指定濫用防止医薬品の指定について」/JSMI「指定濫用防止医薬品の販売制度について」/兵庫県 薬務課 制度改正資料",
        fontsize=4.4, ha="center", va="center", color="#aaaaaa")

plt.savefig(OUTPUT_PNG, dpi=300)  # bbox_inches="tight"を使わない（比率固定のため）
plt.close()
print(f"v11【裏面】出力完了: {OUTPUT_PNG}")
print(f"col1_end={current_y_col1:.2f} col2_end={current_y_col2:.2f}")
