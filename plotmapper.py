#!/usr/bin/env python

# general python packages
import matplotlib as mp
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os.path


# scripts in JNBTools
from data import *
from plots import *


def create_code_button():
    from IPython.display import display, HTML
    display(HTML('''<script>
                 code_show=true;
                 function code_toggle() {
                 if (code_show) {$('div.input').hide();}
                 else {$('div.input').show();}
                 code_show = !code_show
                 }
                 $( document ).ready(code_toggle);
                 </script>
                 <form action="javascript:code_toggle()">
                 <input type="submit" value="Hide/show raw code.">
                 </form>'''))


# STYLE SHEET
###############################################################################
sns.set_context("talk")
sns.set_style("ticks")
colors = [
    '#0092edff',  # Blue
    '#ff8300ff',  # Orange
    '#a100ffff',  # Purple
    '#edc600ff',  # Yellow
    '#ff48e9ff',  # Pink
    '#3fd125ff'  # Green
]
sns.set_palette(colors)

# Hard coded defaults
###############################################################################


def get_nt_color(nt, colors="new"):
    nt_color = {"old": {"A": "#f20000",  # red
                        "U": "#f28f00",  # yellow
                        "G": "#00509d",  # blue
                        "C": "#00c200"},  # green
                "new": {"A": "#366ef0",  # blue
                        "U": "#9bb9ff",  # light blue
                        "G": "#f04c4c",  # red
                        "C": "#ffa77c"}  # light red
                }[colors][nt]
    return nt_color


def view_colormap(ij_data=None, metric=None, ticks=None, values=None,
                  title=None, cmap=None):
    """Given an ij_data (ij data) will display a colorbar for the default
    values (metric, cmap, min_max).

    Args:
        ij_data (str, optional): string matching an ij data type.
            Options are "rings", "pairs" or "deletions".
            Defaults to None.
        metric (str, optional): string matching column name of ij data.
            Default determined by get_default_metric.
        ticks (list, optional): locations to add ticks. scale is 0-10.
            Defaults to [0.5, 0.95], or [10/6, 30/6/, 50/6] for "Class" metric.
        title (str, optional): string for title of colorbar.
            Defaults to "{ij_data}: {metric}"
        cmap (str, optional): string matching a valid matplotlib colormap.
            Default determined by get_default_cmap.
    """
    if metric is None:
        metric = get_default_metric(ij_data)
    if ticks is None:
        if metric == "Class":
            ticks = [10/6, 30/6, 50/6]
        else:
            ticks = [0, 2, 4, 6, 8, 10]
    if values is None:
        if metric == "Class":
            values = ['Complementary', 'Primary', 'Secondary']
        else:
            mn, mx = get_default_min_max(metric)
            values = [f"{mn + ((mx-mn)/5)*i:.2}" for i in range(6)]
    if title is None:
        title = f"{ij_data.capitalize()}: {metric.lower()}"
    if cmap is None:
        cmap = get_default_cmap(metric)
    else:
        cmap = plt.get_cmap(cmap)
    colors = cmap(np.arange(cmap.N))

    _, ax = plt.subplots(1, figsize=(6, 2))
    ax.imshow([colors], extent=[0, 10, 0, 1])
    ax.set_title(title)
    ax.set_xticks(ticks)
    ax.set_xticklabels(values)
    ax.set_yticks([])


# COPIED FROM SHAPEMAPPER2
# some of this might be inappropriately applied to all plots
# TODO: look into passing dict to mp.rc()
###############################################################################
mp.rcParams["font.sans-serif"].insert(0, "Arial")
shapemapper_style = {"font.family": "sans-serif",
                     "pdf.fonttype": 42,
                     # use TrueType fonts when exporting PDFs
                     # (embeds most fonts - this is especially
                     #  useful when opening in Adobe Illustrator)
                     'xtick.direction': 'out',
                     'ytick.direction': 'out',
                     'legend.fontsize': 14,
                     'grid.color': ".8",
                     'grid.linestyle': '-',
                     'grid.linewidth': 1}

rx_color = "red"
bg_color = "blue"
dc_color = "darkgoldenrod"
###############################################################################


