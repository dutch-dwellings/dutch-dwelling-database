-- use IF NOT EXISTS to make the statement idempotent
CREATE TABLE IF NOT EXISTS cbs_pc6_2019_energy_use
(
	pc6 character varying(6),
	gemiddelde_aardgaslevering_woningen int,
	gemiddelde_aardgaslevering_woningen_gecorrigeerd int,
	gemiddelde_elektriciteitslevering_woningen int,
	gemiddelde_aardgaslevering_bedrijven int,
	gemiddelde_elektriciteitslevering_bedrijven int
);
