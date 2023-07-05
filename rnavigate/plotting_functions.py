"""Contains all rnavigate convenience plotting functions"""

import os.path
from rnavigate import plots
from rnavigate import data

_list = object()
_dict = object()

###############################################################################
# accessory functions
#   get_sequence
#   fit_data
###############################################################################


def replace_sentinels(*args):
    """takes arguments, replaces any _dict with {} and _list with []

    Returns:
        list: arguments with sentinels replaced
    """
    mutable = {_dict: {}, _list: []}
    return [mutable[arg] if arg in mutable else arg for arg in args]


def get_sequence(sequence, sample=None, default=None):
    """Flexible function that returns a Data object containing a sequence.

    Args:
        sequence (any): Can be a sequence string, a key in sample.data, or a
            Data object with a sequence
        sample (Sample, optional): sample to get retrieve data from.
            Defaults to None.
        default (any, optional): same format as sequence above. default to
            this if sequence is None.
            Defaults to None.

    Raises:
        ValueError: If sequence and default are both None
        ValueError: If Data object could not be retreived based on inputs

    Returns:
        Data object or subclass: contains a sequence and can be used in factory
            methods
    """
    if sequence is None and default is None:
        raise ValueError("A sequence must be provided.")
    elif sequence is None:
        sequence = default
    if isinstance(sequence, data.Sequence):
        pass
    elif isinstance(sequence, str) and os.path.isfile(sequence):
        sequence = data.Sequence(sequence)
    elif isinstance(sequence, str) and sequence in sample.data.keys():
        sequence = sample.data[sequence]
    elif isinstance(sequence, str) and all([nt.upper() in "AUCGT." for nt in sequence]):
        sequence = data.Sequence(sequence=sequence)
    else:
        raise ValueError(f"Cannot find sequence from {sequence}")
    return sequence


def fit_data(data_list, fit_to, second_alignment=None):
    """Given a sample and list of sample.data keys, Data objects are mapped to
    fit_to

    Args:
        sample (rnavigate.Sample): sample to retrieve data from
        data_list (list): list of sample.data keys or None
        fit_to (rnavigate.Data): Data object with a sequence to fit to
    """
    if isinstance(data_list, dict):
        return {k: fit_data(v, fit_to) for k, v in data_list.items()}
    elif isinstance(data_list, list):
        return [fit_data(v, fit_to) for v in data_list]
    elif data_list is None:
        return None
    elif isinstance(data_list, data.Sequence):
        if isinstance(data_list, data.PDB):
            return data_list
        alignment = data.SequenceAlignment(data_list, fit_to)
        if second_alignment is not None:
            alignment = data.AlignmentChain(alignment, second_alignment)
        return data_list.get_aligned_data(alignment)

###############################################################################
# Plotting functions that accept a list of samples
#   plot_qc
#   plot_skyline
#   plot_arcs
#   plot_ss
#   plot_mol
#   plot_heatmap
#   plot_circle
#   plot_linreg
#   plot_roc
#   plot_disthist
###############################################################################


def plot_qc(samples, labels=None, plot_kwargs=_dict, **kwargs):
    """Makes a multipanel quality control plot displaying mutations per
    molecule, read length distribution, and mutation rate distributions for
    modified and unmodified samples.

    Args:
        samples (list of rnavigate.Sample): samples to plot.
        labels (list of str, optional): same length as samples list. labels to
            to be used on plot legends.
            Defaults to sample attribute of each sample.
        plot_kwargs (dict, optional): kwargs dictionary passed to QC().
            Defaults to {}.
        **kwargs: passed to QC.plot_data

    Returns:
        rnavigate.plots.QC plot: object containing matplotlib figure and axes
            with additional plotting and file saving methods
    """
    if labels is None:
        labels = [sample.sample for sample in samples]
    plot_kwargs = replace_sentinels(plot_kwargs)
    plot = plots.QC(num_samples=len(samples), **plot_kwargs)
    for sample, label in zip(samples, labels):
        plot.add_sample(sample=sample, log="log", profile="profile",
                        label=label, **kwargs)
    plot.set_figure_size()
    return plot

def plot_skyline(samples, sequence=None, profile="profile", labels=None,
                 annotations=_list, region="all", plot_kwargs=_dict, **kwargs):
    """Plots multiple per-nucleotide datasets on a single axis.

    Args:
        samples (list of rnavigate.Sample): samples to plot.
        sequence (str or data object, optional): a key from sample.data, a
            sequence string, or a Data object. All data will be mapped to this
            string using a user-defined or pairwise sequence alignment.
            Defaults to the value of the profile argument below.
        profile (str, optional): per-nucleotide data to retrieve from sample.
            Defaults to "profile".
        labels (list of str, optional): Same length as samples list. Labels to
            be used in plot legends. Defaults to default sample name.
        annotations (list of str, optional): annotations to retrive from
            sample. Defaults to [].
        region (list of int: length 2, optional): start and end positions to
            plot. 1-indexed, inclusive. Defaults to [1, sequence length].
        plot_kwargs (dict, optional): kwargs dictionary passed to Skyline().
            Defaults to {}.
        **kwargs: additional keyword arguments are passed to Skyline.plot_data.
            see rnavigate.plots.Skyline.plot_data for more detail.

    Returns:
        rnavigate.plots.Skyline plot: object containing matplotlib figure and
            axes with additional plotting and file saving methods
    """
    annotations, plot_kwargs = replace_sentinels(annotations, plot_kwargs)
    if labels is None:
        labels = [sample.sample for sample in samples]
    sequence = get_sequence(sequence, samples[0], profile)
    plot = plots.Skyline(num_samples=len(samples),
                         nt_length=sequence.length,
                         region=region,
                         **plot_kwargs)
    for sample, label in zip(samples, labels):
        data_dict = sample.get_data({
            'profile': profile,
            'annotations': annotations})
        data_dict = fit_data(data_dict, sequence)
        plot.plot_data(**data_dict, label=label, **kwargs)
    plot.set_figure_size()
    return plot


