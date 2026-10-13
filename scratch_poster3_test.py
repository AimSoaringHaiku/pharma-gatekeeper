import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import japanize_matplotlib

IMG_FLOWCHART = "ref_flowchart.png"
RED = "#d32f2f"

LOGICAL_W, LOGICAL_H = 32.67, 55.0
fig, ax = plt.subplots(figsize=(3.267, 5.5))
ax.set_position([0, 0, 1, 1])
ax.set_xlim(0, LOGICAL_W)
ax.set_ylim(0, LOGICAL_H)
ax.axis("off")
fig.canvas.draw()

_meas_fig, _meas_ax = plt.subplots(figsize=(3.267, 5.5))
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


x, w = 1.0, 30.67
img = mpimg.imread(IMG_FLOWCHART)
img_h_px, img_w_px = img.shape[0], img.shape[1]
aspect = img_w_px / img_h_px
img_w = w
img_h = img_w / aspect
img_x0, img_y1 = x, LOGICAL_H - 1.0
img_y0 = img_y1 - img_h
ax.imshow(img, extent=[img_x0, img_x0 + img_w, img_y0, img_y1], zorder=2)
ax.add_patch(patches.Rectangle((img_x0, img_y0), img_w, img_h, fill=False, edgecolor="#cccccc", linewidth=0.5, zorder=3))

# --- 「必要に応じ」の右の余白に、注釈を1つだけ書き込む ---
# 「販売した後でも申し送りが必要になる場合がある」という、表面のフローには
# ない実務ポイントを補足する。
note_y = img_y1 - 0.838 * img_h
for i, line in enumerate(wrap_to_width("☞販売しても「申し送り」が必要な場合あり", 3.3, w * 0.24)):
    ax.text(img_x0 + img_w * 0.78, note_y - i * 1.3, line, fontsize=3.3, fontweight="bold",
            ha="left", va="center", color=RED, fontstyle="italic", zorder=4)

plt.close(_meas_fig)
fig.savefig("scratch_poster3_test.png", dpi=300)
plt.close(fig)
print("done")
