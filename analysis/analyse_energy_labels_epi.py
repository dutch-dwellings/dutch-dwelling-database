import os
import sys

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_utils import get_connection
from analyse_energy_labels import energy_label_colours_improved2 as energy_label_colours
from utils.file_utils import project_dir

query = "SELECT energieprestatieindex, energieklasse, berekeningstype FROM energy_labels WHERE gebouwklasse = 'W' AND energieprestatieindex IS NOT NULL AND energieklasse is not NULL LIMIT 100000"
# query = "SELECT energieprestatieindex, energieklasse, berekeningstype FROM energy_labels WHERE gebouwklasse = 'W' AND energieprestatieindex IS NOT NULL AND energieklasse is not NULL ORDER BY energieklasse DESC"
averages_query = "SELECT energieklasse, AVG(energieprestatieindex) FROM energy_labels WHERE energieprestatieindex IS NOT NULL GROUP BY energieklasse"

# TODO: labels and epi throughout the years?

'''
EP
EPA
"ISSO82.3, versie 3.0, oktober 2011"
	ISSO 82.3
NTA-8800 (basisopname woningbouw)
NTA-8800 (detailopname woningbouw)
"Nader Voorschrift, versie 1.0, 1 februari 2014 met erratalijst dd 03-11-201"
	Nader Voorschrift
"Nader Voorschrift, versie 1.0, 1 februari 2014 met erratalijst, addendum 1 juli 2018"
	Nader Voorschrift (addendum)
"Rekenmethodiek Definitief Energielabel, versie 1.2, 16 september 2014"
'''

calculation_colours = {
	'NTA-8800 (detailopname woningbouw)': (0.16342174, 0.0851396, 0.21088893),
	'NTA-8800 (basisopname woningbouw)': (0.33067031, 0.11701189, 0.30632563),
	'Rekenmethodiek': (0.51728314, 0.1179558, 0.35453252),
	'Nader Voorschrift (addendum)': (0.70457834, 0.0882129, 0.34473046),
	'Nader Voorschrift': (0.86641628, 0.17387796, 0.27070818),
	'ISSO 82.3': (0.94291042, 0.37549479, 0.26369821),
	'EPA': (0.96173392, 0.57988594, 0.41844491),
	'EP': (0.96656022, 0.75658231, 0.62527295)
}

def matplot(df, title=None):
	plt.clf()
	print('Plotting...')
	plt.scatter(df['epi'], df['label'], alpha=1/256, c=df['label'].map(energy_label_colours))
	plt.xlim(-2.5, 7.5)
	plt.title(title)
	print('Showing...')
	# plt.show()
	title_sanitized = '_'.join(title.split(' '))
	plt.savefig(f'energy_labels_{title_sanitized}.png')

def seaborn_scatter(df):
	print("plotting seaborn")
	sns.scatterplot(data=df, x='epi', y='label', alpha=0.01)
	# sns.violinplot(data=df, x='epi', y='label', hue='label', color=energy_label_colours)
	print('show seaborn')
	plt.show()


def seaborn_ridgeplot(df):
	# modified from https://seaborn.pydata.org/examples/kde_ridgeplot.html

	# Create the data

	# Initialize the FacetGrid object
	pal = sns.cubehelix_palette(10, rot=-.25, light=.7)
	g = sns.FacetGrid(df, row="label", hue="label", aspect=15, height=.5, palette=pal)

	# Draw the densities in a few steps
	g.map(sns.kdeplot, "epi",
		bw_adjust=.5, clip_on=False,
		fill=True, alpha=1, linewidth=1.5)
	g.map(sns.kdeplot, "epi", clip_on=False, color="w", lw=2, bw_adjust=.5)
	g.map(plt.axhline, y=0, lw=2, clip_on=False)


	# Define and use a simple function to label the plot in axes coordinates
	def label(x, color, label):
		ax = plt.gca()
		ax.text(0, .2, label, fontweight="bold", color=color,
			ha="left", va="center", transform=ax.transAxes)

	g.map(label, "epi")

	# Set the subplots to overlap
	g.fig.subplots_adjust(hspace=-.25)

	# Remove axes details that don't play well with overlap
	g.set_titles("")
	g.set(yticks=[])
	g.despine(bottom=True, left=True)

	plt.show()

def densities_plot(df, common_norm=True):
	print("Plotting kdeplot...")
	sns.kdeplot(
		data=df,
		x="epi",
		hue="label",
		fill=True,
		common_norm=common_norm,
		palette=energy_label_colours,
		alpha=.7,
		linewidth=0,
		# multiple="stack", # also nice to see total distribution
		gridsize=2000
	)
	# g._legend.set_title(None)
	print('Adjusting x-limits...')
	plt.xlim(0, 4)
	plt.xlabel('energieprestatieindex')
	# get rid of plot frame
	sns.despine()
	print('Saving to file')
	if common_norm:
		filename = 'analyse_energy_labels_epi.png'
	else:
		filename = 'analyse_energy_labels_epi_individual.png'
	path = os.path.join(project_dir, 'analysis', filename)
	plt.savefig(path, dpi=300)

	# TODO:
	# scale to occurences of the energy labels in dataset,
	# not filtered on existence of EPI

def calculation_types_plot_aggregated(df):
	# reverse data frame because somehow this type of plot
	# has the order in reverse
	df = df.copy()
	df = df.iloc[::-1]
	# df = df.copy()
	# df = df.sort_values('label')
	print(df.head())
	print('Plotting all calculation types in one plot...')
	g = sns.catplot(
		data=df,
		x='epi',
		y='label',
		hue='type',
		jitter=False,
		dodge=True,
		alpha=1/256,
		palette=calculation_colours)
	plt.xlim(0, 5)

	axes = g.axes.flat
	print(axes)
	print(list(axes))
	ax = g.axes.flat[0]
	# fig, ax = plt.subplots()
	# print(dir(plt))
	# print(dir(plt.Axes))
	ax.set_xticks([0.6, 0.9, 1.2, 1.4, 1.8, 2.1, 2.4, 2.7], minor=False)
	ax.xaxis.grid(True, which='major', linewidth=0.5)

	print('Saving plot...')
	filename = 'energy_labels_epi_calculation_types.png'
	path = os.path.join(project_dir, 'analysis', filename)
	plt.savefig(path, dpi=300)

def calculation_types_plots(df):
	calculation_types = df['type'].unique()
	for calculation_type in calculation_types:
		df_filtered = df[df['type'] == calculation_type]
		matplot(df_filtered, title=calculation_type)

def main():
	cursor = get_connection().cursor()
	print('Executing query...')
	cursor.execute(query)

	results = cursor.fetchall()
	print("Converting to DataFrame...")
	df = pd.DataFrame(results, columns=['epi', 'label', 'type'])

	print('Replacing values in DataFrame...')
	df = df.replace({
		'ISSO82.3, versie 3.0, oktober 2011': 'ISSO 82.3',
		'Nader Voorschrift, versie 1.0, 1 februari 2014 met erratalijst, addendum 1 juli 2018': 'Nader Voorschrift (addendum)',
		'Nader Voorschrift, versie 1.0, 1 februari 2014 met erratalijst dd 03-11-201': 'Nader Voorschrift'
	})

	calculation_types_plot_aggregated(df)
	# seaborn_kdeplot(df)
	# seaborn_kdeplot(df, common_norm=False)
	# matplot(df)

if __name__ == '__main__':
	main()
