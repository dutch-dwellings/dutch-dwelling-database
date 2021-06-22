import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule

class BaseBagDataModule(BaseModule):

	def get_bag_data(self, vbo_id):
		cursor = self.connection.cursor()
		# Get energy label of dwelling
		query = "SELECT oppervlakte, woningtype, bouwjaar FROM bag WHERE vbo_id = %s"
		cursor.execute(query, (vbo_id,))
		results = cursor.fetchone()
		return results
		cursor.close()

	def process(self, dwelling):
		continue_processing = super().process(dwelling)
		# Dwelling has already been processed by this module
		if not continue_processing:
			return

		vbo_id = dwelling.attributes['vbo_id']
		area = self.get_bag_data(vbo_id)[0]
		building_type = self.get_bag_data(vbo_id)[1]
		construction_year = self.get_bag_data(vbo_id)[2]
		dwelling.attributes['oppervlakte'] = area
		dwelling.attributes['woningtype'] = building_type
		dwelling.attributes['bouwjaar'] = construction_year
