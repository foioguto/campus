-- Data Mart de demandas/eventos
-- Etapa 1: schemas, staging e auditoria.
-- Todas as colunas de negócio da origem são TEXT na staging.
-- Não executar transformações nesta etapa.

BEGIN;

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dw;
CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE IF NOT EXISTS staging.demandas (
    staging_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- Metadados de rastreabilidade da carga
    ano_origem SMALLINT NOT NULL,
    arquivo_origem TEXT NOT NULL,
    planilha_origem TEXT,
    linha_origem INTEGER,
    lote_id UUID NOT NULL,
    carregado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Colunas de negócio: preservar como chegaram da planilha
    quant_ci TEXT,
    data_entrada TEXT,
    numero_ci TEXT,
    parecerista TEXT,
    setor TEXT,
    demandante TEXT,
    evento_iniciativa TEXT,
    demanda TEXT,
    pleito TEXT,
    posicao_referente_ao_pleito TEXT,
    previsto_pa TEXT,
    recurso_aprovado_a_ser_aplicado TEXT,
    contrapartida_apenas_valores TEXT,
    segmento TEXT,
    unidade_regional TEXT,
    diretoria_autorizante TEXT,
    observacao TEXT,
    processo_finalizado TEXT,
    data_entrega_para_ur TEXT,
    evento_ja_realizado_no_ultimo_ano TEXT,
    valor_recurso_aplicado_no_ultimo_ano TEXT,
    observacao_ultimo_ano TEXT
);

CREATE INDEX IF NOT EXISTS ix_staging_demandas_ano_ci
    ON staging.demandas (ano_origem, quant_ci);

CREATE INDEX IF NOT EXISTS ix_staging_demandas_lote
    ON staging.demandas (lote_id);

CREATE TABLE IF NOT EXISTS audit.cargas (
    lote_id UUID PRIMARY KEY,
    arquivo_origem TEXT NOT NULL,
    planilha_origem TEXT,
    ano_origem SMALLINT NOT NULL,
    iniciada_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finalizada_em TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'iniciada'
        CHECK (status IN ('iniciada', 'concluida', 'concluida_com_erros', 'falhou')),
    linhas_lidas INTEGER,
    linhas_carregadas INTEGER,
    linhas_rejeitadas INTEGER,
    mensagem_erro TEXT
);

COMMIT;

-- Verificação rápida após executar:
-- SELECT table_schema, table_name
-- FROM information_schema.tables
-- WHERE table_schema IN ('staging', 'dw', 'audit')
-- ORDER BY table_schema, table_name;
