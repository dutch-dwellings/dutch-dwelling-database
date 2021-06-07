import os
import sys

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database_utils import get_connection

# Use two-sided 95% percentile range
PERC_LOW  = 0.025
PERC_HIGH = 0.975

connection = get_connection()
cursor = connection.cursor()

# TODO:
# - region: everything (opt)
# - province: surface area (opt)
# - province: number of dwellings (opt)
# - PC4: everything
# - PC5: everything (opt)
# - streets: everything (opt)
# - perceel: number of dwellings
# - perceel: surface area
# - perceel: count
# - building: surface area


def get_ranges(query):
	'''
	Get statistical ranges (min, max, average, median, low-
	and high-percentiles) of a given query result.
	Assumption: the query needs to return a list of tuples
	with two values, and it needs to be sorted (ascending)
	on the second value.
	'''

	cursor.execute(query)
	results = cursor.fetchall()
	count = len(results)

	perc_low_i = round(count * PERC_LOW) - 1
	perc_median_i = round(count * 0.5) - 1
	perc_high_i = round(count * PERC_HIGH) - 1

	def average(lst):
		return sum(lst) / len(lst)

	# We use the fact that the returned results are sorted,
	# so we can simply use indices to determine min, max and percentiles
	minimum = results[0][1]
	avg = round(average([result[1] for result in results]))
	maximum = results[-1][1]
	perc_low = results[perc_low_i][1]
	median = results[perc_median_i][1]
	perc_high = results[perc_high_i][1]

	print(f"\n  count: {count}\n")

	print(f"    min: {minimum}")
	print(f"average: {avg}")
	print(f"    max: {maximum}\n")

	print(f"    low: {perc_low}")
	print(f" median: {median}")
	print(f"   high: {perc_high}\n")


run_includes = {
	'dwelling': True,
	'pand': True,
	'buurt': True,
	'postcode': True,
	'postcode4': True,
	'wijk': True,
	'woonplaats': True,
	'gemeente': True,
	'country': True
}


if run_includes['dwelling']:
	print("\nSurface area (m^2) per dwelling:")
	dwelling_surface_query = "SELECT pand_id, oppervlakte FROM bag ORDER BY oppervlakte"
	get_ranges(dwelling_surface_query)
	# Note that a lot of the higher surface areas don't make sense or are not correct.
	# Check with
	# SELECT * FROM bag ORDER BY oppervlakte DESC LIMIT 100
	# and then try to Streetview these buildings
	# (helpful tool to convert postal code to address: https://www.postnl.nl/adres-zoeken/)

if run_includes['pand']:
	print('\nDwellings without pand_id:')
	no_pand_id_count_query  = "SELECT COUNT(*) FROM bag WHERE (pand_id  = '') IS NOT FALSE"
	cursor.execute(no_pand_id_count_query)
	print(cursor.fetchall()[0][0])

	print("\nNumber of dwellings per pand_id:")
	dwelling_pand_count_query = "SELECT pand_id, COUNT(pand_id) FROM bag GROUP BY pand_id ORDER BY COUNT(pand_id)"
	get_ranges(dwelling_pand_count_query)
	# Extreme outlier at 17157 VBO's within a pand (next one has 987) is
	# pand_id: 0988100000297161
	# this pand spans multiple buurten!
	# Note that this is an error: this is a large area of non-related buildings around Weert.
	# The next number is ~900, and that is plausible since it is a large cluster of connected
	# flats. (Europaplein Utrecht)

	print("\nSurface area (m^2) per pand_id:")
	pand_surface_query = "SELECT pand_id, SUM(oppervlakte) FROM bag GROUP BY pand_id ORDER BY SUM(oppervlakte)"
	get_ranges(pand_surface_query)

