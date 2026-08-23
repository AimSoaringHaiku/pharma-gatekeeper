import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
import japanize_matplotlib

IMG_POSTER1 = "ref_poster_kounyusha.png"
RED = "#d32f2f"
INK = "#1a1a1a"

# 本番と同じ比率・1コマ幅で検証
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
img = mpimg.imread(IMG_POSTER1)
img_h_px, img_w_px = img.shape[0], img.shape[1]
aspect = img_w_px / img_h_px
img_w = w
img_h = img_w / aspect
img_x0, img_y1 = x, LOGICAL_H - 1.0
img_y0 = img_y1 - img_h
ax.imshow(img, extent=[img_x0, img_x0 + img_w, img_y0, img_y1], zorder=2)
ax.add_patch(patches.Rectangle((img_x0, img_y0), img_w, img_h, fill=False, edgecolor="#cccccc", linewidth=0.5, zorder=3))

# --- 画像内の余白（左端）に直接書き込む ---
# 元画像を目視して、左マージンの相対x位置(0=左端)・各注記の相対y位置を見積もる
note_x = img_x0 + img_w * 0.03  # 画像の左端ギリギリ
notes = [
    (0.135, "☞ここが第一声"),
    (0.315, "☞最重要ルール"),
    (0.44, "☞法的根拠"),
]
for rel_y, text in notes:
    ny = img_y1 - rel_y * img_h
    ax.text(note_x, ny, text, fontsize=3.6, fontweight="bold", ha="left", va="center",
            color=RED, fontstyle="italic", zorder=4,
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.75))

# 情報提供内容の右余白（イラスト左上の空きスペース）に書き込む
ax.text(img_x0 + img_w * 0.50, img_y1 - 0.615 * img_h,
        "☞⑤は薬剤師の判断が\n入る唯一の項目", fontsize=3.4, fontweight="bold", ha="left", va="top",
        color=RED, fontstyle="italic", zorder=4,
        bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.75))

plt.close(_meas_fig)
fig.savefig("scratch_poster1_test3.png", dpi=300)
plt.close(fig)
print("done")
