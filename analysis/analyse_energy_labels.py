import os
import sys

import pandas as pd

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis_utils import query_to_table
from utils.database_utils import get_connection


# extracted from 'energielabel-voorbeeld-woningen.pdf'
energy_label_colours = {
	'A+++++': '#009037', # dark green
	 'A++++': '#009037', # dark green
	  'A+++': '#009037', # dark green
	   'A++': '#009037', # dark green
	    'A+': '#009037', # dark green
	     'A': '#009037', # dark green
	     'B': '#55ab26', # green
	     'C': '#c8d100', # light green
	     'D': '#ffec00', # yellow
	     'E': '#faba00', # orange
	     'F': '#eb6909', # light red
	     'G': '#e2001a'  # red
}
# improved version (with seperate colours going past 'A')
energy_label_colours_improved = {
	'A+++++': '#0a3d1d', # darkest green
	 'A++++': '#005922',
	  'A+++': '#007a2f',
	   'A++': '#5ca336',
	    'A+': '#81ba0f',
	     'A': '#b7d400', # light green
	     'B': '#f6fa00', # yellowish green
	     'C': '#ffdd00',
	     'D': '#ffb700',
	     'E': '#f28d0a',
	     'F': '#e66609',
	     'G': '#e20000' # red
}
# Take the original version since there are not a lot
# of A+... values, but do include a different value for
# A+... values than A.
energy_label_colours_improved2 = {
	'A+++++': '#005922', # darker green
	 'A++++': '#005922', # darker green
	  'A+++': '#005922', # darker green
	   'A++': '#005922', # darker green
	    'A+': '#005922', # darker green
	     'A': '#009037', # dark green
	     'B': '#55ab26', # green
	     'C': '#c8d100', # light green
	     'D': '#ffec00', # yellow
	     'E': '#faba00', # orange
	     'F': '#eb6909', # light red
	     'G': '#e2001a'  # red
}


building_type_title = "Number of dwellings per building type (EP-Online)"
building_type_query = "SELECT pand_gebouwtype, COUNT(*) FROM energy_labels WHERE pand_gebouwklasse = 'W' GROUP BY pand_gebouwtype"

energy_label_title = "Number of dwellings per energy label (EP-Online)"
energy_label_query = "SELECT pand_energieklasse, COUNT(*) FROM energy_labels WHERE pand_gebouwklasse = 'W' GROUP BY pand_energieklasse"

# query_to_table(building_type_query, title=building_type_title, total=True)
# query_to_table(energy_label_query, title=energy_label_title, total=True)

inspection_year_title = "Number of energy label recordings per year"
inspection_year_query = "SELECT date_part('year', pand_opnamedatum), COUNT(*) FROM energy_labels WHERE pand_gebouwklasse = 'W' GROUP BY date_part('year', pand_opnamedatum)"

energy_label_year_title = "Energy labels per recording year"
energy_label_year_query = "SELECT pand_energieklasse, COUNT(*) FROM energy_labels WHERE pand_gebouwklasse = 'W' AND date_part('year', pand_opnamedatum) = %s GROUP BY pand_energieklasse;"


def energy_labels_per_building_year(cursor, relative=False):

	building_year_title = "Energy labels per building year"
	# This takes a while
	building_year_query = (
		"SELECT bag.bouwjaar as year, energy_labels.pand_energieklasse as label, COUNT(*)"
		" FROM energy_labels, bag"
		" WHERE energy_labels.pand_bagverblijfsobjectid = bag.identificatie"
		" AND bag.bouwjaar IS NOT NULL"
		" GROUP BY year, label"
	)
	# returns:
	# [
	# (year, label, count),
	# (year, label, count),
	# ...
	# ]

	print("Executing building year query...")
	cursor.execute(building_year_query)
	print("Fetching results...")
	results = cursor.fetchall()
	print("Converting to DataFrame...")
	df = pd.DataFrame(results, columns=['year', 'label', 'count'])
	print("Pivoting DataFrame...")
	df = df.pivot_table(values='count', index='year', columns='label', fill_value=0)
	# Table now looks like:
	# year    A    A+    A++    A+++ ...
	# 1850  278    2     2      0    ...
	# ...
	#
	# pdb.set_trace()
	df = df.loc[(df.index >= 1850)]

	def convert_to_relative_values(df):
		df_relative = df.apply(lambda x: [val / sum(x) * 100 for val in x], axis=1, result_type='expand')
		df_relative.columns = df.columns
		return df_relative

	if relative:
		df = convert_to_relative_values(df)

	current_dir = os.path.dirname(os.path.realpath(__file__))
	filename = 'analyse_energy_labels_construction_year.csv'
	path = os.path.join(current_dir, filename)
	print('Writing to file...')
	df.to_csv(path)


def main():
	connection = get_connection()
	cursor = connection.cursor()
	energy_labels_per_building_year(cursor)


# TODO:
# check boundaries of energieprestatieindex:
# SELECT pand_energieklasse, MIN(pand_energieprestatieindex), MAX(pand_energieprestatieindex) FROM energy_labels WHERE pand_energieklasse IS NOT NULL AND pand_energieprestatieindex IS NOT NULL GROUP BY pand_energieklasse;
# it doesn't seem to be very useful, ranges are all over the place


# TODO:
# check internal correlation in a pand with multiple verblijfsobjecten.
# Helpful concept:
# Intraclass correlation: https://en.wikipedia.org/wiki/Intraclass_correlation
# In thise case, the buildings (panden) are the groups, and we see energy labels
# from dwellings inside that building as a measurement.
#
# To get these panden with multiple energy labels:
# SELECT pand_bagpandid FROM energy_labels GROUP BY pand_bagpandid HAVING COUNT(*) > 1
# And to select the labels in those panden:
# SELECT pand_bagpandid, pand_energieklasse FROM energy_labels WHERE pand_bagpandid IN (SELECT pand_bagpandid FROM energy_labels GROUP BY pand_bagpandid HAVING COUNT(*) > 1) AND pand_gebouwklasse = 'W';
#
# Final use case:
# Predict an energy_label (or a 95% range of energy_labels) based on other measured energy_labels
# in the same building.
#
# Related: doing this not for dwellings in the same building, but dwellings neighbouring each other, or within a certain radius of each other, or within the same block.
#
# Note: this might no be so useful since a majority of dwellings is in it's own building (5 133 559), see:
# SELECT pand_count, COUNT(pand_count) FROM (
# 	SELECT pand_id, COUNT(pand_id) as pand_count FROM bag GROUP BY pand_id
# ) s
# GROUP BY pand_count
# ORDER BY pand_count DESC

# Best wel wat dubbele verblijfsobjecten:
# SELECT pand_bagverblijfsobjectid, COUNT(pand_bagverblijfsobjectid) FROM energy_labels GROUP BY pand_bagverblijfsobjectid HAVING COUNT(pand_bagverblijfsobjectid) > 1
# Waarvan ook 19 met '0000000...'

if __name__ == '__main__':
	main()
