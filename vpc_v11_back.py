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

BLUE, RED, ORANGE, GREEN, GRAY = "#1565c0", "#d32f2f", "#e65100", "#2e7d32", "#555555"

# --- 全体枠とタイトル ---
ax.add_patch(patches.Rectangle((1.0, 1.0), 98.0, 68.0, fill=False, edgecolor="#cccccc", linewidth=2.0))
ax.text(LOGICAL_W / 2, 66.3, "【裏面】状況別対応のポイント（想定ケースと臨床エビデンス）", fontsize=13, fontweight="bold", ha="center", va="center", color=GRAY)
ax.hlines(64.3, 2.0, 98.0, colors="#cccccc", linewidth=1.0)

COL1_X, COL2_X = 2.5, 51.5
COL_W = 46.0


def draw_case(ax, x, y, q_num, category, condition, action_lines, bg_color):
    n_lines = len(action_lines)
    box_h = 2.6 + n_lines * 1.55
    ax.add_patch(patches.Rectangle((x, y - box_h), COL_W, box_h, facecolor=bg_color, edgecolor="#e0e0e0", linewidth=1.0))
    ax.text(x + 1.0, y - 0.5, f"{q_num} [{category}] {condition}", fontsize=8.6, fontweight="bold", ha="left", va="center", color=BLUE)
    text_y = y - 2.1
    for line in action_lines:
        is_alert = ("禁忌" in line) or ("一律" in line) or ("不可" in line)
        ax.text(x + 1.5, text_y, line, fontsize=6.8, ha="left", va="center",
                color=RED if is_alert else "#222222", fontweight="bold" if is_alert else "normal")
        text_y -= 1.55
    return y - box_h - 0.8


current_y_col1 = 62.5
current_y_col2 = 62.5

# --- 左カラム（年齢・重複・体質・成分の落とし穴） ---
current_y_col1 = draw_case(ax, COL1_X, current_y_col1, "①②", "年齢・重複",
    "18歳未満、または複数個(他店合算)を希望されたら", [
    "▶ 18歳未満への大容量・複数個(種類違い含む)は理由問わず一律禁止",
    "  （販売不可）。家族用でも例外なし。",
    "▶ 12歳未満はコデイン系(ジヒドロコデイン含む)が処方・市販とも",
    "  絶対禁忌。他成分の咳止めへ。",
    "▶ 身分証の提示を拒否されたら、年齢確認不能のため販売不可。",
], "#f4f8fe")

current_y_col1 = draw_case(ax, COL1_X, current_y_col1, "③", "体質(アレルギー)",
    "解熱鎮痛薬でアレルギー歴があると聞いたら", [
    "▶ ピリン疹ならNSAIDs（ロキソプロフェン等）へ代替可。",
    "▶ アスピリン喘息はNSAIDs全般（ロキソプロフェン/イブプロフェン/",
    "  アスピリン等）に100%交差耐性があり全てNG→AAP単剤のみ提案。",
], "#fff9f4")

current_y_col1 = draw_case(ax, COL1_X, current_y_col1, "③", "体質(喘息・不整脈等)",
    "喘息・不整脈・緑内障・前立腺肥大の既往を聞いたら", [
    "▶ 抗コリン薬/第一世代抗ヒスタミン薬は、喘息で痰の粘稠化・",
    "  排痰困難、不整脈で頻脈・QT延長のリスク。",
    "▶ 緑内障は眼圧上昇、前立腺肥大は尿閉のリスクがあり要注意。",
    "  単一成分薬を推奨。",
], "#fff9f4")

current_y_col1 = draw_case(ax, COL1_X, current_y_col1, "※", "成分の落とし穴",
    "長期連用・依存が疑われたら", [
    "▶ ブロモバレリル尿素等ウレイド系は長期乱用で臭素蓄積→歩行",
    "  困難・幻覚（慢性臭素中毒）。高齢者はせん妄・認知機能低下も。",
    "▶ 月15日以上頭痛がある環境で複合鎮痛薬を月10日超・3ヶ月超",
    "  服用→薬剤乱用頭痛（MOH）に進展。",
], "#fafafa")

# --- 右カラム（併用・妊婦授乳・その他） ---
current_y_col2 = draw_case(ax, COL2_X, current_y_col2, "④", "併用",
    "SSRI服用中、または他の薬との併用を聞かれたら", [
    "▶ DXM×SSRIはセロトニン症候群のリスク（濫用防止領域で最も",
    "  急性致死率が高い相互作用）。慎重に対応。",
    "▶ グレープフルーツジュースはDXMの血中濃度を上昇。高脂肪食後は",
    "  ウレイド系の吸収を促進。マクロライド系/アゾール系薬はQT延長・",
    "  心室頻拍に注意。",
], "#fef4f4")

current_y_col2 = draw_case(ax, COL2_X, current_y_col2, "⑤", "妊婦・授乳",
    "妊娠中、または授乳中と分かったら", [
    "▶ 妊娠後期のコデイン系（パブロン/ルル等）は禁忌（新生児呼吸",
    "  抑制）→メジコン等単剤（デキストロメトルファン）を提案。",
    "▶ 抗コリン薬（ブスコパン等）はOTCでは一律禁忌（処方箋なら",
    "  有益性投与可）。授乳中は母乳分泌低下・乳児頻脈のリスクで中断。",
], "#f4f8fe")

current_y_col2 = draw_case(ax, COL2_X, current_y_col2, "※", "運転",
    "運転前後の服用を心配されたら", [
    "▶ 最も排泄が遅い成分を基準に判断。経口・dl体クロルフェニラミン",
    "  （アネトン/パブロンゴールドA等）の半減期は12〜15h",
    "  →服用当日〜翌朝は運転を避けるよう案内。",
], "#fafafa")

current_y_col2 = draw_case(ax, COL2_X, current_y_col2, "※", "外用薬・アンナカ",
    "外用薬や無水カフェインについて聞かれたら", [
    "▶ 軟膏・クリーム・目薬等の外用剤は規制対象成分が入っていても",
    "  対象外。",
    "▶ アンナカ（無水カフェイン）はお茶・コーヒー・エナジードリンク",
    "  等にも大量に含まれ、医薬品だけの一律規制が非現実的なため",
    "  対象外（危険性は認識されている）。",
], "#fafafa")

# --- 中央区切り線 ---
ax.plot([50.0, 50.0], [4.0, 63.5], color="#e0e0e0", linewidth=1.0, linestyle="--")

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
