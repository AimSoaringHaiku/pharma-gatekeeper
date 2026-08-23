import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import japanize_matplotlib

IMG_POSTER1 = "ref_poster_kounyusha.png"
RED = "#d32f2f"
INK = "#1a1a1a"  # 手書きメモ風の黒インク色

LOGICAL_W, LOGICAL_H = 70.0, 90.0
fig, ax = plt.subplots(figsize=(7, 9))
ax.set_position([0, 0, 1, 1])
ax.set_xlim(0, LOGICAL_W)
ax.set_ylim(0, LOGICAL_H)
ax.axis("off")
fig.canvas.draw()

_meas_fig, _meas_ax = plt.subplots(figsize=(7, 9))
_meas_ax.set_xlim(0, LOGICAL_W)
_meas_ax.set_ylim(0, LOGICAL_H)
_meas_ax.axis("off")
_meas_fig.canvas.draw()


def text_width(text, fontsize, weight="normal"):
    t = _meas_ax.text(0, -200, text, fontsize=fontsize, fontweight=weight, ha="left", va="center")
    _meas_fig.canvas.draw()
    bbox = t.get_window_extent(renderer=_meas_fig.canvas.get_renderer())
    inv = _meas_ax.transData.inverted()
    (x0, _), (x1, _) = inv.transform([[bbox.x0, bbox.y0], [bbox.x1, bbox.y1]])
    t.remove()
    return x1 - x0


def wrap_to_width(text, fontsize, max_width):
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


def draw_handwritten_note(x, y, lead, body, fs_lead=7.5, fs_body=5.2, max_w=20.0):
    """手書きメモ風：指差し記号+一番言いたい一言(大)+補足(小)。ジャンプ率で視線誘導。"""
    ax.text(x, y, f"☞ {lead}", fontsize=fs_lead, fontweight="bold", ha="left", va="center", color=RED,
             fontstyle="italic")
    yy = y - fs_lead * 0.14
    for line in wrap_to_width(body, fs_body, max_w):
        ax.text(x + 1.0, yy, line, fontsize=fs_body, ha="left", va="center", color=INK, fontstyle="italic")
        yy -= fs_body * 0.16
    return yy


def draw_arrow(xy_from, xy_to, rad=0.25):
    ax.annotate("", xy=xy_to, xytext=xy_from,
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.3,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=2, shrinkB=2))


x, y_top, w = 3.0, LOGICAL_H - 2.0, LOGICAL_W - 20.0  # 画像は幅を絞り、右に手書きメモ欄を確保

ax.text(x + w / 2 + 8, y_top, "【試作v2】手書きメモ風の書き込み", fontsize=9, fontweight="bold", ha="center", va="center")
y = y_top - 2.2

img = mpimg.imread(IMG_POSTER1)
img_h_px, img_w_px = img.shape[0], img.shape[1]
aspect = img_w_px / img_h_px
img_w = w
img_h = img_w / aspect
img_x0 = x
img_y1 = y
img_y0 = img_y1 - img_h
ax.imshow(img, extent=[img_x0, img_x0 + img_w, img_y0, img_y1], zorder=2)
ax.add_patch(patches.Rectangle((img_x0, img_y0), img_w, img_h, fill=False, edgecolor="#cccccc", linewidth=0.8, zorder=3))

note_x = img_x0 + img_w + 3.0

# --- 書き込み1: 赤枠(18歳未満は複数個・大容量NG)の横に ---
rel_y1 = 0.315
py1 = img_y1 - rel_y1 * img_h
draw_arrow((note_x - 0.5, py1 + 4.0), (img_x0 + img_w - 1.0, py1))
draw_handwritten_note(note_x, py1 + 5.5,
                       "この理由聴取、実は…",
                       "大容量・複数個の理由を聞けるのは18歳以上の場合のみ。18歳未満はそもそも理由に関わらず販売不可。",
                       max_w=LOGICAL_W - note_x - 2.0)

# --- 書き込み2: 情報提供内容⑤の横に ---
rel_y2 = 0.70
py2 = img_y1 - rel_y2 * img_h
draw_arrow((note_x - 0.5, py2 - 4.0), (img_x0 + img_w - 1.0, py2))
draw_handwritten_note(note_x, py2 - 5.5,
                       "⑤だけ毛色が違う",
                       "①〜④は製品の客観情報。⑤は薬剤師の判断が入る唯一の項目（現場の裁量）。",
                       max_w=LOGICAL_W - note_x - 2.0)

plt.close(_meas_fig)
fig.savefig("scratch_poster1_test2.png", dpi=200)
plt.close(fig)
print("done")
