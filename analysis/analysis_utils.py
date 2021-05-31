import os
import sys

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_utils import get_connection

def print_results(results, title=None, total=False, latex=False):
	'''
	Print a nice table from the query results.
	Assumptions: results is a list with tuples with two entries.
	If you want to include the total, the second column has to be
	summable.
	'''

	print("")

	if latex:
		column_sep = " & "
		line_ending = " \\\\\n"
	else:
		column_sep = "  "
		line_ending = "\n"

	if latex:
		print(r"\begin{center}")
		print(r"\begin{tabular}{ l r }")

	def number_str(number):
		# We want a space as a thousands seperator,
		# but that is not possible directly.
		return '{:,}'.format(number).replace(',', ' ')

	max_len = [
		max([len(str(row[0])) for row in results]),
		max([len(number_str(row[1])) for row in results])
	]

	if title:
		padding_n = max(0, max_len[0] - (len(title) - len(column_sep)) // 2)
		if latex:
			print(r"\bf")
		print(f'{" " * padding_n}{title}', end=line_ending)
		if latex:
			print(r"\hline")
		else:
			print(f'{" " * padding_n}{"=" * len(title)}', end=line_ending)

		max_len[0] = max(max_len[0], (len(title) - len(column_sep)) // 2)

	if total:
		sum_total = sum([row[1] for row in results])
		max_len = [
			max(max_len[0], len('Total')),
			max(max_len[1], len(number_str(sum_total)))
		]

	for row in results:
		print(f'{str(row[0]):>{max_len[0]}}{column_sep}{number_str(row[1]):>{max_len[1]}}', end=line_ending)

	if total:
		if latex:
			print(r"\hline \bf")
		else:
			print(f'{"-" * len("Total"):>{max_len[0]}}{column_sep}{"-" * len(number_str(sum_total))}', end=line_ending)
		print(f'{"Total":>{max_len[0]}}{column_sep}{number_str(sum_total):>{max_len[1]}}', end=line_ending)

	if latex:
		print(r"\end{tabular}")
		print(r"\end{center}")

def query_to_table(query, title=None, total=False, latex=False):
	connection = get_connection()
	cursor = connection.cursor()
	cursor.execute(query)
	results = cursor.fetchall()
	print_results(results, title=title, total=total, latex=latex)
