-- solution to load CSV from
-- https://stackoverflow.com/a/2987451/7770056

DROP TABLE energy_labels;

CREATE TABLE energy_labels
(
pand_opnamedatum date,
pand_opnametype varchar,
pand_status varchar,
pand_berekeningstype varchar,
pand_energieprestatieindex varchar,
pand_energieklasse varchar,
pand_energielabel_is_prive varchar,
pand_is_op_basis_van_referentie_gebouw varchar,
pand_gebouwklasse varchar,
meting_geldig_tot varchar,
pand_registratiedatum varchar,
pand_postcode varchar,
pand_huisnummer varchar,
pand_huisnummer_toev varchar,
pand_detailaanduiding varchar,
pand_bagverblijfsobjectid varchar,
pand_bagligplaatsid varchar,
pand_bagstandplaatsid varchar,
pand_bagpandid varchar,
pand_gebouwtype varchar,
pand_gebouwsubtype varchar,
pand_projectnaam varchar,
pand_projectobject varchar,
pand_SBIcode varchar,
pand_gebruiksoppervlakte varchar,
pand_energiebehoefte varchar,
pand_eis_energiebehoefte varchar,
pand_primaire_fossiele_energie varchar,
pand_eis_primaire_fossiele_energie varchar,
pand_primaire_fossiele_energie_EMG_forfaitair varchar,
pand_aandeel_hernieuwbare_energie varchar,
pand_eis_aandeel_hernieuwbare_energie varchar,
pand_aandeel_hernieuwbare_energie_EMG_forfaitair varchar,
pand_temperatuuroverschrijding varchar,
pand_eis_temperatuuroverschrijding varchar,
pand_warmtebehoefte varchar,
pand_forfaitaire varchar,
empty_column varchar -- the CSV file has a dangling ';' at every line
);

COPY energy_labels FROM '/Users/Rens/Dev/DutchDwellings/dutch-dwelling-database/data/EP-Online_v20210501_csv.csv' DELIMITER ';' CSV HEADER;

ALTER TABLE energy_labels
DROP COLUMN empty_column;
