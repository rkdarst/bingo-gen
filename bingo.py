import random
import math
from typing import List

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
from matplotlib import transforms

# --- User inputs: replace these five lists with your content ---
COL1 = ["Apple", "Apricot", "Avocado", "Almond", "Artichoke", "Asparagus"]
COL2 = ["Banana", "Blueberry", "Blackberry", "Broccoli", "Beet", "Bok choy"]
COL3 = ["Cherry", "Cranberry", "Cucumber", "Carrot", "Cauliflower", "Celery"]
COL4 = ["Date", "Dragonfruit", "Durian", "Dill", "Daikon", "Dulse"]
COL5 = ["Elderberry", "Eggplant", "Endive", "Edamame", "Escarole", "Enoki"]

TITLE = "SciComp Bingo"
INSTRUCTIONS = "Talk to people and mark off items when you find someone that matches the point.  There is no real rules here, if someone can tell a story about the topic of the cell, consider it good enough."

OUTPUT_FILENAME = "bingo_board.pdf"
# ----------------------------------------------------------------

A4_W_INCH = 8.27
A4_H_INCH = 11.69
FONT = "Lato"

def _fit_text_in_bbox(ax, text, bbox_xy, bbox_wh, fontname=FONT,
                      fontstyle='normal', weight='normal',
                      max_fontsize=40, min_fontsize=4, line_spacing=1.1,
                      ha='center', va='center'):
    """
    Draw `text` (possibly multiline) into the rectangle defined by bbox_xy (x,y in axes coords)
    and bbox_wh (w,h in axes coords) on axes `ax`. Fontsize is reduced until text fits.
    Returns the Text artist.
    """
    x, y = bbox_xy
    w, h = bbox_wh

    # start from max fontsize, try to reduce until bounding box fits
    fontsize = max_fontsize
    # use fig DPI and axes transform to convert axes coords to display for measurement
    fig = ax.figure
    renderer = fig.canvas.get_renderer()

    # prepare a candidate text with center alignment and multiline
    while fontsize >= min_fontsize:
        txt = ax.text(x + w / 2, y + h / 2, text,
                      fontsize=fontsize, fontname=fontname, fontstyle=fontstyle,
                      fontweight=weight, ha=ha, va=va, wrap=True, linespacing=line_spacing,
                      transform=ax.transAxes)
        fig.canvas.draw_idle()
        bbox = txt.get_window_extent(renderer=renderer)
        # convert bbox_wh in axes coords to display coordinates
        trans = ax.transAxes + fig.dpi_scale_trans
        # Alternative robust conversion: transform axes rect corners to display coords
        ax0 = ax.transAxes.transform((x, y))
        ax1 = ax.transAxes.transform((x + w, y + h))
        disp_w = abs(ax1[0] - ax0[0])
        disp_h = abs(ax1[1] - ax0[1])

        text_w, text_h = bbox.width, bbox.height

        if text_w <= disp_w + 1 and text_h <= disp_h + 1:
            return txt  # fits
        txt.remove()
        fontsize -= 1

    # If nothing fits, return the smallest fontsize text (still may overflow)
    return ax.text(x + w / 2, y + h / 2, text,
                   fontsize=min_fontsize, fontname=fontname, fontstyle=fontstyle,
                   fontweight=weight, ha=ha, va=va, wrap=True, linespacing=line_spacing,
                   transform=ax.transAxes)
