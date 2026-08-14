import matplotlib.pyplot as plt
import matplotlib.patches as patches
import datetime
import japanize_matplotlib  # 文字化け（豆腐）解消のためのインポートを追加

OUTPUT_PNG = "atomic_card_table_v8_page2.png"

# A4完全固定レイアウト
LOGICAL_W = 100.0
LOGICAL_H = 141.4

fig, ax = plt.subplots(figsize=(10, 14.14))
ax.set_xlim(0, LOGICAL_W)
ax.set_ylim(0, LOGICAL_H)
ax.axis("off")

# --- タイトル ---
current_y = LOGICAL_H - 4.0
ax.text(LOGICAL_W / 2, current_y, "薬剤別 包装区分 早見表 (2/2) 詳細参考資料", fontsize=18, fontweight="bold", ha="center", va="center")

today_str = datetime.date.today().strftime("%Y/%m/%d")
ax.text(LOGICAL_W - 2.0, current_y + 1.8, f"更新日: {today_str}", fontsize=8, ha="right", va="center", color="#888888")

current_y -= 2.6
ax.text(LOGICAL_W / 2, current_y, "※1ページ目の早見表で「小/大包装・年齢」まで判別できます。本ページは法的根拠および対応時の専門的参考資料です。", 
        fontsize=7.5, ha="center", va="center", color="#555555")

current_y -= 2.0
ax.hlines(current_y, 2.0, LOGICAL_W - 2.0, colors="#1565c0", linewidth=1.5)
current_y -= 4.0

def draw_section_title(ax, y, text):
    ax.text(2.0, y, text, fontsize=12, fontweight="bold", ha="left", va="center")
    return y - 3.0

# ==========================================================
# 1. 計算手順
# ==========================================================
current_y = draw_section_title(ax, current_y, "【計算手順】 基準日数の把握と消費日数の割り出し")

ax.text(3.0, current_y, "STEP 1:", fontsize=9, fontweight="bold", color="#1565c0")
ax.text(12.0, current_y, "薬の分類を確認し、基準日数を把握する（総合感冒薬・解熱鎮痛薬・鼻炎用内服薬＝7日分 ／ 鎮咳去痰薬＝5日分）", fontsize=9)
current_y -= 2.5

ax.text(3.0, current_y, "STEP 2:", fontsize=9, fontweight="bold", color="#1565c0")
ax.text(12.0, current_y, "成人（15歳以上）の「1日最大服用量」を確認する", fontsize=9)
current_y -= 2.5

ax.text(3.0, current_y, "STEP 3:", fontsize=9, fontweight="bold", color="#1565c0")
ax.text(12.0, current_y, "パッケージ総量が「何日分」か計算する（パッケージ総量 ÷ 1日最大服用量 ＝ 消費日数）", fontsize=9)
current_y -= 2.5

ax.text(3.0, current_y, "STEP 4:", fontsize=9, fontweight="bold", color="#1565c0")
ax.text(12.0, current_y, "基準日数と照らして容量区分を判定する（消費日数が基準日数以下 ＝ 小容量 ／ 基準日数超 ＝ 大容量）", fontsize=9)

current_y -= 4.0
ax.hlines(current_y, 2.0, LOGICAL_W - 2.0, colors="#cccccc", linewidth=0.8, linestyle="--")
current_y -= 4.0

# ==========================================================
# 2. 販売ルールのまとめ
# ==========================================================
current_y = draw_section_title(ax, current_y, "【早見表】 正しい販売ルールのまとめ（小容量1個・大容量の対応）")

# テーブルヘッダー
ax.add_patch(patches.Rectangle((2.0, current_y - 1.5), 96.0, 3.0, facecolor="#f5f5f5", edgecolor="none"))
ax.text(5.0, current_y, "購入者の年齢", fontsize=9, fontweight="bold")
ax.text(25.0, current_y, "購入する容量", fontsize=9, fontweight="bold")
ax.text(45.0, current_y, "氏名・年齢の確認", fontsize=9, fontweight="bold")
ax.text(65.0, current_y, "他店購入状況確認", fontsize=9, fontweight="bold")
ax.text(85.0, current_y, "販売の可否", fontsize=9, fontweight="bold")
current_y -= 3.5

# レコード1
ax.text(5.0, current_y, "18歳未満", fontsize=9)
ax.text(25.0, current_y, "小容量（1個）", fontsize=9)
ax.text(45.0, current_y, "必須（身分証等）", fontsize=9, fontweight="bold")
ax.text(65.0, current_y, "必須", fontsize=9, fontweight="bold")
ax.text(85.0, current_y, "条件を満たせば販売可", fontsize=9)
current_y -= 2.5

# レコード2
ax.text(5.0, current_y, "18歳以上", fontsize=9)
ax.text(25.0, current_y, "小容量（1個）", fontsize=9)
ax.text(45.0, current_y, "原則不要", fontsize=9)
ax.text(65.0, current_y, "必須", fontsize=9, fontweight="bold")
ax.text(85.0, current_y, "通常通り販売可", fontsize=9)
current_y -= 3.0

