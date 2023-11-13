from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import math



class Plot(ABC):
    def __init__(self, num_samples, rows=None, cols=None, **kwargs):
        self.length = num_samples
        self.rows, self.columns = self.get_rows_columns(rows, cols)
        self.fig, self.axes = plt.subplots(
            self.rows, self.columns, squeeze=False, **kwargs
        )
        self.i = 0
        self.colorbars = []

    def get_ax(self, i=None):
        if i is None:
            i = self.i
        row = i // self.columns
        col = i % self.columns
        return self.axes[row, col]

    def add_colorbar_args(self, cmap):
        if cmap is None:
            return
        for colorbar in self.colorbars:
            if cmap.is_equivalent_to(colorbar):
                break
        else:
            self.colorbars.append(cmap)

    def plot_colorbars(self):
        rows = len(self.colorbars)
        if rows == 0:
            return (None, None)
        plot = ColorBar(rows, rows=rows)
        for colorbar in self.colorbars:
            plot.plot_data(colorbar)
        plot.set_figure_size()
        return plot

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
        ax=None,
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
            height_ax_rel (float, optional): ax unit to inches ratio for the
                y-ax.
            width_ax_rel (float, optional): ax unit to inches ration for the
                x-ax.
            width_ax_in (float, optional): fixed width of each ax in inches
            height_ax_in (float, optional): fixed height of each ax in inches
            width_gap_in (float, optional): fixed width of gaps between each
                ax in inches
            height_gap_in (float, optional): fixed height of gaps between each
                ax in inches
            top_in (float, optional): fixed height of top margin in inches
            bottom_in (float, optional): fixed height of bottom margin in inches
            left_in (float, optional): fixed width of left margin in inches
            right_in (float, optional): fixed width of right margin in inches
        """
        if fig is None:
            fig = self.fig
        if ax is None:
            ax = self.axes[0, 0]
        if rows is None:
            rows = self.rows
        if cols is None:
            cols = self.columns

        try:
            right_ax = ax.get_rmax()
            top_ax = right_ax
            left_ax = right_ax * -1
            bottom_ax = left_ax
        except AttributeError:
            left_ax, right_ax = ax.get_xlim()
            bottom_ax, top_ax = ax.get_ylim()

        if width_ax_in is None:
            # width of axes in inches
            width_ax_in = (right_ax - left_ax) * width_ax_rel
        if width_gap_in is None:
            # get width from relative width * ax width
            width_gap_in = fig.subplotpars.wspace * width_ax_in
        else:
            # set relative width to gap:ax ratio
            fig.subplots_adjust(wspace=width_gap_in / width_ax_in)
        # comput subplot width
        width_subplot_in = width_gap_in * (cols - 1) + width_ax_in * cols
        if right_in is not None and left_in is not None:
            width_fig_in = left_in + width_subplot_in + right_in
            fig.subplots_adjust(
                right=(1 - (right_in / width_fig_in)),
                left=(left_in / width_fig_in))
        elif right_in is None and left_in is None:
            right_rel = fig.subplotpars.right
            left_rel = fig.subplotpars.left
            width_fig_in = width_subplot_in / (right_rel - left_rel)
        else:
            raise ValueError(
                "Must provide both right and left margins or neither")

        # repeat the process for figure height
        if height_ax_in is None:
            height_ax_in = (top_ax - bottom_ax) * height_ax_rel
        if height_gap_in is None:
            height_gap_in = fig.subplotpars.hspace * height_ax_in
        else:
            fig.subplots_adjust(hspace=height_gap_in / height_ax_in)
        height_subplot_in = height_gap_in * (rows - 1) + height_ax_in * rows
        if top_in is not None and bottom_in is not None:
            height_fig_in = bottom_in + height_subplot_in + top_in
            fig.subplots_adjust(
                top=(1 - (top_in / height_fig_in)),
                bottom=(bottom_in / height_fig_in))
        elif top_in is None and bottom_in is None:
            top_rel = fig.subplotpars.top
            bottom_rel = fig.subplotpars.bottom
            height_fig_in = height_subplot_in / (top_rel - bottom_rel)
        else:
            raise ValueError(
                "Must provide both top and bottom margins or neither")

        fig.set_size_inches(width_fig_in, height_fig_in)


class ColorBar(Plot):
    def plot_data(self, colorbar):
        ax = self.get_ax(self.i)
        cax = plt.colorbar(
            colorbar, cax=ax, orientation="horizontal", aspect=40,
            spacing='proportional', **colorbar.cbar_args
            )
        if colorbar.tick_labels is not None:
            ax.set_xticklabels(colorbar.tick_labels)
        ax.set_title(colorbar.title)
        cax.outline.set_visible(False)
        cax.set_alpha(0.7)
        self.i += 1
        return (2, self.rows/2)

    def set_figure_size(
            self, fig=None, ax=None, rows=None, cols=None,
            height_ax_rel=None, width_ax_rel=None,
            width_ax_in=3, height_ax_in=0.1,
            height_gap_in=0.75, width_gap_in=0.5,
            top_in=None, bottom_in=None, left_in=None, right_in=None):
        return super().set_figure_size(
            fig, ax, rows, cols, height_ax_rel, width_ax_rel, width_ax_in,
            height_ax_in, height_gap_in, width_gap_in, top_in, bottom_in,
            left_in, right_in)