def plot_profile(samples, sequence=None, profile="profile", labels=None,
                 annotations=_list, region="all", plot_kwargs=_dict, **kwargs):
    """Aligns reactivity profiles by sequence and plots them on seperate axes.

    Args:
        samples (list of rnavigate.Sample): samples to plot.
        sequence (str or data object, optional): a key from sample.data, a
            sequence string, or a Data object. All data will be mapped to this
            string using a user-defined or pairwise sequence alignment.
            Defaults to the value of the profile argument below.
        profile (str, optional): per-nucleotide data to retrieve from sample.
            Defaults to "profile".
        labels (list of str, optional): Same length as samples list. Labels to
            be used in plot legends. Defaults to default sample name.
        annotations (list of str, optional): annotations to retrive from
            sample. Defaults to [].
        region (list of int: length 2, optional): start and end positions to
            plot. 1-indexed, inclusive. Defaults to [1, sequence length].
        plot_kwargs (dict, optional): kwargs dictionary passed to Profile().
            Defaults to {}.
        **kwargs: additional keyword arguments are passed to Profile.plot_data.
            see rnavigate.plots.skyline.Profile.plot_data for more detail.

    Returns:
        rnavigate.plots.Profile plot: object containing matplotlib figure and
            axes with additional plotting and file saving methods
    """
    annotations, plot_kwargs = replace_sentinels(annotations, plot_kwargs)
    if labels is None:
        labels = [sample.sample for sample in samples]
    sequence = get_sequence(sequence, samples[0], profile)
    plot = plots.skyline.Profile(num_samples=len(samples),
                                 nt_length=sequence.length,
                                 region=region,
                                 **plot_kwargs)
    for sample, label in zip(samples, labels):
        data_dict = sample.get_data({
            'annotations': annotations,
            'profile': profile,
            'seq': sequence
        })
        data_dict = fit_data(data_dict, sequence)
        plot.plot_data(**data_dict, label=label, **kwargs)
    plot.set_figure_size()
    return plot


def plot_alignment(data1, data2, labels=None, plot_kwargs=_dict):
    """Plots the sequence alignment used to compare two data objects.

    Args:
        data1 (tuple (rnavigate.Sample, str)): a sample and data class keyword
        data2 (tuple (rnavigate.Sample, str)): a sample and data class keyword
        labels (list of str, optional): length 2. Labels used in plots
            Defaults to default sample name + data class keyword
        plot_kwargs (dict, optional): kwargs dictionary passed to Alignment().
            Defaults to {}.
        **kwargs: additional keyword arguments are passed to
            Alignment.plot_data. see rnavigate.plots.Alignment.plot_data for
            more detail.

    Returns:
        rnavigate.plots.Alignment plot: object containing matplotlib figure and
            axes with additional plotting and file saving methods
    """
    plot_kwargs = replace_sentinels(plot_kwargs)
    if labels is None:
        labels = [f"{s.sample}: {seq}" for s, seq in [data1, data2]]
    plot = plots.Alignment(num_samples=1, **plot_kwargs)
    alignment = data.SequenceAlignment(
        data1[0].data[data1[1]], data1[0].data[data1[1]])
    plot.plot_data(alignment=alignment, label=labels)
    plot.set_figure_size()
    return plot


