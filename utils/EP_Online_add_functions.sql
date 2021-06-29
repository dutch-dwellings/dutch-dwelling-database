CREATE OR REPLACE FUNCTION
	label_to_epi(label_class energy_label_class)
RETURNS
	real
LANGUAGE
	plpgsql
IMMUTABLE
AS
	$$
	BEGIN
		CASE label_class
			WHEN 'A+++++' THEN RETURN 0.281;
			WHEN 'A++++' THEN RETURN 0.281;
			WHEN 'A+++' THEN RETURN 0.281;
			WHEN 'A++' THEN RETURN 0.281;
			WHEN 'A+' THEN RETURN 0.635;
			WHEN 'A' THEN RETURN 0.938;
			WHEN 'B' THEN RETURN 1.200;
			WHEN 'C' THEN RETURN 1.451;
			WHEN 'D' THEN RETURN 1.785;
			WHEN 'E' THEN RETURN 2.184;
			WHEN 'F' THEN RETURN 2.612;
			WHEN 'G' THEN RETURN 3.237;
		END CASE;
	END
	$$
;

CREATE OR REPLACE FUNCTION
	impute_epi(label_class energy_label_class, energieprestatieindex double precision, berekeningstype text)
RETURNS
	real
LANGUAGE
	plpgsql
IMMUTABLE
AS
	$$
	BEGIN
		CASE berekeningstype
			WHEN 'EP' THEN RETURN energieprestatieindex;
			WHEN 'EPA' THEN RETURN energieprestatieindex;
			WHEN 'ISSO82.3, versie 3.0, oktober 2011' THEN RETURN energieprestatieindex;
			ELSE
				IF
					label_class IS NOT NULL THEN RETURN label_to_epi(label_class);
				ELSE
					-- This only happens with recent energy labels,
					-- it is a rare scenario ~150 labels), all having NTA-8800
					-- as a calculation type.
					RETURN NULL;
				END IF;
		END CASE;
	END
	$$
;