class Sample():

    def __init__(self,
                 sample=None,
                 fasta=None,
                 profile=None,
                 ct=None,
                 compct=None,
                 ss=None,
                 log=None,
                 rings=None,
                 deletions=None,
                 pairs=None,
                 pdb=None,
                 probs=None,
                 dance_prefix=None):
        self.paths = {"fasta": fasta,
                      "profile": profile,
                      "ct": ct,
                      "comptct": compct,
                      "ss": ss,
                      "log": log,
                      "rings": rings,
                      "deletions": deletions,
                      "pairs": pairs,
                      "pdb": pdb,
                      "probs": probs}
        self.sample = sample

        self.data = {}  # stores profile, ij, and structure objects
        if ct is not None:
            self.data["ct"] = CT("ct", ct)
        if compct is not None:
            self.data["compct"] = CT("ct", compct)
        if ss is not None:
            self.data["ss"] = CT("ss", ss)
        if pdb is not None:
            self.data["pdb"] = PDB(pdb)

        # ShapeMapper downstream analysis requires sequence given from profile
        if profile is not None:
            self.data["profile"] = Profile(profile)
            prof_seq = self.data["profile"].sequence
            self.has_profile = True
        else:
            self.has_profile = False
        no_profile_message = "{} requires a sequence from ShapeMapper profile."
        if log is not None:
            self.data["log"] = Log(log)
        if rings is not None:
            assert self.has_profile, no_profile_message.format("Rings")
            self.data["rings"] = IJ("rings", rings, prof_seq)
        if pairs is not None:
            assert self.has_profile, no_profile_message.format("Pairs")
            self.data["pairs"] = IJ("pairs", pairs, prof_seq)
        if probs is not None:
            assert self.has_profile, no_profile_message.format("Probabilities")
            self.data["probs"] = IJ("probs", probs, prof_seq)

        # Deletions requires a reference sequence in fasta format.
        if deletions is not None:
            assert fasta is not None, "Deletions plotting requires fasta"
            self.data["deletions"] = IJ("deletions", deletions, fasta=fasta)
        if dance_prefix is not None:
            self.init_dance(dance_prefix)

    def init_dance(self, prefix):
        reactivityfile = f"{prefix}-reactivities.txt"
        # read in 2 line header
        with open(reactivityfile) as inf:
            header1 = inf.readline().strip().split()
            header2 = inf.readline().strip().split()
        # number of components
        self.dance_components = int(header1[0])
        # population percentage of each component
        self.dance_percents = header2[1:]
        # dance is a list containing one sample for each component
        self.dance = [Sample() for _ in range(self.dance_components)]
        # build column names for reading in BM file
        for i, sample in enumerate(self.dance):
            sample.sample = f"{i} - {self.dance_percents[i]}"
            sample.paths = {"profile": reactivityfile,
                            "rings": f"{prefix}-{i}-rings.txt",
                            "pairs": f"{prefix}-{i}-pairmap.txt",
                            "ct": [f"{prefix}-{i}.f.ct",  # if using --pk
                                   f"{prefix}-{i}.ct"]}  # if regular fold used
            # read in "profile" from reactivities
            sample.data["profile"] = Profile(reactivityfile, "dance", i)
            # read in other attributes
            if os.path.isfile(sample.paths["rings"]):
                sample.data["rings"] = IJ(sample.paths["rings"], "rings",
                                          sample.data["profile"].sequence)
            if os.path.isfile(sample.paths["pairs"]):
                sample.data["pairs"] = IJ(sample.paths["pairs"], "pairs",
                                          sample.data["profile"].sequence)
            # ! possible that these both exist
            for ct_file in sample.paths["ct"]:
                if os.path.isfile(ct_file):
                    sample.data["ct"] = CT("ct", ct_file)
                    sample.paths["ct"] = ct_file