def plot_arcs(samples, sequence=None, structure=None, comp=None,
              interactions=None, interactions_filter=_dict, filters=None,
              interactions2=None, interactions2_filter=_dict,
              profile=None, annotations=_list, labels=None, region="all",
              plot_kwargs=_dict, colorbar=True, **kwargs):
    """Generates a multipanel arc plot displaying combinations of secondary
    structures, per-nucleotide data, inter-nucleotide data, and sequence
    annotations. Each plot may display a unique sample and/or filtering scheme.

    Args:
        samples (list of rnavigate.Sample): Samples to retreive data from.
            number of panels will equal the length of this list, unless filters
            argument below is also used.
        sequence (str or data object, optional): a key from sample.data, a
            sequence string, or a Data object. All data will be mapped to this
            string using a user-defined or pairwise sequence alignment.
            Defaults to the value of the ct argument below.
        structure (str, optional): a key from sample.data to retreive a secondary
            structure. This will be plotted on the top half of each panel.
            Defaults to "ss".
        comp (str, optional): same as ct. basepairs from ct and comp will be
            plotted on the top half of each panel. Basepairs are colored by
            which structure contains them (shared, ct only, comp only).
            Defaults to None.
        interactions (str, optional): a key from sample.data to retrieve inter-
            nucleotide data. These data are mapped to sequence coordinates,
            filtered using interactions_filter arguments, and displayed on the
            bottom half of each panel.
            Defaults to None.
        interactions_filter (dict, optional): These key-value pairs are passed
            as keyword arguments to sample.filter_interactions along with
            interactions=interactions and fit_to=sequence. See
            rnavigate.Sample.filter_interactions for more detail.
            Defaults to {}.
        filters (list of dict, optional): For plotting multiple filtering
            schemes applied to each sample, each in a new panel. Each
            dictionary in this list follows a similar structure as
            interactions_filter, but also requires the key-value pair:
            {"interactions": interactions} where interactions is as described
            above. interactions and interactions_filter arguments above will be
            ignored. interactions2 and interactions2_filter will be displayed
            in every panel.
            Defaults to [].
        interactions2 (str, optional): same as interactions above.
            Defaults to None.
        interactions2_filter (dict, optional): same as interactions_filter
            above but applied to interactions2.
            Defaults to {}.
        profile (str, optional): a key from sample.data used to retrieve per-
            nucleotide data. These data are displayed in center of each panel.
            Defaults to "profile".
        annotations (list, optional): a list of keys from sample.data used to
            retrieve sequence annotations. These annotations are displayed in
            the center of each panel.
            Defaults to [].
        labels (str, optional): Same length as samples list. Labels to
            be used in plot legends. Defaults to default sample name.
        region (list of int: length 2, optional): start and end position of
            sequence to be plotted. 1-indexed, inclusive.
            Defaults to [0, sequence length].
        plot_kwargs (dict, optional): kwargs passed to AP(). See
            rnavigate.plots.AP for more detail.
            Defaults to {}.
        **kwargs: additional keyword arguments are passed to AP.plot_data.
            see rnavigate.plots.AP.plot_data for more detail.

    Returns:
        rnavigate.plots.AP plot: object containing matplotlib figure and axes
            with additional plotting and file saving methods
    """
    # use mutable defaults
    annotations, plot_kwargs = replace_sentinels(annotations, plot_kwargs)
    interactions_filter = replace_sentinels(interactions_filter)
    interactions2_filter = replace_sentinels(interactions2_filter)
    if labels is None:
        labels = [sample.sample for sample in samples]
    # coerce interactions and interactions_filter into filters format
    if filters is None:
        filters = [{"interactions": interactions} | interactions_filter]
    # if filters and samples > 1, rows = # samples, columns = # filters
    if (len(filters) > 1) and (len(samples) > 1):
        plot_kwargs |= {'rows': len(filters), 'cols': len(samples)}
    # initialize plot
    num_samples = len(samples) * len(filters)
    sequence = get_sequence(sequence, samples[0], structure)
    plot = plots.AP(
        num_samples=num_samples,
        nt_length=sequence.length,
        region=region, **plot_kwargs)
    # loop through samples and filters, adding each as a new axis
    for sample, label in zip(samples, labels):
        sample.filter_interactions(interactions2, **interactions2_filter)
        data_dict = sample.get_data({
            'annotations': annotations,
            'ct': structure,
            'comp': comp,
            'profile': profile,
            'interactions2': interactions2})
        data_dict = fit_data(data_dict, sequence)
        data_dict['label'] = sample.get_data(label)
        data_dict['seq'] = sequence
        for filt in filters:
            sample.filter_interactions(**filt)
            interactions = sample.get_data(filt['interactions'])
            data_dict['interactions'] = fit_data(interactions, sequence)
            plot.plot_data(**data_dict, **kwargs)
    plot.set_figure_size()
    if colorbar:
        plot.plot_colorbars()
    return plot


