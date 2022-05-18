from .plots import Plot


class Skyline(Plot):
    def __init__(self, num_samples, nt_length, region="all", **kwargs):
        if region == "all":
            self.nt_length = nt_length
            self.region = (1, nt_length)
        else:
            self.nt_length = region[1] - region[0] + 1
            self.region = region
        super().__init__(num_samples, **kwargs)
        self.ax = self.axes[0, 0]
        self.set_axis(self.ax)
        self.pass_through = ["column", "seqbar"]

    def get_rows_columns(self, number_of_samples=None, rows=None, cols=None):
        return (1, 1)

    def plot_data(self, profile, label, column="Reactivity_profile",
                  seqbar=True):
        self.plot_profile(profile, label, column)
        self.i += 1
        if self.i == self.length:
            if seqbar:
                self.add_sequence(self.ax, profile.sequence)
            self.set_labels(self.ax)

    def get_figsize(self):
        left_inches = 0.9
        right_inches = 0.4
        ax_width = self.nt_length * 0.1
        fig_height = 6
        fig_width = max(7, ax_width + left_inches + right_inches)
        return (fig_width, fig_height)

    def set_axis(self, ax, xticks=20, xticks_minor=5):
        xlim = self.region
        ax.set_xlim([xlim[0] - 0.5, xlim[1] + 0.5])
        xrange = range(xlim[0], xlim[1]+1)
        ax.set_xticks([x for x in xrange if (x % xticks) == 0])
        ax.set_xticks([x for x in xrange if (x % xticks_minor) == 0],
                      minor=True)

    def set_labels(self, ax, axis_title="Raw Reactivity Profile",
                   legend_title="Samples", xlabel="Nucleotide",
                   ylabel="Profile"):
        ax.set_title(axis_title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.legend(title=legend_title)

    def plot_profile(self, profile, label, column):
        x = [0.5]
        y = [0]
        # converts standard plot to skyline plot.
        for n, r in zip(profile.data['Nucleotide'], profile.data[column]):
            x.extend([n - 0.5, n + 0.5])
            y.extend([r, r])
        x.append(x[-1])
        y.append(0)
        self.ax.plot(x, y, label=label)
