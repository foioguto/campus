"""Vocabulário da interface; metadados técnicos não entram na consulta de negócio."""
LABELS = {
    'ano_origem': 'Ano', 'quant_ci': 'Identificador (CI)', 'data_entrada': 'Data de entrada',
    'numero_ci': 'Número da CI', 'parecerista': 'Parecerista', 'setor': 'Setor',
    'demandante': 'Demandante', 'evento_iniciativa': 'Projeto / evento', 'demanda': 'Demanda',
    'pleito': 'Tipo de apoio solicitado', 'posicao_referente_ao_pleito': 'Posição sobre o apoio',
    'previsto_pa': 'Previsto no plano anual',
    'recurso_aprovado_a_ser_aplicado': 'Recurso aprovado',
    'contrapartida_apenas_valores': 'Contrapartida', 'segmento': 'Segmento',
    'unidade_regional': 'Unidade regional', 'diretoria_autorizante': 'Diretoria autorizante',
    'observacao': 'Observações', 'processo_finalizado': 'Situação do processo',
    'data_entrega_para_ur': 'Data de entrega à unidade regional',
    'evento_ja_realizado_no_ultimo_ano': 'Realizado no ano anterior',
    'valor_recurso_aplicado_no_ultimo_ano': 'Recurso aplicado no ano anterior',
    'observacao_ultimo_ano': 'Observações do ano anterior',
}
DEFAULT_COLUMNS = ['ano_origem', 'quant_ci', 'evento_iniciativa', 'demandante',
                   'setor', 'unidade_regional', 'processo_finalizado']
CATEGORICAL = {'setor', 'parecerista', 'pleito', 'posicao_referente_ao_pleito',
               'previsto_pa', 'segmento', 'unidade_regional', 'diretoria_autorizante',
               'processo_finalizado', 'evento_ja_realizado_no_ultimo_ano'}


def visible_frame(frame, columns):
    return frame.loc[:, columns].rename(columns=LABELS)
