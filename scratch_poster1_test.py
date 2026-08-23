import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import japanize_matplotlib

IMG_POSTER1 = "ref_poster_kounyusha.png"
RED, GRAY = "#d32f2f", "#555555"

LOGICAL_W, LOGICAL_H = 60.0, 90.0
fig, ax = plt.subplots(figsize=(6, 9))
ax.set_position([0, 0, 1, 1])
ax.set_xlim(0, LOGICAL_W)
ax.set_ylim(0, LOGICAL_H)
ax.axis("off")
fig.canvas.draw()

_meas_fig, _meas_ax = plt.subplots(figsize=(6, 9))
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


def draw_callout_marker(x, y, num, color=RED, r=1.3, fs=7.0):
    ax.add_patch(patches.Circle((x, y), r, facecolor=color, edgecolor="white", linewidth=0.7, zorder=5))
    ax.text(x, y, str(num), fontsize=fs, fontweight="bold", ha="center", va="center", color="white", zorder=6)


POSTER1_CALLOUTS = [
    (0.135, "薬局側がまず伝える第一声（濫用のリスク説明）"),
    (0.315, "★最重要：18歳未満は複数個・大容量NG（表面①と同じ内容）"),
    (0.44, "レジで確認する法的根拠一覧（表面の必須質問に対応）"),
    (0.665, "販売時に必ず説明する5項目"),
]

x, y_top, w = 3.0, LOGICAL_H - 2.0, LOGICAL_W - 6.0

ax.text(x + w / 2, y_top, "【試作】参考① 記述層＋解釈層", fontsize=10, fontweight="bold", ha="center", va="center")
y = y_top - 2.5

img_pad_left = 4.5
img_w = w - img_pad_left - 1.0
img = mpimg.imread(IMG_POSTER1)
img_h_px, img_w_px = img.shape[0], img.shape[1]
aspect = img_w_px / img_h_px
img_h = img_w / aspect
img_x0 = x + img_pad_left
img_y1 = y
img_y0 = img_y1 - img_h
ax.imshow(img, extent=[img_x0, img_x0 + img_w, img_y0, img_y1], zorder=2)
ax.add_patch(patches.Rectangle((img_x0, img_y0), img_w, img_h, fill=False, edgecolor="#cccccc", linewidth=0.8, zorder=3))

for i, (rel_y, _c) in enumerate(POSTER1_CALLOUTS, start=1):
    marker_y = img_y1 - rel_y * img_h
    draw_callout_marker(img_x0 - 2.2, marker_y, i)

y = img_y0 - 2.0
ax.text(x, y, "【解釈】このポスターの読み方", fontsize=7.5, fontweight="bold", ha="left", va="center", color=GRAY)
y -= 1.8
comment_fs = 7.0
for i, (_rel_y, comment) in enumerate(POSTER1_CALLOUTS, start=1):
    wrapped = wrap_to_width(comment, comment_fs, w - 6.0)
    draw_callout_marker(x + 1.5, y, i, r=1.1, fs=6.2)
    for wi, line in enumerate(wrapped):
        ax.text(x + 3.5, y - wi * 1.6, line, fontsize=comment_fs, ha="left", va="center", color="#333333")
    y -= max(1.9, 1.6 * len(wrapped)) + 0.4

plt.close(_meas_fig)
fig.savefig("scratch_poster1_test.png", dpi=200)
plt.close(fig)
print("done. final y =", y, "(logical bottom = 0)")
