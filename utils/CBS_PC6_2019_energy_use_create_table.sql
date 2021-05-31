-- use IF NOT EXISTS to make the statement idempotent
CREATE TABLE IF NOT EXISTS cbs_pc6_2019_energy_use
(
Postcode6 varchar,
Gemiddelde_aardgaslevering_woningen varchar,
Gemiddelde_aardgaslevering_woningen_gecorrigeerd int,
Gemiddelde_elektriciteitslevering_woningen int,
Gemiddelde_aardgaslevering_bedrijven  int,
Gemiddelde_elektriciteitslevering_bedrijven int
);
