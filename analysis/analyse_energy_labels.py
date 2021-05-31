import os
import sys
import pdb
import matplotlib.pyplot as plt

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis_utils import query_to_table
from utils.database_utils import get_connection

building_type_title = "Number of dwellings per building type (EP-Online)"
building_type_query = "SELECT pand_gebouwtype, COUNT(*) FROM energy_labels WHERE pand_gebouwklasse = 'W' GROUP BY pand_gebouwtype"

energy_label_title = "Number of dwellings per energy label (EP-Online)"
energy_label_query = "SELECT pand_energieklasse, COUNT(*) FROM energy_labels WHERE pand_gebouwklasse = 'W' GROUP BY pand_energieklasse"

# query_to_table(building_type_query, title=building_type_title, total=True)
# query_to_table(energy_label_query, title=energy_label_title, total=True)

inspection_year_title = "Number of energy label recordings per year"
inspection_year_query = "SELECT date_part('year', pand_opnamedatum), COUNT(*) FROM energy_labels WHERE pand_gebouwklasse = 'W' GROUP BY date_part('year', pand_opnamedatum)"

building_year_title = "Energy labels per building year"
# This takes a while
building_year_query = "SELECT bag.bouwjaar as year, energy_labels.pand_energieklasse as label, COUNT(*) FROM energy_labels, bag WHERE energy_labels.pand_bagverblijfsobjectid = bag.identificatie AND bag.bouwjaar IS NOT NULL AND bag.bouwjaar >= 1850 GROUP BY year, label"
# returns:
# [
# (year, label, count),
# (year, label, count),
# ...
# ]


energy_label_year_title = "Energy labels per recording year"
energy_label_year_query = "SELECT pand_energieklasse, COUNT(*) FROM energy_labels WHERE pand_gebouwklasse = 'W' AND date_part('year', pand_opnamedatum) = %s GROUP BY pand_energieklasse;"


connection = get_connection()
cursor = connection.cursor()
cursor.execute(building_year_query)
results = cursor.fetchall()

years = sorted(set([entry[0] for entry in results]))

results_dict = {}
defaults = {
	'A+++++': 0,
	'A++++': 0,
	'A+++': 0,
	'A++': 0,
	'A+': 0,
	'A': 0,
	'B': 0,
	'C': 0,
	'D': 0,
	'E': 0,
	'F': 0,
	'G': 0
}
for year in years:
	results_dict[year] = defaults.copy()
for entry in results:
	results_dict[entry[0]][entry[1]] = entry[2]

data = {
	key: [results_dict[year][key] for year in years] for key in defaults.keys()
}

relative = True
if relative == True:
	sums = {
		year: sum(results_dict[year].values()) for year in years
	}
	print(sums)
	data = {
		key: [results_dict[year][key] / sums[year] for year in years] for key in defaults.keys()
	}


A = [results_dict[year]['A'] for year in years]
B = [results_dict[year]['B'] for year in years]
C = [results_dict[year]['C'] for year in years]

# extracted from 'energielabel-voorbeeld-woningen.pdf'
colours = {
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

bottom = [0 for year in years]
for key in data.keys():
	print(bottom)
	print(data[key])
	plt.bar(years, data[key], bottom=bottom, color=colours[key], width=1.0)
	# need to increase the bottom offset by added data
	bottom = [sum(x) for x in zip(bottom, data[key])]

plt.show()


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
