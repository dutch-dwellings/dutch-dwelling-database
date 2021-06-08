import os
import pprint
import sys

# Necessary to import modules from parent folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_utils import get_connection

cursor = get_connection().cursor()
pp = pprint.PrettyPrinter(indent=4)

# Note: alle 'W'-buildings have an assigned gebouwtype
energy_label_query = "SELECT pand_gebouwtype, pand_gebouwsubtype, COUNT(pand_gebouwtype) FROM energy_labels WHERE pand_gebouwklasse = 'W' GROUP BY pand_gebouwtype, pand_gebouwsubtype"
print("Querying energy labels...")
cursor.execute(energy_label_query)
energy_label_results = cursor.fetchall()
pp.pprint(energy_label_results)

bag_query = "SELECT woningtype, COUNT(woningtype) FROM bag GROUP BY woningtype"
print("\nQuerying BAG...")
cursor.execute(bag_query)
bag_results = cursor.fetchall()
pp.pprint(bag_results)

woon_query = "SELECT vormwo, vorm_eg5, vorm_mg2, SUM(ew_huis) from woon_2018_energie GROUP BY vormwo, vorm_eg5, vorm_mg2"
# WOoN:
# - vormwo (Type woning):
#	1: eengezins
#	2: meergezins
# - vorm_eg5 (Type eengezinswoning)
#	1: vrijstaande woning
#	2: 2 onder 1 kap
#	3: rijwoning hoek
#	4: rijwoning
# - vorm_mg2 (Type meergezinswoning)
#	1: appartement met 1 woonlaag
#	2: appartement met meerdere woonlagen
type_lookup = {
	('1', '1', None): 'eengezins vrijstaande woning',
	('1', '2', None): 'eengezins 2 onder 1 kap',
	('1', '3', None): 'eengezins rijwoning hoek',
	('1', '4', None): 'eengezins rijwoning',
	('2', None, '1'): 'meergezins appartement met 1 woonlaag',
	('2', None, '2'): 'meergezins appartement met meerdere woonlagen'
}
print("\nQuerying WoON...")
cursor.execute(woon_query)
woon_results = cursor.fetchall()
for vormwo, vorm_eg5, vorm_mg2, sum_huis in woon_results:
	print(f'{type_lookup[(vormwo, vorm_eg5, vorm_mg2)]}: {sum_huis}')
