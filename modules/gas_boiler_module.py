import os
import sys
from collections import defaultdict

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule


class GasBoilerModule(BaseModule):

	def __init__(self, connection):
		super().__init__(connection)
		self.load_cbs_neigh_heating_data()
		self.load_cbs_gas_use_data()
		self.load_bag_data()
		self.rank_postal_codes()

		# Amount of boilers in a buurt
	def load_cbs_neigh_heating_data(self):
		cursor = self.connection.cursor()
		query = "SELECT wijken_en_buurten, woningen FROM cbs_84983ned_woningen_hoofdverwarmings_buurt_2019 WHERE wijken_en_buurten LIKE 'BU%' AND type_verwarmingsinstallatie = 'A050112';"
		cursor.execute(query)
		results = cursor.fetchall()
		self.gas_boiler_data = {
			wijken_en_buurten: woningen
			for (wijken_en_buurten, woningen)
			in results
		}
		cursor.close()

		# Gas use per postal code
	def load_cbs_gas_use_data(self):
		cursor = self.connection.cursor()
		query = "SELECT Postcode6, Gemiddelde_aardgaslevering_woningen FROM cbs_pc6_2019_energy_use;"
		cursor.execute(query)
		results = cursor.fetchall()
		self.gas_use_data = {
			postcode: gas_use
			for (postcode, gas_use)
			in results
		}
		cursor.close()

		#Postcodes in a buurt
	def load_bag_data(self):
		cursor = self.connection.cursor()
		query = "SELECT DISTINCT buurt_id, postcode FROM bag ORDER BY buurt_id;"
		cursor.execute(query)
		results = cursor.fetchall()

		self.buurt_postcode_data = results

		'''
		self.buurt_postcode_data = defaultdict(list)
		for buurt_id, postcode in results:
			self.buurt_postcode_data[buurt_id].append(postcode)
		cursor.close()
		'''

		# Rank postal codes on gas use per buurt
	def rank_postal_codes(self):
		print('start ranking')
		# Make list of tuples into list
		buurt_postcode_list= [x for t in self.buurt_postcode_data for x in t]
		print('listified')
		# Remove duplicate buurten
		buurt_postcode_list = list(dict.fromkeys(buurt_postcode_list))
		print('removed duplicates')
		#Insert gas use data after corresponding postal code
	#	buurt_postcode_list=buurt_postcode_list[:1000]
		print(buurt_postcode_list)



		'''
		#propably not needed to insert all the gas uses
		for item in buurt_postcode_list:
			if item in self.gas_use_data:
				index = buurt_postcode_list.index(item) +1
				gas_use  = self.gas_use_data[item]
				buurt_postcode_list.insert(index,gas_use)
			else:
				pass
		print('Gas use inserted')
		'''
		# Turn list into list of lists


		# Sort sublists

	def process(self, dwelling):
		super().process(dwelling)
		# Kies percentage postcodes gelijk aan woningen als boilerhebbend

	outputs = {
		'boiler_p': 'double precision'
	}


# A050112 is the code for a gas boiler
