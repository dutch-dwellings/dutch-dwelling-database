-- First make sure that the relevant functions are defined (impute_epi, label_to_epi).
-- Calculating the can take a minute or
ALTER TABLE energy_labels
ADD COLUMN IF NOT EXISTS
	epi_imputed real
GENERATED ALWAYS AS (impute_epi(energieklasse, energieprestatieindex, berekeningstype)) STORED
