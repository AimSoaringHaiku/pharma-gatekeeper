import matplotlib.pyplot as plt
import matplotlib.patches as patches
import japanize_matplotlib

OUTPUT_PNG = "atomic_card_table_v8_page2.png"

LOGICAL_W = 100.0
LOGICAL_H = 141.4

fig, ax = plt.subplots(figsize=(10, 14.14))
ax.set_xlim(0, LOGICAL_W)
ax.set_ylim(0, LOGICAL_H)
ax.axis("off")

GRAY = "#555555"
LGRAY = "#888888"
RED = "#d32f2f"
BLUE = "#1565c0"

y = LOGICAL_H - 2.2
ax.text(LOGICAL_W / 2, y, "薬剤別 包装区分 早見表（2/2）詳細参考資料", fontsize=15, fontweight="bold", ha="center", va="center")
y -= 1.8
ax.text(LOGICAL_W / 2, y, "※1ページ目の早見表で「小/大包装・年齢」まで判断できます。ここは相談を受けた際の深掘り用の参考資料です。",
        fontsize=6.5, ha="center", va="center", color=LGRAY)
y -= 1.5
ax.hlines(y, 0, LOGICAL_W, linewidth=1.5)
y -= 2.5


def section_title(ax, y, text):
    ax.text(1.5, y, text, fontsize=11, fontweight="bold", ha="left", va="center")
    return y - 1.8


