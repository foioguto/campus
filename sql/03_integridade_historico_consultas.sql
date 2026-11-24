-- Migração incremental: não remove nem escolhe arbitrariamente registros antigos.
BEGIN;
LOCK TABLE staging.demandas IN SHARE ROW EXCLUSIVE MODE;
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM staging.demandas WHERE quant_ci IS NULL OR btrim(quant_ci) = '')
       OR EXISTS (SELECT 1 FROM staging.demandas GROUP BY ano_origem, quant_ci HAVING count(*) > 1)
    THEN RAISE EXCEPTION 'Staging contém chaves vazias ou duplicadas. Saneie os dados antes da migração.';
    END IF;
END $$;
ALTER TABLE staging.demandas ALTER COLUMN quant_ci SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS ux_demandas_ano_ci ON staging.demandas (ano_origem, quant_ci);
ALTER TABLE audit.cargas ADD COLUMN IF NOT EXISTS sha256 TEXT;
ALTER TABLE audit.cargas ADD COLUMN IF NOT EXISTS linhas_atualizadas INTEGER NOT NULL DEFAULT 0;
ALTER TABLE audit.cargas ADD COLUMN IF NOT EXISTS linhas_inalteradas INTEGER NOT NULL DEFAULT 0;
ALTER TABLE audit.cargas ADD COLUMN IF NOT EXISTS detalhes JSONB NOT NULL DEFAULT '{}';
CREATE TABLE IF NOT EXISTS audit.demandas_versoes (
    versao_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ano_origem SMALLINT NOT NULL,
    quant_ci TEXT NOT NULL,
    lote_id UUID NOT NULL,
    registrada_em TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    dados JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_versoes_chave ON audit.demandas_versoes (ano_origem, quant_ci, versao_id);
-- Registra o estado legado antes da primeira atualização pela nova aplicação.
INSERT INTO audit.demandas_versoes (ano_origem, quant_ci, lote_id, dados)
SELECT d.ano_origem, d.quant_ci, d.lote_id, to_jsonb(d)
FROM staging.demandas d
WHERE NOT EXISTS (SELECT 1 FROM audit.demandas_versoes v
                  WHERE v.ano_origem=d.ano_origem AND v.quant_ci=d.quant_ci);
CREATE OR REPLACE FUNCTION audit.registrar_versao_demanda() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO audit.demandas_versoes (ano_origem, quant_ci, lote_id, dados)
    VALUES (NEW.ano_origem, NEW.quant_ci, NEW.lote_id, to_jsonb(NEW));
    RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS demanda_versionada ON staging.demandas;
CREATE TRIGGER demanda_versionada AFTER INSERT OR UPDATE ON staging.demandas
FOR EACH ROW EXECUTE FUNCTION audit.registrar_versao_demanda();
CREATE SCHEMA IF NOT EXISTS mart;
CREATE OR REPLACE VIEW mart.projetos AS SELECT
    ano_origem, quant_ci, data_entrada, numero_ci, parecerista, setor,
    demandante, evento_iniciativa, demanda, pleito, posicao_referente_ao_pleito,
    previsto_pa, recurso_aprovado_a_ser_aplicado, contrapartida_apenas_valores,
    segmento, unidade_regional, diretoria_autorizante, observacao,
    processo_finalizado, data_entrega_para_ur, evento_ja_realizado_no_ultimo_ano,
    valor_recurso_aplicado_no_ultimo_ano, observacao_ultimo_ano,
    arquivo_origem, planilha_origem, linha_origem, lote_id, carregado_em
FROM staging.demandas;
CREATE OR REPLACE VIEW mart.resumo_anual AS
SELECT ano_origem, count(*) AS projetos,
       count(DISTINCT setor) AS setores, max(carregado_em) AS ultima_atualizacao
FROM mart.projetos GROUP BY ano_origem;
COMMIT;
