import os
import sys

# Required for relative imports to also work when called
# from project root directory.
sys.path.append(os.path.dirname(__file__))
from base_module import BaseModule


class GasBoilerModule(BaseModule):

    def __init__(self, connection):
        super().__init__(connection)

        self.load_installation_type_data()
        self.load_gas_use_data()

    def load_installation_type_data(self):

        cursor = self.connection.cursor()
        # create dictionary with buurt_id and percentage of gas boilers
        query = "SELECT wijken_en_buurten, woningen FROM  cbs_84983ned_woningen_hoofdverwarmings_buurt_2019 WHERE wijken_en_buurten LIKE 'BU%' AND type_verwarmingsinstallatie LIKE 'A050112';"
        # A050112 is the code for a gas boiler
        cursor.execute(query)
        results = cursor.fetchall()
        self.buurten_verwarming_data = {
        buurt_id: percentage_gas_boilers
        for (buurt_id, percentage_gas_boilers)
        in results
        }
        print('self.buurten_verwarming_data created')
        cursor.close()

    def load_gas_use_data(self):
        # Create list of tuples with postal code, buurt_id, amount of dwellings in the postal code and the average gas use of the dwellings
        cursor = self.connection.cursor()
        query = "SELECT DISTINCT postcode, buurt_id,  gemiddelde_aardgaslevering_woningen FROM bag LEFT JOIN cbs_pc6_2019_energy_use ON postcode = postcode6  WHERE gemiddelde_aardgaslevering_woningen IS NOT null GROUP BY postcode, gemiddelde_aardgaslevering_woningen, buurt_id ORDER BY buurt_id, gemiddelde_aardgaslevering_woningen DESC;"
        # Possibly add: COUNT(bag.identificatie) AS aantal_woningen_in_postcode,

        cursor.execute(query)
        results = cursor.fetchall()
        self.postcode_gas_use_data = [x for x in results]
        '''
        # As dictionary
        self.postcode_gas_use_data = {
        postcode: (buurt_id, gas_use)
        for (postcode, buurt_id, gas_use)
        in results
        }
        '''
        print('self.postcode_gas_use_data created')
        cursor.close()

    def process(self, dwelling):
        super().process(dwelling)
        # Get base probability from percentage of dwellings with gas boiler in neighbourhood
        buurt_id = dwelling.attributes['buurt_id']
        boiler_p_base = self.buurten_verwarming_data.get(buurt_id, 0) / 100


        # Find average gas use of postal code of dwelling
        postcode = dwelling.attributes['postcode']
        postal_gas_use = [x[2] for x in self.postcode_gas_use_data if x[0] == postcode]
        if postal_gas_use == [] or postal_gas_use == [0]:
            boiler_p = boiler_p_base
        else:
            postal_gas_use = list(dict.fromkeys(postal_gas_use))
            postal_gas_use = postal_gas_use.pop()

            '''
            #as dictionary
            self.postcode_gas_use_data.get(postal_code, (0,0))[1]
            '''

            # Find maximum average gas use in neighbourhood
            gas_use_nbh = []
            gas_use_nbh.append([x[2] for x in self.postcode_gas_use_data if x[1] == buurt_id])
            max_gas_use_nbh = max(max(gas_use_nbh))

            # Calculate relative use of gas in nbh
            gas_use_fraction = round(postal_gas_use/max_gas_use_nbh,3)
            # Compare relative use to percentage of dwellings with a boiler
            if gas_use_fraction < (1-boiler_p_base):
                boiler_p = round(boiler_p_base * 0.1,2) #Find a way to nicely do this
            else:
                boiler_p = boiler_p_base
    outputs = {
    'boiler_p': 'double precision'
    }
