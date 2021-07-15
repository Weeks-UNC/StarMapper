import matplotlib as mp
import matplotlib.pyplot as plt
import math
import numpy as np


class Plot():  # Children of Plot must have get_figsize and plot_data methods.
    def __init__(self, num_samples):
        self.length = num_samples
        self.rows, self.columns = self.get_rows_columns(num_samples)
        figsize = self.get_figsize()
        self.fig, self.axes = plt.subplots(
            self.rows, self.columns, figsize=figsize)
        self.i = 0

    def get_ax(self, i=None):
        if i is None:
            i = self.i
        row = i // self.columns
        col = i % self.columns
        return self.axes[row, col]

    def add_sample(self, sample, **kwargs):
        if isinstance(sample, list):
            for s in sample:
                self.add_sample(s, **kwargs)
            return
        for key in kwargs.keys():
            if kwargs[key] in sample.data.keys():
                kwargs[key] = sample.data[kwargs[key]]
            elif key == "label":
                if kwargs[key] == None:
                    kwargs[key] = sample.sample
                continue
            else:
                kwargs[key] = None
        self.plot_data(**kwargs)

    def view_colormap(self, ax=None, ij=None, metric=None, ticks=None, values=None,
                      title=None, cmap=None):
        if ij == "ct_compare":
            metric = "Pairing"
            ticks = [10/6, 30/6, 50/6]
            values = ["Reference\nonly", "Shared\npairs", "Comparison\nonly"]
            title = "Base-pairing comparison"
            cmap = mp.colors.ListedColormap([(0.6, 0.6, 0.6, 0.7),
                                             (0.15, 0.8, 0.6, 0.7),
                                             (0.6, 0.0, 1.0, 0.7)])
        elif ij is None:
            return
        else:
            metric = ij.metric
        if ticks is None:
            if metric == "Class":
                ticks = [10/6, 30/6, 50/6]
            else:
                ticks = [0, 2, 4, 6, 8, 10]
        if values is None:
            if metric == "Class":
                values = ['Complementary', 'Primary', 'Secondary']
            else:
                mn, mx = ij.min_max
                values = [f"{mn + ((mx-mn)/5)*i:.1f}" for i in range(6)]
        if title is None:
            title = f"{ij.datatype.capitalize()}: {metric.lower()}"
        if cmap is None:
            cmap = ij.cmap
        else:
            cmap = plt.get_cmap(cmap)
        colors = cmap(np.arange(cmap.N))

        if ax is None:
            _, ax = plt.subplots(1, figsize=(6, 2))
        ax.imshow([colors], extent=[0, 10, 0, 1])
        ax.set_title(title)
        ax.set_xticks(ticks)
        ax.set_xticklabels(values)
        ax.set_yticks([])

    def get_rows_columns(self, number_of_samples, rows=None, cols=None):
        if isinstance(rows, int) and cols is None:
            cols = math.ceil(number_of_samples / rows)
        elif isinstance(cols, int) and rows is None:
            rows = math.ceil(number_of_samples / cols)
        elif number_of_samples < 10:
            rows, cols = [(0, 0), (1, 1), (1, 2), (1, 3), (2, 2),
                          (2, 3), (2, 3), (3, 3), (3, 3), (3, 3)
                          ][number_of_samples]
        else:
            cols = 4
            rows = math.ceil(number_of_samples / cols)
        return rows, cols

    def add_sequence(self, sequence, yvalue=0.005):
        # set font style and colors for each nucleotide
        font_prop = mp.font_manager.FontProperties(
            family="monospace", style="normal", weight="bold", size="12")
        color_dict = {"A": "#f20000", "U": "#f28f00",
                      "G": "#00509d", "C": "#00c200"}
        # transform yvalue to a y-axis data value
        ax = self.get_ax()
        ymin, ymax = ax.get_ylim()
        yvalue = (ymax-ymin)*yvalue + ymin
        for i, seq in enumerate(sequence):
            col = color_dict[seq.upper()]
            ax.annotate(seq, xy=(i + 1, yvalue), xycoords='data',
                        fontproperties=font_prop,
                        color=col, horizontalalignment="center")