# ==========================================================
# A. 計算手順
# ==========================================================
y = section_title(ax, y, "【計算手順】基準日数の把握と消費日数の割り出し")
steps = [
    ("STEP1", "薬の分類を確認し、基準日数を把握する", "かぜ薬・解熱鎮痛薬・鼻炎用内服薬＝7日分／それ以外（せき止め薬等）＝5日分"),
    ("STEP2", "成人（15歳以上）の「1日最大服用量」を確認する", "パッケージの用法・用量から「1回量×1日の服用回数」を計算"),
    ("STEP3", "パッケージ総量が「何日分」か割り出す", "計算式：パッケージ総量 ÷ 1日最大服用量 ＝ 消費日数"),
    ("STEP4", "基準日数と照らして容量区分を判定する", "基準日数以下＝小容量（小包装）／基準日数超＝大容量（大包装）"),
]
for i, (tag, title, detail) in enumerate(steps):
    x = 1.5 + (i % 2) * 49.0
    yy = y - (i // 2) * 3.2
    ax.text(x, yy, tag, fontsize=8, fontweight="bold", color=BLUE, ha="left", va="center")
    ax.text(x + 7.0, yy, title, fontsize=8, ha="left", va="center")
    ax.text(x, yy - 1.5, detail, fontsize=6.3, ha="left", va="center", color=GRAY)
y -= 7.2
y -= 1.5
ax.hlines(y, 0, LOGICAL_W, colors="#dddddd", linewidth=0.8)
y -= 2.2

# ==========================================================
# B. 正しい販売ルール早見表（年齢別）
# ==========================================================
y = section_title(ax, y, "【早見表】正しい販売ルールのまとめ（小容量1個・大容量の対応）")

rule_headers = ["購入者の年齢", "購入する容量", "氏名・年齢の確認", "他店購入状況確認", "販売の可否"]
rule_x = [2.0, 20.0, 40.0, 62.0, 82.0]
for hx, htext in zip(rule_x, rule_headers):
    ax.text(hx, y, htext, fontsize=7.5, fontweight="bold", ha="left", va="center")
y -= 1.3
ax.hlines(y, 0, LOGICAL_W, colors="#cccccc", linewidth=0.8)
y -= 1.8

rule_rows = [
    ("18歳未満", "小容量（1個）", "必須（要身分証等）", "必須", "条件を満たせば販売可"),
    ("18歳以上", "小容量（1個）", "原則不要", "必須", "通常通り販売可"),
]
for r in rule_rows:
    for hx, val in zip(rule_x, r):
        ax.text(hx, y, val, fontsize=7.5, ha="left", va="center")
    y -= 1.9

ax.text(2.0, y, "※【販売謝絶】18歳未満への「大容量製品」や「複数個（他薬・他店合算含む）」の販売は理由を問わず一律禁止です。",
        fontsize=6.5, ha="left", va="center", color=RED, fontweight="bold")
y -= 2.5
ax.hlines(y, 0, LOGICAL_W, colors="#dddddd", linewidth=0.8)
y -= 2.2

# ==========================================================
# C. 瞬時の判別
# ==========================================================
y = section_title(ax, y, "【瞬時の判別】成分・ブランド名からの、大まかな分類方法")

ax.text(2.0, y, "■大原則", fontsize=8, fontweight="bold", ha="left", va="center")
y -= 1.4
ax.text(2.0, y, "・外用薬（のどスプレー、湿布、軟膏等）はすべて濫用防止の対象外。指定成分の抗ヒスタミンは「ジフェンヒドラミンのみ」該当。",
        fontsize=6.5, ha="left", va="center", color=GRAY)
y -= 1.3
ax.text(2.0, y, "・比較的最近の第二世代抗ヒスは皮膚適応なしが基本だが、「ムヒAZ錠」等一部は例外的に皮膚適応を持つ。",
        fontsize=6.5, ha="left", va="center", color=GRAY)
y -= 2.2

ax.text(2.0, y, "■ブランドからの類推（代表例）", fontsize=8, fontweight="bold", ha="left", va="center")
y -= 1.4
brand_lines = [
    ("原則すべて対象:", "ルル、パブロン、ベンザブロック（※パブロンで唯一の非該当は「パブロン50」／ベンザブロックはYASUMO・トローチも対象、対象外はのどスプレーのみ）"),
    ("対象:", "エースがつかないナロン、パイロンPL錠ゴールド、パイロン溶かしてのむかぜ薬"),
    ("すべて対象外:", "セデス、ノーシン、バファリン、イブ"),
]
for label, text in brand_lines:
    ax.text(2.0, y, label, fontsize=6.8, fontweight="bold", ha="left", va="center", color="#333333")
    ax.text(21.0, y, text, fontsize=6.3, ha="left", va="center", color=GRAY)
    y -= 1.5
y -= 0.8

ax.text(2.0, y, "■成分からの判別ポイント（指定8成分 vs 紛らわしい対象外成分）", fontsize=8, fontweight="bold", ha="left", va="center")
y -= 1.6

col_x = [2.0, 20.0, 60.0]
ax.text(col_x[0], y, "分類", fontsize=6.8, fontweight="bold", ha="left", va="center")
ax.text(col_x[1], y, "対象（🔴規制あり）", fontsize=6.8, fontweight="bold", ha="left", va="center", color=RED)
ax.text(col_x[2], y, "対象外（🟢規制なし）", fontsize=6.8, fontweight="bold", ha="left", va="center", color="#2e7d32")
y -= 1.3
ax.hlines(y, 0, LOGICAL_W, colors="#eeeeee", linewidth=0.6)
y -= 1.5

ingr_rows = [
    ("中枢神経興奮\n（アッパー系）", "エフェドリン・メチルエフェドリン\nプソイドエフェドリン",
     "生薬マオウ（葛根湯等）※対象外\n無水カフェイン（アンナカ等）※急性期事象の主因"),
    ("中枢神経抑制\n（ダウナー系）", "コデイン・ジヒドロコデイン\nデキストロメトルファン・ジフェンヒドラミン\nブロモバレリル尿素",
     "クロルフェニラミン・プロメタジン・アゼラスチン\nアリルイソプロピルアセチル尿素 ※MOHの主因"),
]
for label, red_text, green_text in ingr_rows:
    ax.text(col_x[0], y, label, fontsize=6.3, ha="left", va="top")
    ax.text(col_x[1], y, red_text, fontsize=6.3, ha="left", va="top", color=GRAY)
    ax.text(col_x[2], y, green_text, fontsize=6.3, ha="left", va="top", color=GRAY)
    y -= 3.6

y -= 1.0
ax.hlines(y, 0, LOGICAL_W, colors="#dddddd", linewidth=0.8)
y -= 2.2

# ==========================================================
# D. 医療エビデンス
# ==========================================================
y = section_title(ax, y, "【医療エビデンス】過量服薬タイムライン上の致死リスク／薬剤乱用頭痛（MOH）")

evidence = [
    ("初日：急性心毒性（無水カフェイン等）",
     "致死的な不整脈や痙攣を引き起こし、救急搬送中やICU搬入直後に亡くなるケースが大半。"),
    ("3日目以降：遅延性劇症肝不全（アセトアミノフェン）",
     "24〜48時間は無症状〜軽微な胃腸症状のみで危機感を抱きにくいが、3〜5日目に致命的な劇症肝不全へ急速悪化。アルコール併用は解毒機能を失わせリスクを跳ね上げる。"),
    ("薬剤乱用頭痛（MOH）への進展",
     "アリルイソプロピルアセチル尿素等の複合鎮痛薬の慢性過量摂取が誘発。頭痛悪化を原疾患増悪と誤認し鎮痛薬を増やす悪循環。月10日以上・3ヶ月超の定期服用で進展しやすい。"),
]
for title, detail in evidence:
    ax.text(2.0, y, "■" + title, fontsize=7.3, fontweight="bold", ha="left", va="center", color="#333333")
    y -= 1.3
    ax.text(3.0, y, detail, fontsize=6.3, ha="left", va="center", color=GRAY)
    y -= 1.7

y -= 0.8
ax.hlines(y, 0, LOGICAL_W, colors="#dddddd", linewidth=0.8)
y -= 2.2

# ==========================================================
# E. 授乳婦指導早見表
# ==========================================================
y = section_title(ax, y, "【授乳婦指導早見表】実践4ステップ（Hale's L分類・成育医療センター基準準拠）")

nursing_x = [2.0, 16.0, 62.0]
nursing_rows = [
    ("🟢 通常授乳可", "直前授乳で制限なし。母乳移行量は極めて微量。", "アセトアミノフェン／イブプロフェン／無水カフェイン（通常量）／カルボシステイン・葛根湯"),
    ("🟡 ピーク回避", "服薬直前に授乳し、その後2〜4時間は授乳回避（血中濃度ピーク帯を避ける）。", "デキストロメトルファン／dl-メチルエフェドリン／ジフェンヒドラミン（短期）"),
    ("🔴 搾乳破棄", "直接授乳を中止し搾乳して破棄。半減期×3〜4時間経過までミルクで代替。", "クロルフェニラミン（長期）／プロメタジン／ブロモバレリル尿素"),
    ("⛔ 代替薬提案", "授乳中は服用を避け安全な成分・処方薬へ変更。モルヒネ代謝物の乳児移行リスクあり。", "コデインリン酸塩／ジヒドロコデインリン酸塩 →非麻薬性鎮咳薬等へ変更提案"),
]
for tag, action, ingr in nursing_rows:
    ax.text(nursing_x[0], y, tag, fontsize=7.0, fontweight="bold", ha="left", va="top")
    ax.text(nursing_x[1], y, action, fontsize=6.3, ha="left", va="top", color=GRAY)
    ax.text(nursing_x[2], y, ingr, fontsize=6.0, ha="left", va="top", color=GRAY)
    y -= 2.6

y -= 1.0
ax.hlines(y, 0, LOGICAL_W, colors="#dddddd", linewidth=0.8)
y -= 2.2

# ==========================================================
# F. 免責事項
# ==========================================================
y = section_title(ax, y, "免責事項および販売制限の理由・確認業務の根拠")
disclaimer_text = (
    "医薬品の販売に際し、販売個数・容量の確認やご購入理由のお伺いなどご面倒をおかけしています。"
    "かつて安全確認が不十分なまま販売され、規定量を上回る自己判断の服用により身体への致命的な損傷に至った事例が実際にありました。"
    "過去の事例から学び、同じ事象を繰り返さないことが今回の販売制限の目的です。"
    "市販薬には厚労省の厳格な配合・最大量のルールがあり、用法用量を守ることで最大効果・最小副作用が達成されます。"
    "意図的な過量服薬による健康被害はメーカー保証・国の救済制度の対象外となるため、複数の薬の同時服用も自己責任となり、飲み合わせ等の確認が必要です。"
)
ax.text(2.0, y, disclaimer_text, fontsize=6.3, ha="left", va="top", color=GRAY, wrap=True)

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches="tight")
plt.close()

print("==========================================")
print("2ページ目（詳細参考資料） 生成完了")
print(f"出力ファイル: {OUTPUT_PNG}")
print("==========================================")