def plot_arcs_compare(samples, sequence=None, structure="ss", structure2=None,
                      interactions=None, interactions_filter=_dict,
                      interactions2=None, interactions2_filter=_dict,
                      profile="profile", labels=None, region="all",
                      plot_kwargs=_dict, colorbar=True, **kwargs):
    """Generates a single arc plot displaying combinations of secondary
    structures, per-nucleotide data, inter-nucleotide data, and sequence
    annotations. The first sample will be on top, the second on the bottom.
    Center shows how these sequences are being aligned.

    Args:
        samples (list of rnavigate.Sample): Samples to retreive data from.
            number of panels will equal the length of this list, unless filters
            argument below is also used.
        sequence (str or data object, optional): a key from sample.data, a
            sequence string, or a Data object. All data will be mapped to this
            string using a user-defined or pairwise sequence alignment.
            Defaults to the value of the ct argument below.
        ct (str, optional): a key from sample.data to retreive a secondary
            structure. This will be plotted on the top half of each panel.
            Defaults to "ct".
        comp (str, optional): same as ct. basepairs from ct and comp will be
            plotted on the top half of each panel. Basepairs are colored by
            which structure contains them (shared, ct only, comp only).
            Defaults to None.
        interactions (str, optional): a key from sample.data to retrieve inter-
            nucleotide data. These data are mapped to sequence coordinates,
            filtered using interactions_filter arguments, and displayed on the
            bottom half of each panel.
            Defaults to None.
        interactions_filter (dict, optional): These key-value pairs are passed
            as keyword arguments to sample.filter_interactions along with
            interactions=interactions and fit_to=sequence. See
            rnavigate.Sample.filter_interactions for more detail.
            Defaults to {}.
        interactions2 (str, optional): same as interactions above.
            Defaults to None.
        interactions2_filter (dict, optional): same as interactions_filter
            above but applied to interactions2.
            Defaults to {}.
        profile (str, optional): a key from sample.data used to retrieve per-
            nucleotide data. These data are displayed in center of each panel.
            Defaults to "profile".
        labels (str, optional): Same length as samples list. Labels to
            be used in plot legends. Defaults to default sample name.
        region (list of int: length 2, optional): start and end position of
            sequence to be plotted. 1-indexed, inclusive.
            Defaults to [0, sequence length].
        plot_kwargs (dict, optional): kwargs passed to AP(). See
            rnavigate.plots.AP for more detail.
            Defaults to {}.
        **kwargs: additional keyword arguments are passed to AP.plot_data.
            see rnavigate.plots.AP.plot_data for more detail.

    Returns:
        rnavigate.plots.AP plot: object containing matplotlib figure and axes
            with additional plotting and file saving methods
    """
    seq1 = get_sequence(sequence, samples[0], structure)
    seq2 = get_sequence(sequence, samples[1], structure)
    alignment = data.SequenceAlignment(seq1, seq2)
    # use mutable defaults
    interactions_filter = replace_sentinels(interactions_filter)
    interactions2_filter = replace_sentinels(interactions2_filter)
    plot_kwargs = replace_sentinels(plot_kwargs)
    if labels is None:
        labels = [sample.sample for sample in samples]
    # coerce interactions and interactions_filter into filters format
    filters = [{"interactions": interactions} | interactions_filter]
    # initialize plot using all structure drawings
    plot = plots.AP(num_samples=1, nt_length=len(alignment.target),
                    region=region, **plot_kwargs)
    # loop through samples and filters, adding each as a new axis
    for sample, seq, panel in zip(samples, [1, 2], ["top", "bottom"]):
        if seq == 1:
            seq, other_seq = seq1, seq2
        else:
            seq, other_seq = seq2, seq1
        alignment = data.SequenceAlignment(seq, other_seq)
        sample.filter_interactions(interactions2, **interactions2_filter)
        data_dict = sample.get_data({
            'ct': structure,
            'comp': structure2,
            'profile': profile,
            'interactions2': interactions2,
        })
        panels = {
            'ct_panel': panel, 
            'interactions_panel': panel,
            'interactions2_panel': panel,
            'profile_panel': panel}
        data_dict = fit_data(data_dict, seq, alignment)
        for filt in filters:
            sample.filter_interactions(**filt)
            interactions = sample.get_data(filt['interactions'])
            data_dict['interactions'] = fit_data(interactions, seq, alignment)
            plot.plot_data(
                ax=0, seq=None, annotation_gap=10, label='', seqbar=False,
                **panels, **data_dict, **kwargs)
    plots.alignment.plot_alignment(
        plot=plot, ax=plot.axes[0, 0], alignment=alignment, label=labels,
        center=-5, offset=4, spines_positions={"top": 0, "bottom": -10})
    plot.set_figure_size()
    if colorbar:
        plot.plot_colorbars()
    return plot

def plot_ss(samples, structure="ss", profile="profile", annotations=_list,
            interactions=None, interactions_filter=_dict, interactions2=None,
            interactions2_filter=_dict, filters=None, labels=None,
            plot_kwargs=_dict, colorbar=True, **kwargs):
    """Generates a multipanel secondary structure drawing with optional
    coloring by per-nucleotide data and display of inter-nucleotide data and/or
    sequence annotations. Each plot may display a unique sample and/or
    inter-nucleotide data filtering scheme.

    Args:
        samples (list of rnavigate.Sample): Samples to retreive data from.
            number of panels will equal the length of this list, unless filters
            argument below is also used.
        ss (str, optional): a key from sample.data used to retrieve a secondary
            structure containing drawing coordinates.
            Defaults to "ss"
        profile (str, optional): a key from sample.data used to retrieve per-
            nucleotide data. These data may be used to color nucleotides in the
            structure drawing.
            Defaults to "profile".
        annotations (list, optional): a list of keys from sample.data used to
            retrieve sequence annotations. These annotations are highlighted on
            the structure drawing.
            Defaults to [].
        interactions (str, optional): a key from sample.data to retrieve inter-
            nucleotide data. These data are mapped to ss sequence coordinates,
            filtered using interactions_filter arguments, and displayed as
            lines connecting nucleotides in the structure drawing.
            Defaults to None.
        interactions_filter (dict, optional): These key-value pairs are passed
            as keyword arguments to sample.filter_interactions along with
            interactions=interactions and fit_to=ss. See
            rnavigate.Sample.filter_interactions for more detail.
            Defaults to {}.
        interactions2 (str, optional): same as interactions above.
            Defaults to None.
        interactions2_filter (dict, optional): same as interactions_filter
            above but applied to interactions2.
            Defaults to {}.
        filters (list of dict, optional): For plotting multiple filtering
            schemes applied to each sample, each in a new panel. Each
            dictionary in this list follows a similar structure as
            interactions_filter, but also requires the key-value pair:
            {"interactions": interactions} where interactions is as described
            above. interactions and interactions_filter arguments above will be
            ignored. interactions2 and interactions2_filter will be displayed
            in every panel.
            Defaults to [].
        labels (str, optional): Same length as samples list. Labels to
            be used in plot legends. Defaults to default sample name.
        plot_kwargs (dict, optional): kwargs passed to SS(). See
            rnavigate.plots.SS for more detail.
            Defaults to {}.
        **kwargs: additional keyword arguments are passed to SS.plot_data.
            see rnavigate.plots.SS.plot_data for more detail.

    Returns:
        rnavigate.plots.SS plot: object containing matplotlib figure and axes
            with additional plotting and file saving methods
    """
    # use mutable defaults
    interactions_filter = replace_sentinels(interactions_filter)
    interactions2_filter = replace_sentinels(interactions2_filter)
    annotations, plot_kwargs = replace_sentinels(annotations, plot_kwargs)
    if labels is None:
        labels = [sample.sample for sample in samples]
    # coerce interactions and interactions_filter into filters format
    if filters is None:
        filters = [{"interactions": interactions} | interactions_filter]
    # if filters and samples > 1, rows = # samples, columns = # filters
    if (len(filters) > 1) and (len(samples) > 1):
        plot_kwargs |= {'rows': len(filters), 'cols': len(samples)}
    # initialize plot using all structure drawings
    num_samples = len(samples) * len(filters)
    plot = plots.SS(num_samples=num_samples, **plot_kwargs)
    # loop through samples and filters, adding each as a new axis
    for sample, label in zip(samples, labels):
        sample.filter_interactions(interactions2, **interactions2_filter)
        data_dict = sample.get_data({
            'structure': structure,
            'annotations': annotations,
            'profile': profile,
            'interactions2': interactions2})
        data_dict = fit_data(data_dict, data_dict['structure'])
        for filt in filters:
            sample.filter_interactions(**filt)
            interactions = sample.get_data(filt['interactions'])
            data_dict['interactions'] = fit_data(interactions,
                                                 data_dict['structure'])
            plot.plot_data(**data_dict, label=label, **kwargs)
    plot.set_figure_size()
    if colorbar:
        plot.plot_colorbars()
    return plot