def _fit_text_in_bbox(ax, text, bbox_xy, bbox_wh, fontname='DejaVu Sans',
                      fontstyle='normal', weight='normal',
                      max_fontsize=40, min_fontsize=4, line_spacing=1.05,
                      ha='center', va='center'):
    """
    Place `text` (single-line input) into rectangle defined by bbox_xy (x,y in axes coords)
    and bbox_wh (w,h in axes coords) on axes `ax`. Automatically wraps on spaces and
    lowers fontsize until wrapped text fits. Returns the Text artist.
    """
    x, y = bbox_xy
    w, h = bbox_wh
    fig = ax.figure
    renderer = fig.canvas.get_renderer()

    # helper: measure a candidate multiline string at a given fontsize
    def _measured_size(multiline_str, fontsize):
        # create a temporary Text artist off-screen (use transform=ax.transAxes)
        txt = ax.text(x + w / 2, y + h / 2, multiline_str,
                      fontsize=fontsize, fontname=fontname, fontstyle=fontstyle,
                      fontweight=weight, ha=ha, va=va, linespacing=line_spacing,
                      transform=ax.transAxes)
        fig.canvas.draw_idle()
        bbox = txt.get_window_extent(renderer=renderer)
        txt.remove()
        # get display size of axes bbox
        ax0 = ax.transAxes.transform((x, y))
        ax1 = ax.transAxes.transform((x + w, y + h))
        disp_w = abs(ax1[0] - ax0[0])
        disp_h = abs(ax1[1] - ax0[1])
        return bbox.width, bbox.height, disp_w, disp_h

    # word list for wrapping
    words = text.split()
    if not words:
        return ax.text(x + w / 2, y + h / 2, text,
                       fontsize=min_fontsize, fontname=fontname,
                       fontstyle=fontstyle, fontweight=weight,
                       ha=ha, va=va, transform=ax.transAxes)

    # Try decreasing fontsize; for each fontsize, attempt greedy wrapping into minimal lines
    fontsize = max_fontsize
    while fontsize >= min_fontsize:
        # Determine max characters-per-line indirectly by greedy building lines:
        lines = []
        cur_line = words[0]
        for word in words[1:]:
            candidate = cur_line + " " + word
            # measure candidate width only (single-line height not needed here)
            tw, th, disp_w, disp_h = _measured_size(candidate, fontsize)
            if tw <= disp_w + 1:
                cur_line = candidate
            else:
                lines.append(cur_line)
                cur_line = word
        lines.append(cur_line)
        multiline = "\n".join(lines)

        text_w, text_h, disp_w, disp_h = _measured_size(multiline, fontsize)

        # Allow small epsilon
        if text_w <= disp_w + 1 and text_h <= disp_h + 1:
            # create final text artist and return
            txt_artist = ax.text(x + w / 2, y + h / 2, multiline,
                                 fontsize=fontsize, fontname=fontname, fontstyle=fontstyle,
                                 fontweight=weight, ha=ha, va=va, linespacing=line_spacing,
                                 transform=ax.transAxes)
            return txt_artist

        fontsize -= 1

    # If nothing fit, return smallest fontsize with best-effort wrapping at min_fontsize
    # produce greedy wrapping at min_fontsize
    fontsize = min_fontsize
    lines = []
    cur_line = words[0]
    for word in words[1:]:
        candidate = cur_line + " " + word
        tw, th, disp_w, disp_h = _measured_size(candidate, fontsize)
        if tw <= disp_w + 1:
            cur_line = candidate
        else:
            lines.append(cur_line)
            cur_line = word
    lines.append(cur_line)
    multiline = "\n".join(lines)
    return ax.text(x + w / 2, y + h / 2, multiline,
                   fontsize=fontsize, fontname=fontname, fontstyle=fontstyle,
                   fontweight=weight, ha=ha, va=va, linespacing=line_spacing,
                   transform=ax.transAxes)


