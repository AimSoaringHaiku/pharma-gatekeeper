import matplotlib.pyplot as plt
import matplotlib.patches as patches
import japanize_matplotlib

OUTPUT_PNG = "atomic_card_table_v11_back_half.png"

# A5横相当の比率レイアウト (A4下半分に印刷)
LOGICAL_W, LOGICAL_H = 100.0, 70.0
fig, ax = plt.subplots(figsize=(10, 7.0))
ax.set_xlim(0, LOGICAL_W); ax.set_ylim(0, LOGICAL_H); ax.axis("off")

BLUE, RED, ORANGE, GREEN, GRAY = "#1565c0", "#d32f2f", "#e65100", "#2e7d32", "#555555"

# --- 全体枠とタイトル ---
ax.add_patch(patches.Rectangle((1.0, 1.0), 98.0, 68.0, fill=False, edgecolor="#cccccc", linewidth=2.0))
ax.text(LOGICAL_W/2, 66.0, "【裏面】 安全確認マニュアル （想定ケースと臨床エビデンス）", fontsize=14, fontweight="bold", ha="center", color=GRAY)
ax.hlines(64.0, 2.0, 98.0, colors="#cccccc", linewidth=1.0)

# ==========================================================
# 2カラムレイアウト（表面の質問に対応）
# ==========================================================
COL1_X, COL2_X = 2.5, 51.5

def draw_case(ax, x, y, q_num, category, condition, action, bg_color):
    ax.add_patch(patches.Rectangle((x, y-10.0), 46.0, 11.5, facecolor=bg_color, edgecolor="#e0e0e0", linewidth=1.0))
    ax.text(x+1.0, y, f"{q_num} [{category}] {condition}", fontsize=10.5, fontweight="bold", color=BLUE)
    lines = action.split('\n')
    text_y = y - 2.5
    for line in lines:
        is_alert = "禁忌" in line or "謝絶" in line or "不可" in line
        ax.text(x+1.5, text_y, line, fontsize=8.5, color=RED if is_alert else "#222222", fontweight="bold" if is_alert else "normal")
        text_y -= 2.0
    return y - 11.0

current_y_col1, current_y_col2 = 61.0, 61.0

# --- 左カラム（年齢・重複・体質） ---
current_y_col1 = draw_case(ax, COL1_X, current_y_col1, "①②", "年齢・重複", "18歳未満 / または複数個を希望", 
                           "▶ 18歳未満は「大容量」「複数個」ともに一律販売不可（謝絶）。\n▶ 12歳未満はコデイン類（ジヒドロ等）が呼吸抑制リスクのため\n  絶対禁忌。\n▶ 成人で複数個希望の場合、適正使用外（買いだめ等）と\n  判断した場合は販売謝絶。", "#f4f8fe")

current_y_col1 = draw_case(ax, COL1_X, current_y_col1, "③", "体質", "アレルギー / 喘息がある", 
                           "▶ ピリン疹既往：非ピリン系（イブプロフェン等）へ代替可。\n▶ アスピリン喘息：NSAIDs全般が重篤な発作を誘発するため\n  禁忌。アセトアミノフェン単剤を推奨。", "#fff9f4")

current_y_col1 = draw_case(ax, COL1_X, current_y_col1, "③", "体質", "緑内障 / 前立腺肥大 / 不整脈がある", 
                           "▶ 抗コリン薬・第一世代抗ヒスタミン（プロメタジン等）は\n  眼圧上昇や尿閉リスクのため禁忌または要注意。\n▶ 頻脈・QT延長リスクがあるため、単一成分薬を推奨。", "#fff9f4")

# --- 右カラム（併用・妊婦・その他） ---
current_y_col2 = draw_case(ax, COL2_X, current_y_col2, "④", "併用", "SSRI・MAO阻害薬・鎮静薬を服用中", 
                           "▶ DXM（デキストロメトルファン）とSSRI等の併用は、\n  セロトニン症候群（発熱・錯乱等）の重大リスク。販売謝絶。\n▶ 中枢神経抑制薬との併用は呼吸抑制を増強するため不可。", "#fef4f4")

current_y_col2 = draw_case(ax, COL2_X, current_y_col2, "⑤", "妊婦・授乳", "妊娠中 / 授乳中", 
                           "▶ 妊娠後期のNSAIDsは動脈管早期閉鎖リスクで禁忌。\n  アセトアミノフェン単剤等を第一選択として提案。\n▶ 授乳中のコデインは乳児モルヒネ中毒リスクのため代替薬へ。\n▶ DXM等は服薬後2〜4時間授乳を回避。", "#f4f8fe")

current_y_col2 = draw_case(ax, COL2_X, current_y_col2, "※", "その他", "運転 / ドーピング / 長期連用", 
                           "▶ 運転：最遅排泄成分（例: 経口dl体クロルフェニラミンの\n  半減期12〜15h）を基準に、翌日への影響を指導。\n▶ 連用：月15日以上頭痛がある環境での連用は\n  薬剤乱用頭痛（MOH）に進展しやすいため受診勧奨。", "#fafafa")

# --- 中央区切り線 ---
ax.plot([50.0, 50.0], [4.0, 63.0], color="#e0e0e0", linewidth=1.0, linestyle="--")

# --- 下部免責 ---
ax.text(LOGICAL_W/2, 2.0, "※本マニュアルは一次的対応の目安であり、個別の診断を行うものではありません。最終判断は薬剤師・登録販売者の専門的知見に基づき実施してください。", fontsize=6.5, ha="center", color=GRAY)

plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches="tight")
plt.close()
print(f"v11【裏面】出力完了: {OUTPUT_PNG}")