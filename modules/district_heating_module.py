import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule

class DistrictHeatingModule(BaseModule):

	def process(self, dwelling):
		# First run the processing as defined by the
		# parent class.
		super().process(dwelling)

		dwelling.attributes['district_heating'] = False

	outputs = {
		'district_heating': 'boolean'
	}