def plot_mol(samples, structure="pdb", interactions=None,
             interactions_filter=_dict, filters=None, profile="profile",
             labels=None, show=True, hide_cylinders=False, colorbar=True,
             custom_function=None, plot_kwargs=_dict, **kwargs):
    """Generates a multipanel interactive 3D molecular rendering of a PDB
    structure. Nucleotides may be colored by per-nucleotide data or custom
    color lists. Inter-nucleotide data may be displayed as cylinders connecting
    atoms or residues. Each plot may display a unique sample and/or filtering
    scheme.

    Args:
        samples (list of rnavigate.Sample): Samples to retreive data from.
            number of panels will equal the length of this list, unless filters
            argument below is also used.
        structure (str, optional): a key from sample.data to retrieve PDB data
            with atomic coordinates.
        interactions (str, optional): a key from sample.data to retrieve inter-
            nucleotide data. These data are mapped to structre sequence
            coordinates, filtered using interactions_filter arguments, and
            displayed as cylinders connecting nucleotides in the 3D structure.
            Defaults to None.
        interactions_filter (dict, optional): These key-value pairs are passed
            as keyword arguments to sample.filter_interactions along with
            interactions=interactions and fit_to=structure. See
            rnavigate.Sample.filter_interactions for more detail.
            Defaults to {}.
        filters (list of dict, optional): For plotting multiple filtering
            schemes applied to each sample, each in a new panel. Each
            dictionary in this list follows a similar structure as
            interactions_filter, but also requires the key-value pair:
            {"interactions": interactions} where interactions is as described
            above. interactions and interactions_filter arguments above will be
            ignored.
            Defaults to [].
        profile (str, optional): a key from sample.data used to retrieve per-
            nucleotide data. These data may be used to color nucleotides.
            Defaults to "profile".
        labels (str, optional): Same length as samples list. Labels to
            be used in plot legends.
            Defaults to default sample name.
        show (bool, optional): whether to display the interactive rendering.
            Defaults to True
        hide_cylinders (bool, optional): whether to display cylinders
            representing nucleoside orientation. Setting to false will display
            only the backbone as a ribbon.
            Defaults to False.
        plot_kwargs (dict, optional): kwargs passed to Mol(). See
            rnavigate.plots.Mol for more detail.
            Defaults to {}.
        **kwargs: additional keyword arguments are passed to Mol.plot_data.
            see rnavigate.plots.Mol.plot_data for more detail.

    Returns:
        rnavigate.plots.Mol plot: object containing py3dmol viewer with
            additional plotting and file saving methods
    """
    # use mutable defaults
    interactions_filter = replace_sentinels(interactions_filter)
    plot_kwargs = replace_sentinels(plot_kwargs)
    if labels is None:
        labels = [sample.sample for sample in samples]
    # coerce interactions and interactions_filter into filters format
    if filters is None:
        filters = [{"interactions": interactions} | interactions_filter]
    # if filters and samples > 1, rows = # samples, columns = # filters
    if (len(filters) > 1) and (len(samples) > 1):
        plot_kwargs |= {'rows': len(filters), 'cols': len(samples)}
    num_samples = len(samples) * len(filters)
    # initialize plot using 1st 3D structure (applies to all samples)
    structure = samples[0].get_data(structure)
    plot = plots.Mol(num_samples=num_samples, pdb=structure, **plot_kwargs)
    # loop through samples and filters, adding each as a new viewer
    for sample, label in zip(samples, labels):
        data_dict = sample.get_data({'profile': profile})
        data_dict = fit_data(data_dict, structure)
        for filt in filters:
            sample.filter_interactions(**filt)
            interactions = sample.get_data(filt['interactions'])
            data_dict['interactions'] = fit_data(interactions, structure)
            plot.plot_data(**data_dict, label=label, **kwargs)
    # apply custom function
    if custom_function is not None:
        custom_function(plot)
    # hide nucleotide cylinders in all viewers
    if hide_cylinders:
        plot.hide_cylinders()
    # show viewer grid
    if show:
        plot.view.show()
    if colorbar:
        plot.plot_colorbars()
    return plot


