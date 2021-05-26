import os
import sys
import random

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule

class DistrictHeatingModule(BaseModule):
	def __init__(self,connection):
		super().__init__(connection)

	#Load the RVO dataset into the module
	def load_data(self,connection):
		cursor = connection.cursor()
		query = "SELECT buurt_code, aantal_woningen, percentage_stadsverwarming FROM rvo_warmtenetten;"
		cursor.execute(query)
		global RVO_data
		RVO_data = cursor.fetchall()
		cursor.close()

	def process(self, dwelling):
		# First run the processing as defined by the
		# parent class.
		super().process(dwelling)

		#Obtain buurt_id associated with the dwelling
		buurt_id = dwelling.attributes['buurt_id']

		#Match buurt_id with RVO buurt_code and get percentage_stadsverwarming
		p_stads = 0
		for entry in RVO_data:
			if buurt_id in entry:
				p_stads = entry[2]

		#Convert percentage_stadsverwarming into boolean presence of DH
		if p_stads >= random.randint(0,99):
			DH = True
		else:
			DH = False

		#Assign district heating to dwelling
		dwelling.attributes['district_heating'] = DH
		outputs = {
		'district_heating': 'boolean'
		}
