SELECT to_regclass('staging.demandas') AS tabela_staging,
       to_regclass('audit.cargas') AS tabela_auditoria;


SELECT table_schema, table_name, column_name, data_type
FROM information_schema.columns
WHERE (table_schema, table_name) IN (('staging','demandas'), ('audit','cargas'))
ORDER BY table_schema, table_name, ordinal_position;
