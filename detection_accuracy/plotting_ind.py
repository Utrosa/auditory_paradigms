#! /usr/bin/env python
# Time-stamp: <2026-03-20 m.utrosa@bcbl.eu>
'''
Visualize the relationship between variables that define trials.
Plots a count plot and a bar plot separately for each variable.

Count plot
- allows grouping of variable

Bar plot
- takes a subset of data as input
'''
# 01. PREPARATION ---------------------------------------------------------------------------------
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import seaborn as sns

# 02. DEFINE THE FUNCTION -------------------------------------------------------------------------
def plot_count(df, title, x_name, x_label, y_name, y_label, y_group=None, col_no=3, save_as=None, show=False):
	
	sns.set_theme(style="white", font="sans-serif")
	
	if y_group:
		h = sns.FacetGrid(
			data=df,
			col=x_name,
			col_wrap=col_no, # incompatible with row
			height=2,
			aspect=1,
			sharey=True,
			sharex=True
			)

		h.map_dataframe(
			sns.countplot,
			data=df,
			x=y_name,
			hue=y_group,
			palette="viridis"
			)
	else:
		h = sns.FacetGrid(
			data=df,
			col=x_name,
			col_wrap=col_no, # incompatible with row
			height=2,
			aspect=1,
			sharey=True,
			sharex=True,
			hue=x_name,
			palette="viridis"
			)

		h.map_dataframe(
			sns.countplot,
			data=df,
			x=y_name
			)

	h.set_axis_labels("", "")
	# h.set_titles("{col_name}", size=12)

	for ax in h.axes.flat:
		ax.tick_params(
			axis="x",
			which="both",
			bottom=True,
			top=False,
			labelbottom=True,
			labelsize=11,
			rotation=90
			)
		ax.tick_params(
			axis="y",
			which="both",
			left=True,
			right=False,
			labelleft=True,
			labelsize=11
			)
		ax.tick_params(labelbottom=True, labelleft=True)

	h.fig.supxlabel(x_label, fontsize=14)
	h.fig.supylabel(y_label, fontsize=14)
	h.fig.suptitle(
		title,
		fontsize=16,
		weight="bold"
		)

	sns.despine()

	# Optionally show
	if show:
		plt.show()

	# Optionally save
	if save_as:
		h.fig.savefig(save_as, dpi=300, bbox_inches='tight')
		print(f"Figure saved to: {save_as}")

	# Close the figure to free memory
	h.fig.clear()
	plt.close(h.fig)

def plot_bar(df, title, x_name, x_label, y_name, y_label, col_no=2, save_as=None, show=False):
	sns.set_theme(style="white", palette="Spectral", font="sans-serif")
	
	g = sns.FacetGrid(
		df,
		col=x_name,
		col_wrap=col_no,
		height=3,
		aspect=1.5,
		sharey=True,
		sharex=True
	)
	
	g.map_dataframe(
		sns.barplot,
		x=y_name,
		y="COUNT",
		order=sorted(df[y_name].unique())
	)

	g.set_axis_labels("", "")
	g.set_titles("{col_name}", size=11)

	for ax in g.axes.flat:
		ax.tick_params(
			axis="x",
			which="both",
			bottom=True,
			top=False,
			labelbottom=True,
			rotation=90,
			labelsize=8
			)
		ax.tick_params(
			axis="y",
			which="both",
			left=True,
			right=False,
			labelleft=True,
			labelsize=8
			)
		ax.tick_params(labelbottom=True, labelleft=True)

	g.fig.supxlabel(x_label, fontsize=11)
	g.fig.supylabel(y_label, fontsize=11)

	g.fig.suptitle(
		title,
		fontsize=11,
		weight="bold"
		)

	sns.despine()

	# Optionally save
	if save_as:
		g.fig.tight_layout(rect=[0, 0, 1, 1.03])
		g.fig.savefig(save_as, dpi=300, bbox_inches='tight')
		print(f"Figure saved to: {save_as}")

	# Optionally show
	if show:
		plt.show()

	# Close the figure to free memory
	g.fig.clear()
	plt.close(g.fig)

def calculate_distributions(dataDir, filename, y_name, x_name):

	# A.) LOAD THE COMBINATIONS -------------------------------------------------------------------
	dataPath = Path(dataDir) / filename
	df = pd.read_csv(dataPath)

	# B.) CALCULATE THE DISTRIBUTIONS -------------------------------------------------------------
	# Get Y per category of X
	groups = df.groupby(by=[x_name, y_name])[y_name].count()

	# Add zero occurrence if y_name values don't exist with x_name values
	complete_groups = groups.unstack(fill_value=0).stack()
	plot_groups = complete_groups.reset_index(name='COUNT')

	return plot_groups

# 03. CREATE FIGURES -----------------------------------------------------------------------------
if __name__ == "__main__":

	# Load the the csv
	sesID = 9
	dataDir  = Path('/home/mutrosa/Documents/projects/auditory_paradigms/detection_accuracy/selected_trials')
	filename = f'ses-{sesID:003d}_exp_parameter_combo.csv'
	df = pd.read_csv(dataDir / filename)

	# ------ TIMING DEVIANCY MAGNITUDE | TIMING DEVIANCY LOCATION
	y_name = "dev";
	y_label = "Timing Deviation [msec]";
	y_group = None
	x_name = "dev_loc"
	x_label = "Timing Deviation Location [tone idx]"
	title_count = f"Count of Timing Deviants | Timing Deviants Location for SES-{sesID:003d}"
	title_bar   = f"Occurrences of Timing Deviants | Timing Deviants Location for SES-{sesID:003d}"

	plot_group = calculate_distributions(dataDir, filename, y_name, x_name)
	plot_count(df, title_count, x_name, x_label, y_name, y_label, y_group, save_as="timDev-posneg_count.png", show=True)
	# plot_count(df, title_count, x_name, x_label, y_name, y_label, save_as="timDev-absolute_count.png", show=True)
	# plot_bar(plot_group, title_bar, x_name, x_label, y_name, y_label, save_as="timDev-absolute_bar.png", show=True)