def plot_heatmap(samples, structure=None, interactions=None,
                 interactions_filter=_dict, filters=None, labels=None,
                 plot_kwargs=_dict, **kwargs):
    """Generates a multipanel plot displaying a heatmap of inter-nucleotide
    data (nucleotide resolution of 2D KDE) and/or contour map of structure
    distances. Each plot may display a unique sample and/or filtering scheme.

    Args:
        samples (list of rnavigate.Sample): Samples to retreive data from.
            number of panels will equal the length of this list, unless filters
            argument below is also used.
        structure (str, optional): a key from sample.data to retrieve either
            PDB data with atomic coordinates (contours outline 3D distance) or
            secondary structure data (contours outline contact distance).
        interactions (str, optional): a key from sample.data to retrieve inter-
            nucleotide data. These data are mapped to sequence coordinates,
            filtered using interactions_filter arguments, and displayed as
            either nucleotide-resolution heatmaps, or 2D kernel density
            estimate.
            Defaults to None.
        interactions_filter (dict, optional): These key-value pairs are passed
            as keyword arguments to sample.filter_interactions along with
            interactions=interactions and fit_to=sequence. See
            rnavigate.Sample.filter_interactions for more detail.
            Defaults to {}.
        filters (list of dict, optional): For plotting multiple filtering
            schemes applied to each sample, each in a new panel. Each
            dictionary in this list follows a similar structure as
            interactions_filter, but also requires the key-value pair:
            {"interactions": interactions} where interactions is as described
            above. interactions and interactions_filter arguments above will be
            ignored.
            Defaults to [].
        labels (str, optional): Same length as samples list. Labels to
            be used in plot legends. Defaults to default sample name.
        plot_kwargs (dict, optional): kwargs passed to Heatmap(). See
            rnavigate.plots.Heatmap for more detail.
            Defaults to {}.
        **kwargs: additional keyword arguments are passed to Heatmap.plot_data.
            see rnavigate.plots.Heatmap.plot_data for more detail.

    Returns:
        rnavigate.plots.Heatmap plot: object containing matplotlib figure and
            axes with additional plotting and file saving methods
    """
    # use mutable defaults
    interactions_filter = replace_sentinels(interactions_filter)
    plot_kwargs = replace_sentinels(plot_kwargs)
    if labels is None:
        labels = [sample.sample for sample in samples]
    # coerce interactions and interactions_filter into filters format
    if filters is None:
        filters = [{"interactions": interactions} | interactions_filter]
    # if filters and samples > 1, rows = # samples, columns = # filters
    if (len(filters) > 1) and (len(samples) > 1):
        plot_kwargs |= {'rows': len(filters), 'cols': len(samples)}
    # initialize plot using 1st 3D structure (applies to all samples)
    num_samples = len(samples) * len(filters)
    structure = samples[0].data[structure]
    plot = plots.Heatmap(num_samples, structure, **plot_kwargs)
    # loop through samples and filters, adding each as a new axis
    for sample, label in zip(samples, labels):
        for filt in filters:
            sample.filter_interactions(**filt)
            interactions = sample.get_data(filt['interactions'])
            interactions = fit_data(interactions, structure)
            plot.plot_data(interactions=interactions, label=label, **kwargs)
    plot.set_figure_size()
    return plot

