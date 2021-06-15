import bisect

def label_to_epi(label):
	'''
	Converts an energy label to the corresponding
	EP/EPA/ISSO82.3-type EPI
	(energieprestatieindex).
	Values are based on averages found within the
	EP-Online dataset, filtered on labels calculated
	with EP/EPA/ISSO82.3.
	'''
	averages = {
	"A+++++": 0.281, # actually the average for A++
	 "A++++": 0.281, # actually the average for A++
	  "A+++": 0.281, # actually the average for A++
	   "A++": 0.281,
	    "A+": 0.635,
	     "A": 0.938,
	     "B": 1.200,
	     "C": 1.451,
	     "D": 1.785,
	     "E": 2.184,
	     "F": 2.612,
	     "G": 3.237
	}
	return averages[label]

def epi_to_label(epi):
	'''
	Converts an EP/EPA/ISSO82.3-type EPI
	(energieprestatieindex) to the corresponding
	energy label.
	'''
	# Method adapted from https://stackoverflow.com/a/53138486/7770056.
	# Limits are inclusive maximums for the corresponding value,
	# e.g.
	#	0.5 --> A++ or higher
	#	0.51 -> A+.
	limits = [            0.5,  0.7, 1.05, 1.3, 1.6, 2.0, 2.4, 2.9     ]
	values = ['A++ or higher', 'A+',  'A', 'B', 'C', 'D', 'E', 'F', 'G']

	index = bisect.bisect_left(limits, epi)
	return values[index]