###############################################################################
# Plotting functions
#     make_skyline
#     make_qc
#
###############################################################################

    def make_skyline(self, dance=False, **kwargs):
        profiles, labels = [], []
        if dance:
            for dance in self.dance:
                profiles.append(dance.data["profile"])
                labels.append(dance.sample)
            kwargs["legend_title"] = "Comp: Percent"
            kwargs["axis_title"] = f"{self.sample}: DANCE Reactivities"
        else:
            profiles.append(self.data["profile"])
            labels.append(self.sample)
        Skyline(profiles, labels).make_plot(**kwargs)

    def make_qc(self, **kwargs):
        profiles = [self.data["profile"]]
        logs = [self.data["log"]]
        labels = [self.sample]
        QC(logs, profiles, labels).make_plot(**kwargs)

    def get_data(self, key):
        if key == "ctcompare":
            return [self.data["ct"], self.data["compct"]]
        elif key in self.data.keys():
            return self.data[key]
        elif isinstance(key, list):
            return [self.data[k] for k in key]
        else:
            print(f"Key must be one of:\n{self.data.keys()}")

    def make_ap(self, top, bottom, dance=False, **filter_kwargs):
        def add_sample(sample):
            ap_kwargs["top"].append(sample.get_data(top))
            ap_kwargs["bottom"].append(sample.get_data(bottom))
            ap_kwargs["profiles"].append(sample.get_data("profile"))
            ap_kwargs["labels"].append(self.sample)

        self.filter_ij(self.get_data(bottom), self.get_data(top), **filter_kwargs)
        ap_kwargs = {"top": [], "bottom": [], "profiles": [], "labels": []}
        if dance:
            for sample in self.dance:
                add_sample(sample)
        else:
            add_sample(self)
        AP(**ap_kwargs).make_plot()

    def filter_ij(self, data, fit_to, **kwargs):
        data.filter(fit_to, profile=self.data["profile"],
                    ct=self.data["ct"], **kwargs)

    def filter_dance_rings(self, filterneg=True, cdfilter=15, sigfilter=20,
                           ssfilter=True):
        ctlist = [dance.ct for dance in self.dance]
        ringlist = [dance.ij_data["rings"].copy() for dance in self.dance]
        for index, rings in enumerate(ringlist):
            rings[['i_offset', 'j_offset']] = rings[['i', 'j']]
            mask = []
            for _, row in rings.iterrows():
                i, j, G, sign = row[['i', 'j', 'Statistic', '+/-']]
                true_so_far = True
                if ssfilter and true_so_far:
                    true_so_far = (ctlist[index].ct[i-1]
                                   == 0 and ctlist[index].ct[j-1] == 0)
                if filterneg and true_so_far:
                    true_so_far = sign == 1
                if sigfilter is not None and true_so_far:
                    true_so_far = G > sigfilter
                if cdfilter is not None and true_so_far:
                    for ct in ctlist:
                        if not true_so_far:
                            break
                        true_so_far = ct.contactDistance(i, j) >= cdfilter
                mask.append(true_so_far)
            rings['mask'] = mask
            self.dance[index].ij_data["rings"] = rings

    def make_shapemapper(self, **kwargs):
        SM(self.data["profile"]).make_shapemapper(**kwargs)

###############################################################################
# Plotting functions that accept a list of samples
#   array_qc
#   array_skyline
#   array_ap
#   array_ss
#   array_3d
###############################################################################


def array_ap(samples=[], rows=None, cols=None, **kwargs):
    rows, cols = get_rows_columns(len(samples), rows, cols)
    figsize = samples[0].get_ap_figsize(rows, cols)
    gs_kw = {'rows': rows, 'cols': cols, 'hspace': 0.01, 'wspace': 0.1}
    _, axes = plt.subplots(rows, cols, figsize=figsize, gridspec_kw=gs_kw)
    for i, sample in enumerate(samples):
        row = i // cols
        col = i % rows
        ax = axes[row, col]
        sample.make_ap(ax=ax, **kwargs)


def array_qc(samples=[]):
    logs, profiles, labels = []
    for sample in samples:
        logs.append(sample.data["logs"])
        profiles.append(sample.data["profile"])
        labels.append(sample.sample)
    QC(logs, profiles, labels).make_plot()


def array_skyline(samples, **kwargs):
    fig, ax = plt.subplots(1, figsize=samples[0].get_skyline_figsize(1, 1))
    for sample in samples[:-1]:
        sample.plot_skyline(ax)
    samples[-1].make_skyline(ax, **kwargs)


def array_ss(samples, **kwargs):
    fig, ax = plt.subplots(1, 4, figsize=samples[0].get_ss_figsize(1, 4))
    for i, sample in enumerate(samples):
        sample.make_ss(ax[i], **kwargs)


def array_3d(samples, rows=None, cols=None, **kwargs):
    """Given a list of samples, creates a grid of py3Dmol views. Kwargs passed
    to samples[0].make_3d(). Samples must all use the same structure.

    Args:
        samples (List of Sample objects): Sample objects from which to display.
        rows (int, optional): number of rows for figure.
            Default determined by get_rows_columns.
        cols (int, optional): number of columns for figure.
            Default determined by get_rows_columns.

    Returns:
        [type]: [description]
    """
    rows, cols = get_rows_columns(len(samples), rows, cols)
    view = py3Dmol.view(viewergrid=(rows, cols),
                        width=400*rows,
                        height=400*cols)
    view = samples[0].set_3d_view(view)
    for i, sample in enumerate(samples):
        row = i // cols
        col = i % rows
        view = sample.make_3d(view, (row, col), **kwargs)
    return view