def plot_circle(samples, sequence=None, structure=None, structure2=None,
                interactions=None, interactions_filter=_dict,
                interactions2=None, interactions2_filter=_dict, filters=None,
                annotations=_list, profile="profile", labels=None,
                colorbar=True, plot_kwargs=_dict, **kwargs):
    """Generates a multipanel circle plot displaying combinations of secondary
    structures, per-nucleotide data, inter-nucleotide data, and sequence
    annotations. Each plot may display a unique sample and/or filtering scheme.

    Args:
        samples (list of rnavigate.Sample): Samples to retreive data from.
            number of panels will equal the length of this list, unless filters
            argument below is also used.
        sequence (str or data object, optional): a key from sample.data, a
            sequence string, or a Data object. All data will be mapped to this
            sequence using a user-defined or pairwise sequence alignment.
            Defaults to the value of the ct argument below.
        ct (str, optional): a key from sample.data to retreive a secondary
            structure. Basepairs are plotted as grey arcs within the circle.
            Defaults to "ct".
        comp (str, optional): same as ct. basepairs from ct and comp will be
            plotted. Basepairs are colored by which structure contains them
            (shared, ct only, comp only).
            Defaults to None.
        interactions (str, optional): a key from sample.data to retrieve inter-
            nucleotide data. These data are mapped to sequence coordinates,
            filtered using interactions_filter arguments, and displayed as arcs
            within the circle.
            Defaults to None.
        interactions_filter (dict, optional): These key-value pairs are passed
            as keyword arguments to sample.filter_interactions along with
            interactions=interactions and fit_to=sequence. See
            rnavigate.Sample.filter_interactions for more detail.
            Defaults to {}.
        interactions2 (str, optional): same as interactions above.
            Defaults to None.
        interactions2_filter (dict, optional): same as interactions_filter
            above but applied to interactions2.
            Defaults to {}.
        filters (list of dict, optional): For plotting multiple filtering
            schemes applied to each sample, each in a new panel. Each
            dictionary in this list follows a similar structure as
            interactions_filter, but also requires the key-value pair:
            {"interactions": interactions} where interactions is as described
            above. interactions and interactions_filter arguments above will be
            ignored. interactions2 and interactions2_filter will be displayed
            in every panel.
            Defaults to [].
        annotations (list, optional): a list of keys from sample.data used to
            retrieve sequence annotations. These annotations are displayed next
            to the sequence, outside of the circle.
            Defaults to [].
        profile (str, optional): a key from sample.data used to retrieve per-
            nucleotide data. These data may be used to color nucleotides.
            Defaults to "profile".
        labels (str, optional): Same length as samples list. Labels to
            be used as titles.
            Defaults to default sample name.
        plot_kwargs (dict, optional): kwargs passed to Circle(). See
            rnavigate.plots.Circle for more detail.
            Defaults to {}.
        **kwargs: additional keyword arguments are passed to Circle.plot_data.
            see rnavigate.plots.Circle.plot_data for more detail.

    Returns:
        rnavigate.plots.Circle: object containing matplotlib figure and axes
            with additional plotting and file saving methods
    """
    # use mutable defaults
    interactions_filter = replace_sentinels(interactions_filter)
    interactions2_filter = replace_sentinels(interactions2_filter)
    annotations, plot_kwargs = replace_sentinels(annotations, plot_kwargs)
    if labels is None:
        labels = [sample.sample for sample in samples]
    # coerce interactions and interactions_filter into filters format
    if filters is None:
        filters = [{"interactions": interactions} | interactions_filter]
    # if filters and samples > 1, rows = # samples, columns = # filters
    if (len(filters) > 1) and (len(samples) > 1):
        plot_kwargs |= {'rows': len(filters), 'cols': len(samples)}
    # initialize plot
    sequence = get_sequence(sequence, samples[0], structure)
    num_samples = len(samples) * len(filters)
    plot = plots.Circle(num_samples=num_samples,
                        sequence=sequence, **plot_kwargs)
    # loop through samples and filters, adding each as a new axis
    for sample, label in zip(samples, labels):
        sample.filter_interactions(interactions2, **interactions2_filter)
        data_dict = sample.get_data({
            'ct': structure,
            'comp': structure2,
            'interactions2': interactions2,
            'profile': profile,
            'annotations': annotations})
        data_dict = fit_data(data_dict, sequence)
        for filt in filters:
            sample.filter_interactions(**filt)
            interactions = sample.get_data(filt['interactions'])
            data_dict['interactions'] = fit_data(interactions, sequence)
            plot.plot_data(**data_dict, label=label, **kwargs)
    plot.set_figure_size()
    if colorbar:
        plot.plot_colorbars()
    return plot


def plot_linreg(samples, sequence=None, structure=None, profile="profile",
                labels=None, plot_kwargs=_dict, **kwargs):
    """Performs linear regression analysis and generates scatter plots of all
    sample-to-sample profile vs. profile comparisons. Colors nucleotides by
    identity or base-pairing status.

    Args:
        samples (list of rnavigate.Sample): Samples to retreive data from.
            number of panels will equal the length of this list squared.
        ct (str, optional): a key from sample.data to retreive a secondary
            structure. Scatter plot points may be colored by base-pairing
            status in this structure.
        profile (str, optional): a key from sample.data used to retrieve per-
            nucleotide data. These data are used for the linear regression.
        labels (str, optional): Same length as samples list. Labels to
            be used in titles.
            Defaults to default sample name.
        plot_kwargs (dict, optional): kwargs passed to LinReg(). See
            rnavigate.plots.LinReg for more detail.
            Defaults to {}.
        **kwargs: additional keyword arguments are passed to LinReg.plot_data.
            see rnavigate.plots.LinReg.plot_data for more detail.

    Returns:
        rnavigate.plots.LinReg: object containing matplotlib figure and axes
            with additional plotting and file saving methods
    """
    plot_kwargs = replace_sentinels(plot_kwargs)
    if labels is None:
        labels = [sample.sample for sample in samples]
    sequence = get_sequence(sequence, samples[0], profile)
    plot = plots.LinReg(len(samples), **plot_kwargs)
    for sample, label in zip(samples, labels):
        data_dict = sample.get_data({
            'ct': structure,
            'profile': profile})
        data_dict = fit_data(data_dict, sequence)
        plot.plot_data(**data_dict, label=label, **kwargs)
    plot.set_figure_size()
    return plot

