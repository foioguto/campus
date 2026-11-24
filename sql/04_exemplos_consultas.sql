-- Exemplos somente leitura para operadores e ferramentas de BI.
SELECT * FROM mart.resumo_anual ORDER BY ano_origem;

SELECT ano_origem, quant_ci, demandante, evento_iniciativa, setor, processo_finalizado
FROM mart.projetos
ORDER BY ano_origem DESC, quant_ci;

SELECT ano_origem, setor, count(*) AS projetos
FROM mart.projetos GROUP BY ano_origem, setor ORDER BY ano_origem, projetos DESC;

SELECT ano_origem, quant_ci, registrada_em, dados
FROM audit.demandas_versoes
WHERE ano_origem = 2026 AND quant_ci = '1'
ORDER BY versao_id;

-- Controle de reconciliação: esta consulta deve retornar zero linhas.
SELECT lote_id, linhas_lidas, linhas_carregadas, linhas_atualizadas, linhas_inalteradas
FROM audit.cargas
WHERE status = 'concluida'
  AND linhas_lidas <> linhas_carregadas + linhas_atualizadas + linhas_inalteradas;
