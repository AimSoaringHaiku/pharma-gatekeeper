"""A4印刷時の文字サイズ基準（vpc_v13_page1〜4 共通）。

各ページは figsize=(10, 14.14) インチで描画し、A4（210mm＝8.27インチ幅）に縮小して印刷する。
そのため matplotlib の fontsize（pt）は印刷時に約0.83倍になる。
ここでは「印刷後の実寸pt」で最小サイズを決め、描画用の fontsize に換算して使う。

最小 6pt（印刷実寸）の根拠:
  - 一般的な印刷物で、注記まで含めて読める下限が 6pt 前後（これ未満は虫眼鏡が必要になる）
  - 店頭で毎回読む本文は 7pt 以上を目標とし、6pt は注記・出典など補足情報だけに使う
"""

FIG_W_IN = 10.0
A4_W_IN = 210 / 25.4
PRINT_SCALE = A4_W_IN / FIG_W_IN  # ≒0.827（描画pt → 印刷pt）

MIN_PRINT_PT = 6.0  # 注記・出典を含む全テキストの下限（印刷実寸）
BODY_PRINT_PT = 7.0  # 本文の目標（印刷実寸）


def fs_pt(print_pt):
    """印刷実寸 pt を、描画用の fontsize に換算する。"""
    return print_pt / PRINT_SCALE


MIN_FS = fs_pt(MIN_PRINT_PT)  # ≒7.26
BODY_FS = fs_pt(BODY_PRINT_PT)  # ≒8.47

SOURCE_TEXT = ("準拠: 厚生労働省 局長通知「指定濫用防止医薬品の指定について」/JSMI「指定濫用防止医薬品の販売制度について」"
               "/兵庫県 薬務課 制度改正資料")


def check_min_font(fig, label=""):
    """保存前の最終チェック：印刷実寸で MIN_PRINT_PT 未満の文字が残っていないか確認して表示する。"""
    from matplotlib.text import Text
    scale = A4_W_IN / fig.get_size_inches()[0]
    small = []
    for t in fig.findobj(Text):
        s = t.get_text().strip()
        if s and t.get_visible() and t.get_fontsize() * scale < MIN_PRINT_PT - 0.01:
            small.append((t.get_fontsize() * scale, s))
    if small:
        print(f"⚠ {label} 印刷{MIN_PRINT_PT}pt未満の文字が {len(small)} 箇所あります:")
        for pt, s in sorted(small)[:20]:
            print(f"   {pt:.2f}pt  {s[:50]}")
    else:
        print(f"✓ {label} 全テキストが印刷{MIN_PRINT_PT}pt以上")
    return small


_NO_LINE_START = "。、，．）)」』】〕・ー：；？！ゃゅょっャュョッァィゥェォ"


def wrap_fill(text, fontsize, max_width, text_width):
    """行幅いっぱいまで文字を詰めて折り返す（句読点区切りの折り返しより行数が減る）。
    行頭に句読点・閉じ括弧が来る場合は前の行へ追い込む（簡易禁則）。"""
    lines, cur = [], ""
    for ch in text:
        trial = cur + ch
        if cur and text_width(trial, fontsize) > max_width and ch not in _NO_LINE_START:
            lines.append(cur)
            cur = ch
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines
