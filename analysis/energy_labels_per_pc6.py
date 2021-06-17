import os
import sys

import pandas as pd

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_utils import execute

energy_labels_per_pc6_query = '''
SELECT pc6_label_count, COUNT(pc6_label_count)
FROM

-- This subquery gets all pc6 with the label_count
(SELECT q.pc6, COALESCE(r.pc6_count, 0) as pc6_label_count
FROM
	-- Gets all pc6s with dwellings from BAG
	(SELECT pc6 FROM bag WHERE pc6 != '' GROUP BY pc6) q
-- JOINs them with the number of labels of that pc6
LEFT JOIN
	(SELECT pc6, COUNT(pc6) as pc6_count FROM energy_labels WHERE gebouwklasse = 'W' GROUP BY pc6 ) r
ON q.pc6 = r.pc6) s

GROUP BY pc6_label_count
ORDER BY pc6_label_count
'''

dwellings_per_pc6_query = '''
SELECT pc6_count, COUNT(pc6_count)
FROM
-- Gets all pc6s and their number of dwellings from the BAG
(SELECT pc6, COUNT(pc6) as pc6_count FROM bag WHERE pc6 != '' GROUP BY pc6) q
GROUP BY pc6_count
ORDER BY pc6_count
'''

def get_energy_labels_per_pc6():
	print('== Energy labels per pc6 ==')
	print('Executing, this might take a minute...')
	results = execute(energy_labels_per_pc6_query, fetch='all')
	print("Converting to dataframe...")
	df = pd.DataFrame(results, columns=['pc6_label_count', 'count'])

	current_dir = os.path.dirname(os.path.realpath(__file__))
	filename = 'energy_labels_per_pc6.csv'
	path = os.path.join(current_dir, filename)
	print('Writing to file...')
	df.to_csv(path, index=False)

def get_dwellings_per_pc6():
	print('== Dwellings per pc6 ==')
	print('Executing, this might take a minute...')
	results = execute(dwellings_per_pc6_query, fetch='all')
	print("Converting to dataframe...")
	df = pd.DataFrame(results, columns=['pc6_count', 'count'])

	current_dir = os.path.dirname(os.path.realpath(__file__))
	filename = 'dwellings_per_pc6.csv'
	path = os.path.join(current_dir, filename)
	print('Writing to file...')
	df.to_csv(path, index=False)

def main():
	get_energy_labels_per_pc6()
	get_dwellings_per_pc6()

if __name__ == '__main__':
	main()
