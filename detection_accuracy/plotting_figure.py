#! /usr/bin/env python
# Time-stamp: <2026-03-28 m.utrosa@bcbl.eu>
'''
Visualize the relationships between variables that define trials.
- inter trial interval (ITI) [msec]
- size of timing/frequency deviants [msec]
- location of timing/frequency deviants [tone idx]

Plots several `countplots` on the same figure for a set of variables.
Returns one figure.
'''

# 01. PREPARATION ---------------------------------------------------------------------------------
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import seaborn as sns
import numpy as np
import math
import ast # to handle data types in pandas dataframes

# 02. DEFINE THE FUNCTION -------------------------------------------------------------------------
def plot_count(df, title, x_names, x_label, y_name, y_order, y_label, y_group=None, save_as=None, show=False, max_cols=7, rect=(0,0,1,1), fig_n=3.5):
    '''
    Plots count plots. These can be thought of as histograms of "y_name" 
    for every unique value of x_names, where "y_name" and "x_names" are
    categorical variables. "y_group" is the grouping variable (hue).
    '''
    # --------- 01. Calculate layout --------- 
    # For each column given in x_names, flatten the values, drop NaNs,
    # selet unique values only, sort in ascending order, and turn to a list.
    uniques = {
        col: list(sorted(df[col].explode().dropna().unique()))
        for col in x_names
    }

    # Calculate the number of rows needed for each variable
    rows_per_var = {x: math.ceil(len(vals) / max_cols) for x, vals in uniques.items()}
    total_rows = sum(rows_per_var.values())

    # Determine the maximum width (columns)
    n_cols = min(max_cols, max(len(v) for v in uniques.values()))

    # --------- 02. Set up the grid and theme --------- 
    fig, axes = plt.subplots(
        total_rows,
        n_cols,
        figsize=(n_cols * fig_n, total_rows * fig_n + 0.5),
        sharex="row",
        sharey="row"
    )

    # Allow plotting only one parameter
    # Non-array inputs are converted to arrays.
    # Arrays that already have two or more dimensions are preserved.
    axes = np.atleast_2d(axes)

    sns.set_theme(style="white", font="sans-serif")
    if y_group:
        palettes = ["blend:#7AB,#EDA", "flare", "ch:s=.25,rot=-.25"]
    else:
        colors = sns.color_palette("pastel", len(x_names))

    # --------- 03. Plot --------- 
    row_offset = 0

    for i, x in enumerate(x_names):
        vals = uniques[x]
        n_rows = rows_per_var[x]

        # Select color / palette
        if y_group:
            palette = palettes[i % len(palettes)]
        else:
            color = colors[i % len(colors)]

        for r in range(n_rows):
            row = row_offset + r

            # Slice values for this row
            chunk = vals[r * max_cols:(r + 1) * max_cols]

            for c, val in enumerate(chunk):
                ax = axes[row, c]

                # Calculate the distributions
                subset = df[df[x] == val]
                if y_group:
                    sns.countplot(
                        data=subset,
                        x=y_name,
                        order=order,
                        hue=y_group,
                        palette=palette,
                        ax=ax
                    )
                else:
                    sns.countplot(
                        data=subset,
                        x=y_name,
                        order=order,
                        color=color,
                        ax=ax
                    )

                ax.set_title(f"{x}: {val}", fontsize=11, weight="bold")
                ax.set_xlabel("")
                ax.set_ylabel("")

                # Add a single legend to the figure
                if y_group:
                    if val == vals[-1]:
                        ax.legend(
                            fontsize=11,
                            title_fontsize=11,
                            loc='center left',
                            bbox_to_anchor=(1.05, 0.5)
                        )
                    else:
                        if ax.get_legend():
                            ax.get_legend().remove()

                ax.tick_params(
                    axis="x",
                    which="both",
                    bottom=True,
                    top=False,
                    labelbottom=True,
                    labelsize=8,
                    rotation=90
                )
                ax.tick_params(
                    axis="y",
                    which="both",
                    left=True,
                    right=False,
                    labelleft=True,
                    labelsize=8
                )

            # Remove unused subplots in this row
            for c in range(len(chunk), n_cols):
                axes[row, c].axis('off')

        # Move row offset AFTER processing this variable
        row_offset += n_rows

    # Global
    fig.supxlabel(x_label, fontsize=12, weight="bold", va="bottom")
    fig.supylabel(y_label, fontsize=12, weight="bold", ha="left")
    fig.suptitle(title, fontsize=12, weight="bold", va="bottom")
    sns.despine()

    # Adjust size
    # fig.subplots_adjust(right=0.80, left=0.07, top=0.93, bottom=0.08)
    if y_group:
        fig.subplots_adjust(right=0.80, left=0.07, top=0.93, bottom=0.08)
    else:
        plt.tight_layout(rect=rect)

    # Optionally save
    if save_as:
        fig.savefig(save_as, dpi=300)
        print(f"Figure saved to: {save_as}")

    # Optionally show
    if show:
        plt.show()

    # Close, so it's not in memory
    fig.clear()
    plt.close(fig)