if run_includes['buurt']:
	print('Dwellings without buurt_id:')
	no_buurt_id_count_query = "SELECT COUNT(*) FROM bag WHERE (buurt_id = '') IS NOT FALSE"
	cursor.execute(no_buurt_id_count_query)
	print(cursor.fetchall()[0][0])

	print("\nNumber of dwellings per buurt_id (BAG):")
	dwelling_buurt_count_query = "SELECT buurt_id, COUNT(buurt_id) FROM bag GROUP BY buurt_id ORDER BY COUNT(buurt_id)"
	get_ranges(dwelling_buurt_count_query)

	print("\nNumber of dwellings (technically: households) per buurt (CBS kerncijfers, filtered out buurten without dwellings):")
	dwelling_buurt_count_query_cbs = "SELECT codering, huishoudens_totaal FROM cbs_84799ned_kerncijfers_wijken_en_buurten_2020 WHERE codering LIKE 'BU%' AND huishoudens_totaal > 0 ORDER BY huishoudens_totaal"
	get_ranges(dwelling_buurt_count_query_cbs)

	print("\nNumber of postcode per buurt_id:")
	postcode_buurt_count_query = "SELECT buurt_id, count(buurt_id) FROM (SELECT buurt_id, postcode FROM bag GROUP BY buurt_id, postcode) sub GROUP BY buurt_id ORDER BY COUNT(buurt_id)"
	get_ranges(postcode_buurt_count_query)

	print("\nSurface area (ha) per buurt:")
	buurt_surface_query = "SELECT codering, oppervlakte_land FROM public.cbs_84799ned_kerncijfers_wijken_en_buurten_2020 WHERE codering LIKE 'BU%' ORDER BY oppervlakte_land"
	get_ranges(buurt_surface_query)


if run_includes['postcode']:
	print('\nDwellings without postcode:')
	no_postcode_count_query = "SELECT COUNT(*) FROM bag WHERE (postcode = '') IS NOT FALSE"
	cursor.execute(no_postcode_count_query)
	print(cursor.fetchall()[0][0])

	print("\nNumber of dwellings per postcode:")
	dwelling_postcode_count_query = "SELECT postcode, COUNT(postcode) FROM bag GROUP BY postcode ORDER BY COUNT(postcode)"
	get_ranges(dwelling_postcode_count_query)

if run_includes['postcode4']:
	print("\nNumber of dwellings per PC4:")
	dwelling_pc4_count_query = "SELECT SUBSTRING(postcode, 1, 4), COUNT(SUBSTRING(postcode, 1, 4)) FROM bag WHERE postcode != '' GROUP BY SUBSTRING(postcode, 1, 4) ORDER BY COUNT(SUBSTRING(postcode, 1, 4))"
	get_ranges(dwelling_pc4_count_query)


if run_includes['wijk']:
	print("\nNumber of dwellings (technically: households) per wijk (CBS kerncijfers, filtered out wijken without dwellings):")
	dwelling_wijk_count_query_cbs = "SELECT codering, huishoudens_totaal FROM cbs_84799ned_kerncijfers_wijken_en_buurten_2020 WHERE codering LIKE 'WK%' AND huishoudens_totaal > 0 ORDER BY huishoudens_totaal"
	get_ranges(dwelling_wijk_count_query_cbs)

	print("\nSurface area (ha) per wijk:")
	wijk_surface_query = "SELECT codering, oppervlakte_land FROM public.cbs_84799ned_kerncijfers_wijken_en_buurten_2020 WHERE codering LIKE 'WK%' ORDER BY oppervlakte_land"
	get_ranges(wijk_surface_query)


if run_includes['woonplaats']:
	print("Number of woonplaatsen:")
	woonplaatsen_count_query = "SELECT COUNT(*) FROM public.cbs_84734ned_woonplaatsen_in_nederland_2020"
	cursor.execute(woonplaatsen_count_query)
	print(cursor.fetchall()[0][0])


if run_includes['gemeente']:
	print("\nSurface area (ha) per gemeente:")
	gemeente_surface_query = "SELECT codering, oppervlakte_land FROM public.cbs_84799ned_kerncijfers_wijken_en_buurten_2020 WHERE codering LIKE 'GM%' ORDER BY oppervlakte_land"
	get_ranges(gemeente_surface_query)


if run_includes['country']:
	print("\nSurface area (ha) per NL:")
	country_surface_query = "SELECT codering, oppervlakte_land FROM public.cbs_84799ned_kerncijfers_wijken_en_buurten_2020 WHERE codering LIKE 'NL%' ORDER BY oppervlakte_land"
	get_ranges(country_surface_query)
