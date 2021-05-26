import os
import sys
import random
import collections


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

		#Counter to control for max amount of DH connections
		global DH_counter
		DH_counter = collections.Counter()


	def process(self, dwelling):
		# First run the processing as defined by the
		# parent class.
		super().process(dwelling)

		#Obtain buurt_id associated with the dwelling
		buurt_id = dwelling.attributes['buurt_id']

		#Match buurt_id with RVO buurt_code and get percentage_stadsverwarming
		p_stads = 0
		aantal_woningen = 0
		for entry in RVO_data:
			if buurt_id in entry:
				aantal_woningen = entry[1]
				p_stads = entry[2]

		#Convert percentage_stadsverwarming into boolean presence of DH,
		#while also controlling for the maximum amount of possible connections

		if p_stads >= random.randint(0,99) and DH_counter[buurt_id] <= aantal_woningen * p_stads *0.01:
			DH = True
			DH_counter[buurt_id]+=1
		else:
			DH = False

		#Assign district heating to dwelling
		dwelling.attributes['district_heating'] = DH
		outputs = {
		'district_heating': 'boolean'
		}
