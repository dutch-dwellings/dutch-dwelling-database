# -*- coding: utf-8 -*-
"""
Created on Mon May 17 13:26:48 2021

@author: wesse
"""
#%%
import csv

def linear_search(array, to_find):
	for i in range(0, len(array)):
		if array[i] == to_find:
			return i
	return -1

#%%
BU_CODE_WARMTE = []
P_STADS = []

BAG_ID_LIST = []
BU_CODE_BAG = []

BAG_ID = []
index = []

with open(r'C:\Users\wesse\Documents\aaa Uni\Blok4\DataSets\Download-WarmteNetten-CSV.csv') as WarmteNet:
    CSVReader = csv.reader(WarmteNet,delimiter=';')
    next(CSVReader)
    for row in CSVReader:
        BU_CODE_WARMTE.append(row[0])
        P_STADS.append(row[4])

with open(r'C:\Users\wesse\Documents\aaa Uni\Blok4\DataSets\Databestanden\Databestanden\Invoer_RuimtelijkeData_BAG_vbo_woonfunctie_studiegebied_Export.csv') as BAG:
    CSVReader = csv.reader(BAG,delimiter=';')
    next(CSVReader)
    for row in CSVReader:
        BAG_ID_LIST.append(row[0])
        BU_CODE_BAG.append(row[11])
        
#%%
#BAG_ID = BAG_ID_LIST[0]
BAG_ID =	"'0344010000068357'"
indexBAG = BAG_ID_LIST.index(BAG_ID)
BU_CODE = BU_CODE_BAG[indexBAG]
BU_CODE = BU_CODE.strip('\'')

#Match BU_CODES
indexWarmte=linear_search(BU_CODE_WARMTE,BU_CODE)
print(indexWarmte)
if indexWarmte!=-1:
    P_DH=P_STADS[indexWarmte]
else: 
    P_DH=0
    
print(P_DH)