def create_bingo_pdf(out_pdf: PdfPages,
                     col1: List[str], col2: List[str], col3: List[str],
                     col4: List[str], col5: List[str],
                     title: str, instructions: str,
                     ):
    # Randomize each column list independently and take first 5 items
    random.shuffle(col1)
    random.shuffle(col2)
    random.shuffle(col3)
    random.shuffle(col4)
    random.shuffle(col5)
    cols = [col1[:5], col2[:5], col3[:5], col4[:5], col5[:5]]

    # make center a "FREE" square
    cols[2][2] = "FREE"

    fig = plt.figure(figsize=(A4_W_INCH, A4_H_INCH), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis('off')

    # Title area (top)
    top_margin = 0.06
    title_box_height = 0.08
    instr_box_height = 0.08
    grid_top = 1 - (top_margin + title_box_height + instr_box_height + 0.02)
    grid_left = 0.17
    grid_right = 1 - grid_left
    grid_width = grid_right - grid_left
    grid_height = grid_top - 0.07  # leave bottom margin
    # use square cells: determine cell size based on width
    cell_size = min(grid_width / 5, grid_height / 5)
    grid_height = cell_size * 5
    grid_bottom = grid_top - grid_height

    # Draw title box
    title_x = 0.05
    title_y = 1 - top_margin - title_box_height
    title_w = 0.9
    title_h = title_box_height
    ax.add_patch(Rectangle((title_x, title_y), title_w, title_h,
                           transform=ax.transAxes, facecolor='none', edgecolor='none'))
    _fit_text_in_bbox(ax, title, (title_x, title_y), (title_w, title_h),
                      max_fontsize=36, min_fontsize=8, fontname=FONT,
                      weight='bold', line_spacing=1.0)

    # Draw instruction box under title
    instr_x = title_x
    instr_y = title_y - instr_box_height - 0.005
    instr_w = title_w
    instr_h = instr_box_height
    # draw light rectangle background for instructions
    ax.add_patch(Rectangle((instr_x, instr_y), instr_w, instr_h,
                           transform=ax.transAxes, facecolor='#f2f2f2',
                           edgecolor='0.7', linewidth=0.8))
    _fit_text_in_bbox(ax, instructions, (instr_x + 0.005, instr_y + 0.005),
                      (instr_w - 0.01, instr_h - 0.01), max_fontsize=12, min_fontsize=6,
                      fontname=FONT, weight='normal', line_spacing=1.0)

    # Grid drawing: draw 5x5 squares
    left = grid_left
    bottom = grid_bottom
    cell_w = cell_h = cell_size

    # Draw outer border
    ax.add_patch(Rectangle((left, bottom), cell_w * 5, cell_h * 5,
                           transform=ax.transAxes, facecolor='none',
                           edgecolor='black', linewidth=1.5))

    # vertical and horizontal lines
    for i in range(1, 5):
        # vertical
        ax.add_line(plt.Line2D([left + i * cell_w, left + i * cell_w],
                               [bottom, bottom + 5 * cell_h],
                               transform=ax.transAxes, color='black', linewidth=1))
        # horizontal
        ax.add_line(plt.Line2D([left, left + 5 * cell_w],
                               [bottom + i * cell_h, bottom + i * cell_h],
                               transform=ax.transAxes, color='black', linewidth=1))

    # Column headers (B I N G O) centered above columns
    #headers = list(title.replace(" ", "")) if len(title.replace(" ", "")) >= 5 else ["B","I","N","G","O"]
    #for col_idx in range(5):
    #    hx = left + col_idx * cell_w
    #    hy = bottom + 5 * cell_h + 0.005
    #    _fit_text_in_bbox(ax, headers[col_idx], (hx, hy), (cell_w, 0.03),
    #                      max_fontsize=24, min_fontsize=8, fontname=FONT,
    #                      weight='bold')

    # Fill cells with fitted text
    for r in range(5):
        for c in range(5):
            x = left + c * cell_w
            y = bottom + (4 - r) * cell_h  # r=0 is top row visually
            cell_text = cols[c][r]
            # center cell background optional
            if r == 2 and c == 2:
                # highlight FREE cell
                ax.add_patch(Rectangle((x, y), cell_w, cell_h,
                                       transform=ax.transAxes, facecolor='#e6ffe6', edgecolor='none'))
            # draw thin inner rect border for cell (so overall border remains bold)
            ax.add_patch(Rectangle((x, y), cell_w, cell_h,
                                   transform=ax.transAxes, facecolor='none', edgecolor='black', linewidth=0.6))
            pad = 0.01
            _fit_text_in_bbox(ax, cell_text, (x + pad, y + pad), (cell_w - 2 * pad, cell_h - 2 * pad),
                              max_fontsize=24, min_fontsize=6, fontname=FONT, line_spacing=1.05)

    # Save to PDF
    #with PdfPages(out_pdf) as pdf:
    out_pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved bingo board to {pdf}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('n', type=int)
    parser.add_argument('output', nargs='?', default=OUTPUT_FILENAME)
    args = parser.parse_args()

    import csv
    data = list(csv.reader(open(args.input)))[1:]  # skip header
    print(data)
    COL1 = list(filter(None, list(zip(*data))[0]))
    COL2 = list(filter(None, list(zip(*data))[1]))
    COL3 = list(filter(None, list(zip(*data))[2]))
    COL4 = list(filter(None, list(zip(*data))[3]))
    COL5 = list(filter(None, list(zip(*data))[4]))


    with PdfPages(args.output) as pdf:
        for _ in range(args.n):
            create_bingo_pdf(pdf, COL1, COL2, COL3, COL4, COL5, TITLE, INSTRUCTIONS)