ax.text(2.0, current_y, "※ 薬機法により18歳未満のお客様へは大容量および複数個の販売が禁止されています。", fontsize=8.5, color="#d32f2f")

current_y -= 4.0
ax.hlines(current_y, 2.0, LOGICAL_W - 2.0, colors="#cccccc", linewidth=0.8, linestyle="--")
current_y -= 4.0

# ==========================================================
# 3. 医療エビデンス (Fact-based)
# ==========================================================
current_y = draw_section_title(ax, current_y, "【医療エビデンス】 過量服薬における致死リスクおよび薬剤乱用頭痛（MOH）")

ax.text(2.0, current_y, "■ 急性中毒および致死量（アセトアミノフェン等）", fontsize=9.5, fontweight="bold")
current_y -= 2.0
ax.text(4.0, current_y, "成人の急性中毒量は通常7.5g以上、致死量は10-15g以上とされています。過量摂取により重篤な肝機能障害を引き起こすリスクがあります。", fontsize=8.5)
current_y -= 3.0

ax.text(2.0, current_y, "■ カフェインの過量摂取", fontsize=9.5, fontweight="bold")
current_y -= 2.0
ax.text(4.0, current_y, "過量摂取により神経過敏、不眠、動悸、頻脈、不整脈、痙攣などを引き起こす可能性があります。", fontsize=8.5)
current_y -= 3.0

ax.text(2.0, current_y, "■ 薬剤乱用頭痛（MOH）の進展", fontsize=9.5, fontweight="bold")
current_y -= 2.0
ax.text(4.0, current_y, "鎮痛成分等を週に3日以上、3ヶ月以上連用した場合、薬剤乱用頭痛（MOH）を引き起こす可能性があります。", fontsize=8.5)

current_y -= 4.0
ax.hlines(current_y, 2.0, LOGICAL_W - 2.0, colors="#cccccc", linewidth=0.8, linestyle="--")
current_y -= 4.0

# ==========================================================
# 4. 授乳婦指導
# ==========================================================
current_y = draw_section_title(ax, current_y, "【授乳婦指導早見表】 推奨および注意喚起（L分類相当）")

# L1/L2相当
ax.add_patch(patches.Circle((3.5, current_y), 0.8, color="#2e7d32"))
ax.text(6.0, current_y, "通常推奨 (L1/L2相当)", fontsize=9, fontweight="bold")
current_y -= 1.8
ax.text(6.0, current_y, "アセトアミノフェンは通常のOTC用量であれば母子ともに安全性が極めて高いとされています。第一選択として推奨されます。", fontsize=8.5)
current_y -= 3.0

# L3相当
ax.add_patch(patches.Circle((3.5, current_y), 0.8, color="#f57c00"))
ax.text(6.0, current_y, "相談・注意 (L3相当)", fontsize=9, fontweight="bold")
current_y -= 1.8
ax.text(6.0, current_y, "デキストロメトルファンは通常量であれば安全とされますが、乳児の呼吸抑制に注意が必要です。プロメタジンは乳児の傾眠リスクがあります。", fontsize=8.5)
current_y -= 3.0

# 禁忌等
ax.add_patch(patches.Circle((3.5, current_y), 0.8, color="#d32f2f"))
ax.text(6.0, current_y, "代替薬推奨", fontsize=9, fontweight="bold")
current_y -= 1.8
ax.text(6.0, current_y, "禁忌成分（サリチルアミド等）を含む場合、または影響が懸念される場合は、アセトアミノフェン単剤等への切り替えを推奨してください。", fontsize=8.5)

current_y -= 4.0
ax.hlines(current_y, 2.0, LOGICAL_W - 2.0, colors="#cccccc", linewidth=0.8, linestyle="--")
current_y -= 4.0

# ==========================================================
# 5. 免責事項・販売制限の根拠
# ==========================================================
current_y = draw_section_title(ax, current_y, "【免責事項および販売制限の根拠】")

ax.text(2.0, current_y, 
        "本システム（本資料を含む）は、入力情報に基づく個別具体的な医療判断・診断・処方監査を行うプログラム医療機器（SaMD）ではありません。\n"
        "事前に登録されたマスタ情報を表示する電子辞書機能であり、小容量1個の販売時であっても、18歳未満には「氏名・年齢の確認」、\n"
        "成人には「他店での直近購入状況の確認」が法令上必須となります。\n\n"
        "最終的な販売可否や服薬指導は、関係法令（医薬品医療機器等法）を遵守し、現場の資格職の専門的知見に基づき実施してください。", 
        fontsize=8.5, ha="left", va="top", linespacing=1.6)

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=300, bbox_inches="tight")
plt.close()

print("==========================================")
print("ページ2（詳細参考資料 - フラット化版・文字化け修正済） 生成完了")
print(f"出力ファイル: {OUTPUT_PNG}")
print("==========================================")