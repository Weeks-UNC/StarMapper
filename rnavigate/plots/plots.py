from abc import ABC, abstractmethod
import math
import matplotlib as mp
import matplotlib.pyplot as plt
import numpy as np
from rnavigate import styles


class Plot(ABC):
    def __init__(self, num_samples, rows=None, cols=None, figsize=None, **kwargs):
        self.length = num_samples
        self.rows, self.columns = self.get_rows_columns(rows, cols)
        if figsize is None:
            figsize = self.get_figsize()
        self.fig, self.axes = plt.subplots(
            self.rows, self.columns, figsize=figsize, squeeze=False, **kwargs
        )
        self.i = 0
        self.pass_through = []
        self.colorbars = []

    def get_ax(self, i=None):
        if i is None:
            i = self.i
        row = i // self.columns
        col = i % self.columns
        return self.axes[row, col]

    def add_colorbar_args(self, interactions):
        cmap = interactions.cmap
        for colorbar in self.colorbars:
            if cmap.is_equivalent_to(colorbar):
                break
        else:
            self.colorbars.append(cmap)

    def plot_colorbars(self):
        rows = len(self.colorbars)
        if rows == 0:
            return (None, None)
        fig, axes = plt.subplots(rows, 1, figsize=(4, 1.5 * rows), squeeze=False)
        for cbar, axis in zip(self.colorbars, axes[:, 0]):
            colorbar = plt.colorbar(cbar, cax=axis, orientation="horizontal",
                         **cbar.cbar_args)
            colorbar.outline.set_visible(False)
        plt.tight_layout()
        return (fig, axes)

    @classmethod
    def view_colormap(self, axis=None, interactions=None, ticks=None,
                      values=None, title=None, cmap=None):
        if interactions is not None:
            cbargs = self.get_colorbar_args(interactions=interactions)
        if (None in [ticks, values, title, cmap]) and (cbargs is None):
            return
        if ticks is None:
            ticks = cbargs["ticks"]
        if values is None:
            values = cbargs["values"]
        if title is None:
            title = cbargs["title"]
        if cmap is None:
            cmap = cbargs["cmap"]
        if isinstance(cmap, str):
            cmap = plt.get_cmap(cmap)
            cmap = cmap(np.arange(cmap.N)).tolist()

        if axis is None:
            _, axis = plt.subplots(1, figsize=(6, 2))
        axis.imshow([cmap], extent=[0, 10, 0, 1])
        axis.set_title(title)
        axis.set_xticks(ticks)
        axis.set_xticklabels(values)
        axis.set_yticks([])
        return axis

    def get_rows_columns(self, rows=None, cols=None):
        has_rows = isinstance(rows, int)
        has_cols = isinstance(cols, int)
        if has_rows and has_cols:
            return rows, cols
        elif has_rows:
            cols = math.ceil(self.length / rows)
        elif has_cols:
            rows = math.ceil(self.length / cols)
        elif self.length < 10:
            rows, cols = [
                (0, 0),
                (1, 1),
                (1, 2),
                (1, 3),
                (2, 2),
                (2, 3),
                (2, 3),
                (3, 3),
                (3, 3),
                (3, 3),
            ][self.length]
        else:
            cols = 4
            rows = math.ceil(self.length / cols)
        return rows, cols

    def add_sequence(self, axis, sequence, yvalue=0, ytrans="axes"):
        # set font style and colors for each nucleotide
        font_prop = mp.font_manager.FontProperties(
            family="monospace", style="normal", weight="bold", size="12"
        )
        # transform yvalue to a y-axis data value
        if ytrans == "axes":
            trans = axis.get_xaxis_transform()
        elif ytrans == "data":
            trans = axis.transData
        sequence = sequence[self.region[0] - 1 : self.region[1]]
        for i, seq in enumerate(sequence):
            col = styles.get_nt_color(seq, colors="old")
            axis.text(
                i + self.region[0],
                yvalue,
                seq,
                fontproperties=font_prop,
                transform=trans,
                color=col,
                horizontalalignment="center",
                verticalalignment="center",
            )

    @abstractmethod
    def get_figsize(self):
        pass

    @abstractmethod
    def plot_data(self):
        pass

    def save(self, filename):
        """Saves the figure to a file

        Args:
            filename (str):
                A file path to write to. The file format is provided by this
                file extension (svg, pdf, or png).
        """
        self.fig.savefig(filename)

    def set_figure_size(
        self,
        fig=None,
        axis=None,
        rows=None,
        cols=None,
        height_ax_rel=None,
        width_ax_rel=None,
        width_ax_in=None,
        height_ax_in=None,
        height_gap_in=None,
        width_gap_in=None,
        top_in=None,
        bottom_in=None,
        left_in=None,
        right_in=None,
    ):
        """Sets figure size so that axes sizes are always consistent.

        Args:
            height_ax_rel (float, optional): axis unit to inches ratio for the
                y-axis.
            width_ax_rel (float, optional): axis unit to inches ration for the
                x-axis.
            width_ax_in (float, optional): fixed width of each axis in inches
            height_ax_in (float, optional): fixed height of each axis in inches
            width_gap_in (float, optional): fixed width of gaps between each
                axis in inches
            height_gap_in (float, optional): fixed height of gaps between each
                axis in inches
            top_in (float, optional): fixed height of top margin in inches
            bottom_in (float, optional): fixed height of bottom margin in inches
            left_in (float, optional): fixed width of left margin in inches
            right_in (float, optional): fixed width of right margin in inches
        """
        if fig is None:
            fig = self.fig
        if axis is None:
            axis = self.axes[0, 0]
        if rows is None:
            rows = self.rows
        if cols is None:
            cols = self.columns

        if width_ax_in is None:
            # x limits of axes
            left_ax, right_ax = axis.get_xlim()
            # width of axes in inches
            width_ax_in = (right_ax - left_ax) * width_ax_rel
        if width_gap_in is None:
            # get width from relative width * axis width
            width_gap_in = fig.subplotpars.wspace * width_ax_in
        else:
            # set relative width to gap:axis ratio
            fig.subplots_adjust(wspace=width_gap_in / width_ax_in)
        # comput subplot width
        width_subplot_in = width_gap_in * (cols - 1) + width_ax_in * cols
        if right_in is None:
            # get right margin size from relative size * subplot size
            right_in = (1 - fig.subplotpars.right) * width_subplot_in
        else:
            # set relative right side position to 1 - margin:subplot ratio
            fig.subplots_adjust(right=1 - (right_in / (right_in + width_subplot_in)))
        if left_in is None:
            # get left margin size from relative size * subplot size
            left_in = fig.subplotpars.left * width_subplot_in
        else:
            # set relative left side position to margin:subplot ratio
            fig.subplots_adjust(left=left_in / (left_in + width_subplot_in))
        width_fig_in = left_in + width_subplot_in + right_in

        # repeat the process for figure height
        if height_ax_in is None:
            bottom_ax, top_ax = axis.get_ylim()
            height_ax_in = (top_ax - bottom_ax) * height_ax_rel
        if height_gap_in is None:
            height_gap_in = fig.subplotpars.hspace * height_ax_in
        else:
            fig.subplots_adjust(hspace=height_gap_in / height_ax_in)
        height_subplot_in = height_gap_in * (rows - 1) + height_ax_in * rows
        if top_in is None:
            top_in = (1 - fig.subplotpars.top) * height_subplot_in
        else:
            fig.subplots_adjust(top=1 - (top_in / (top_in + height_subplot_in)))
        if bottom_in is None:
            bottom_in = fig.subplotpars.bottom * height_subplot_in
        else:
            fig.subplots_adjust(bottom=bottom_in / (bottom_in + height_subplot_in))
        height_fig_in = top_in + height_subplot_in + bottom_in

        fig.set_size_inches(width_fig_in, height_fig_in)


def adjust_spines(axis, spines):
    for loc, spine in axis.spines.items():
        if loc in spines:
            spine.set_position(("outward", 10))  # outward by 10 points
        else:
            spine.set_color("none")  # don't draw spine
    if "left" in spines:
        axis.yaxis.set_ticks_position("left")
    else:
        axis.yaxis.set_ticks([])
    if "bottom" in spines:
        axis.xaxis.set_ticks_position("bottom")
    else:
        axis.xaxis.set_ticks([])


def clip_spines(axis, spines):
    for spine in spines:
        if spine in ["left", "right"]:
            ticks = axis.get_yticks()
        if spine in ["top", "bottom"]:
            ticks = axis.get_xticks()
        axis.spines[spine].set_bounds((min(ticks), max(ticks)))
