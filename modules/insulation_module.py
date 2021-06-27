import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule

class InsulationModule(BaseModule):

	def process(self, dwelling):
		pass

	# Based on the WoON survey
	dwelling_type_multipliers = {
		"hoekwoning": 0.866707,
		"meergezinspand_hoog": 1.101116,
		"meergezinspand_laag_midden": 1.101116,
		"tussenwoning": 0.697829,
		"twee_onder_1_kap": 0.727686,
		"vrijstaand": 1.606662
	}