def plot_roc(samples, structure="ct", profile="profile", labels=None,
             plot_kwargs=_dict, **kwargs):
    """Performs receiver operator characteristic analysis (ROC), calculates
    area under ROC curve (AUC), and generates ROC plots to assess how well
    per-nucleotide data predicts base-paired status. Does this for all
    positions as well as positions categorized by nucleotide
    5 plots: All, A, U, C, G

    Args:
        samples (list of rnavigate.Sample): Samples to retreive data from.
            All samples are plotted on the same set of axes.
        ct (str, optional): a key from sample.data to retreive a secondary
            structure. Base-pairing status retreived from this data.
        profile (str, optional): a key from sample.data used to retrieve per-
            nucleotide data. These data are used for the ROC/AUC analysis.
        labels (str, optional): Same length as samples list. Labels to
            be used in legends.
            Defaults to default sample name.
        plot_kwargs (dict, optional): kwargs passed to ROC(). See
            rnavigate.plots.ROC for more detail.
            Defaults to {}.
        **kwargs: additional keyword arguments are passed to ROC.plot_data.
            see rnavigate.plots.ROC.plot_data for more detail.

    Returns:
        rnavigate.plots.ROC: object containing matplotlib figure and axes with
            additional plotting and file saving methods
    """
    plot_kwargs = replace_sentinels(plot_kwargs)
    if labels is None:
        labels = [sample.sample for sample in samples]
    plot = plots.ROC(len(samples), **plot_kwargs)
    for sample, label in zip(samples, labels):
        data_dict = sample.get_data({
            'ct': structure,
            'profile': profile})
        data_dict = fit_data(data_dict, data_dict['ct'])
        plot.plot_data(**data_dict, label=label, **kwargs)
    plot.set_figure_size()
    return plot


def plot_disthist(samples, structure="pdb", interactions=None,
                  interactions_filter=_dict, bg_interactions=None,
                  bg_interactions_filter=_dict, filters=None, labels=None,
                  same_axis=False, plot_kwargs=_dict, **kwargs):
    """Calculates 3D distance of nucleotides in inter-nucleotide data and plots
    the distribution of these distances. Compares this to a 'background'
    distribution consisting of either all pairwise distances in structure, or
    those defined by bg_interactions and bg_interactions_filter

    Args:
        samples (list of rnavigate.Sample): Samples to retreive data from.
            number of panels will equal the length of this list unless
            same_axis is set to True.
        structure (str, optional): a key from sample.data to retreive a PDB
            structure with atomic coordinates.
        interactions (str, optional): a key from sample.data to retrieve inter-
            nucleotide data. These data are mapped to PDB sequence coordinates,
            filtered using interactions_filter arguments, and used to calculate
            distance distribution histograms.
            Defaults to None.
        interactions_filter (dict, optional): These key-value pairs are passed
            as keyword arguments to sample.filter_interactions along with
            interactions=interactions and fit_to=sequence. See
            rnavigate.Sample.filter_interactions for more detail.
            Defaults to {}.
        bg_interactions (str, optional): same as interactions above. used to
            calulate 'background' distance distribution histograms.
            Defaults to None.
        bg_interactions_filter (dict, optional): same as interactions_filter
            above but applied to bg_interactions.
            Defaults to {}.
        filters (list of dict, optional): For plotting multiple filtering
            schemes applied to each sample. Each dictionary in this list
            follows a similar structure as interactions_filter, but also
            requires the key-value pair: {"interactions": interactions} where
            interactions is as described above. interactions and
            interactions_filter arguments above will be ignored.
            Defaults to [].
        labels (str, optional): Same length as samples list. Labels to
            be used as titles.
            Defaults to default sample name.
        plot_kwargs (dict, optional): kwargs passed to DistHist(). See
            rnavigate.plots.DistHist for more detail.
            Defaults to {}.
        **kwargs: additional keyword arguments are passed to DistHist.plot_data
            see rnavigate.plots.DistHist.plot_data for more detail.

    Returns:
        rnavigate.plots.DistHist: object containing matplotlib figure and axes
            with additional plotting and file saving methods
    """
    # use mutable defaults
    interactions_filter = replace_sentinels(interactions_filter)
    bg_interactions_filter = replace_sentinels(bg_interactions_filter)
    plot_kwargs = replace_sentinels(plot_kwargs)
    if labels is None:
        labels = [sample.sample for sample in samples]
    # coerce interactions and interactions_filter into filters format
    if filters is None:
        filters = [{"interactions": interactions} | interactions_filter]
    # if filters and samples > 1, rows = # samples, columns = # filters
    if (len(filters) > 1) and (len(samples) > 1) and (not same_axis):
        plot_kwargs |= {'rows': len(filters), 'cols': len(samples)}
    # initialize plot
    num_samples = len(samples) * len(filters)
    if same_axis:
        plot = plots.DistHist(num_samples=1, **plot_kwargs)
        axis = plot.axes[0, 0]
    else:
        plot = plots.DistHist(num_samples=num_samples, **plot_kwargs)
        axis = None
    # loop through samples and filters, adding each as a new axis
    for sample, label in zip(samples, labels):
        sample.filter_interactions(bg_interactions, **bg_interactions_filter)
        data_dict = sample.get_data({
            'structure': structure,
            'bg_interactions': bg_interactions
        })
        data_dict = fit_data(data_dict, data_dict['structure'])
        for filt in filters:
            sample.filter_interactions(**filt)
            interactions = sample.get_data(filt['interactions'])
            data_dict['interactions'] = fit_data(interactions, structure)
            plot.plot_data(**data_dict, label=label, ax=axis, **kwargs)
    plot.set_figure_size()
    return plot