# 03. CREATE FIGURES -----------------------------------------------------------------------------
dataDir  = Path('/home/mutrosa/Documents/projects/auditory_paradigms/detection_accuracy/trials')

for idx in range(300, 350):
    i = idx + 1

    # Load the csv with trials
    filename = f'ses-{i:003d}_exp_parameter_combo.csv'
    df_raw = pd.read_csv(dataDir / filename)

    # Correct column data types: lists should not be strings
    list_cols = ["freq_dev", "freq_dev_type", "freq_loc", "freq_diff", "freq_diff_abs"]
    for col in list_cols:
      df_raw[col] = df_raw[col].apply(
          lambda x: ast.literal_eval(x) if isinstance(x, str) else x
      )

    # Explode the dataframe
    df_trials = df_raw.copy()
    df_events = df_raw.explode(list_cols)

    # Remove silent trials
    df_trials.dropna(inplace=True)
    df_events.dropna(inplace=True)

    # ---------------------------------------------------------------------------------------------
    # TIMING DEVIANTS POSITION
    # How is the position of timing deviants distributed ?
    # Use exploded dataframe (plot is on event-level, not trial-level)

    # Negative vs Positive
    params = ['base_freq', 'freq_diff', 'freq_dev', 'freq_dev_no']
    order = sorted(df_events['dev'].unique())
    plot_count(
        df=df_events,
        title=f"DISTRIBUTION OF TIMING DEVIANTS | SES-{i:003d}",
        x_names=params,
        x_label="Timing Deviants [msec]",
        y_name='dev',
        y_order=order,
        y_label="Count",
        save_as=f"plots/ses-{i:003d}_timeDev-dir.png",
        show=False,
        max_cols=7,
        rect=(0.02, 0, 0.93, 0.98) # left, bottom, right, top
    )

    # Absolute
    params = ['base_freq', 'freq_diff_abs', 'freq_dev', 'freq_dev_no']
    plot_count(
        df=df_events,
        title=f"DISTRIBUTION OF TIMING DEVIANTS | SES-{i:003d}",
        x_names=params,
        x_label="Timing Deviants [msec]",
        y_name='dev',
        y_order=order,
        y_label="Count",
        save_as=f"plots/ses-{i:003d}_timeDev-abs.png",
        show=False,
        max_cols=7,
        rect=(0.02, 0, 0.93, 0.98) # left, bottom, right, top
    )

    # ---------------------------------------------------------------------------------------------
    # TIMING DEVIANCY | DEV LOC, BASE FREQ, FREQ DEV NUMBER
    # How are timing deviants distributed across single events that vary across trials?
    # Use "trials" dataframe (one row per trial)
    # Control check: 
    #       The distribution of DEV over DEV_LOC should be perfectly counterbalanced.
    #       If zero included, there's more values as we're counting for two deviations:
    #       positive and negative zero.
    # params = ["dev_loc", "base_freq", "freq_dev_no"]

    # Negative vs Positive
    # order = sorted(df_trials['dev'].unique())
    # plot_count(
    #     df=df_trials, 
    #     title=f"TIMING DEVIANCY | DEV LOC, BASE FREQ, FREQ DEV NO for SES-{i:003d}",
    #     x_names=params,
    #     x_label="Timing Deviation [ms]",
    #     y_name='dev',
    #     y_order=order,
    #     y_label="Count",
    #     save_as=f"plots/ses-{i:003d}_timDev-dir.png",
    #     show=False,
    #     max_cols=7,
    #     rect=(0.02, 0, 0.93, 1) # left, bottom, right, top
    # )

    # Absolute
    # order = sorted(df_trials['dev_abs'].unique())
    # plot_count(
    #     df=df_trials, 
    #     title=f"TIMING DEVIANCY | DEV LOC, BASE FREQ, FREQ DEV NO for SES-{i:003d}",
    #     x_names=params,
    #     x_label="Timing Deviation [ms]",
    #     y_name='dev_abs',
    #     y_order=order,
    #     y_label="Count",
    #     save_as=f"plots/ses-{i:003d}_timDev-abs.png",
    #     show=False,
    #     max_cols=7,
    #     rect=(0.02, 0, 0.93, 1) # left, bottom, right, top
    # )

    # ---------------------------------------------------------------------------------------------
    # FREQUENCY DEVIANCY
    # How are frequency deviants [Hz] distributed ?
    # Use exploded dataframe (plot is on event-level, not trial-level)
    
    # Negative vs Positive
    # params = ["base_freq", "freq_dev_no", "freq_loc", "dev", "dev_loc"]
    # order = sorted(df_events['freq_dev'].unique())
    # plot_count(
    #     df=df_events, 
    #     title=f"FREQUENCY DEVIANCY | SES-{i:003d}",
    #     x_names=params,
    #     x_label="Frequency Deviation [Hz]",
    #     y_name='freq_dev',
    #     y_order=order,
    #     y_label="Count",
    #     save_as=f"plots/ses-{i:003d}_freqDev_dir.png",
    #     show=False,
    #     max_cols=7,
    #     rect=(0.02, 0.0, 0.93, 0.93), # left, bottom, right, top
    # )

    # Absolute
    # params = ["base_freq", "freq_dev_no", "freq_loc", "dev_abs", "dev_loc"]
    # plot_count(
    #     df=df_events, 
    #     title=f"FREQUENCY DEVIANCY | SES-{i:003d}",
    #     x_names=params,
    #     x_label="Frequency Deviation [Hz]",
    #     y_name='freq_dev',
    #     y_order=order,
    #     y_label="Count",
    #     save_as=f"plots/ses-{i:003d}_freqDev_abs.png",
    #     show=False,
    #     max_cols=7,
    #     rect=(0.02, 0, 0.93, 1) # left, bottom, right, top
    # )

    # ---------------------------------------------------------------------------------------------
    # FREQUENCY DIFFERENCE
    # How is the difference between base and deviant frequency distributed ?
    # Use exploded dataframe (plot is on event-level, not trial-level)
    # params = ['base_freq', 'freq_dev_no', 'freq_dev', 'freq_loc', 'dev', 'dev_loc']

    # Negative vs Positive
    # order = sorted(df_events['freq_diff'].unique())
    # plot_count(
    #     df=df_events,
    #     title=f"FREQUENCY DIFFERENCE | SES-{i:003d}",
    #     x_names=params,
    #     x_label="Frequency Difference [Hz]",
    #     y_name='freq_diff',
    #     y_order=order,
    #     y_label="Count",
    #     save_as=f"plots/ses-{i:003d}_freqDiff-dir.png",
    #     show=False,
    #     max_cols=7,
    #     rect=(0.02, 0, 0.93, 0.98) # left, bottom, right, top
    # )

    # Absolute
    # order = sorted(df_events['freq_diff_abs'].unique())
    # plot_count(
    #     df=df_events,
    #     title=f"FREQUENCY DIFFERENCE | SES-{i:003d}",
    #     x_names=params,
    #     x_label="Frequency Difference [Hz]",
    #     y_name='freq_diff_abs',
    #     y_order=order,
    #     y_label="Count",
    #     save_as=f"plots/ses-{i:003d}_freqDiff-abs.png",
    #     show=False,
    #     max_cols=7,
    #     rect=(0.02, 0, 0.93, 0.98) # left, bottom, right, top
    # )

    # ---------------------------------------------------------------------------------------------
    # FREQUENCY DEVIANTS NUMBER
    # How is the number of frequency deviants distributed ?
    # Use exploded dataframe (plot is on event-level, not trial-level)
    
    # Negative vs Positive
    # params = ['base_freq', 'freq_diff', 'freq_dev', 'freq_loc', 'dev', 'dev_loc']
    # order = sorted(df_events['freq_dev_no'].unique())
    # plot_count(
    #     df=df_events,
    #     title=f"FREQUENCY DEVIANTS COUNT PER TRIAL | SES-{i:003d}",
    #     x_names=params,
    #     x_label="Frequency Deviants Count",
    #     y_name='freq_dev_no',
    #     y_order=order,
    #     y_label="Count",
    #     save_as=f"plots/ses-{i:003d}_freqDevNo-dir.png",
    #     show=False,
    #     max_cols=7,
    #     rect=(0.02, 0, 0.93, 0.98) # left, bottom, right, top
    # )

    # Absolute
    # params = ['base_freq', 'freq_diff_abs', 'freq_dev', 'freq_loc', 'dev_abs', 'dev_loc']
    # plot_count(
    #     df=df_events,
    #     title=f"FREQUENCY DEVIANTS COUNT PER TRIAL | SES-{i:003d}",
    #     x_names=params,
    #     x_label="Frequency Deviants Count",
    #     y_name='freq_dev_no',
    #     y_order=order,
    #     y_label="Count",
    #     save_as=f"plots/ses-{i:003d}_freqDevNo-abs.png",
    #     show=False,
    #     max_cols=7,
    #     rect=(0.02, 0, 0.93, 0.98) # left, bottom, right, top
    # )