from typing import Any
import re
import unicodedata

# Cabeçalhos aceitos: os nomes foram definidos a partir do dicionário informado.
# Acrescente aliases aqui se os títulos reais do Excel tiverem pequenas variações.
COLUMN_ALIASES = {
    "quant_ci": ["quant. ci", "quant ci", "quantidade ci", "quant_ci"],
    "data_entrada": ["data entrada", "data de entrada", "data_entrada"],
    "numero_ci": ["nº ci", "n° ci", "numero ci", "número ci", "nºci", "n°ci"],
    "parecerista": ["parecerista"],
    "setor": ["setor"],
    "demandante": ["demandante"],
    "evento_iniciativa": ["evento/iniciativa", "evento iniciativa", "evento", "iniciativa"],
    "demanda": ["demanda"],
    "pleito": ["pleito"],
    "posicao_referente_ao_pleito": [
        "posição referente ao pleito", "posicao referente ao pleito",
        "posição referente ao pleito (sim/não/parcialmente)"
    ],
    "previsto_pa": ["previsto pa (sim ou não)", "previsto pa"],
    "recurso_aprovado_a_ser_aplicado": [
        "recurso aprovado a ser aplicado", "recurso aprovado"
    ],
    "contrapartida_apenas_valores": [
        "contrapartida apenas valores", "contrapartida", "Contrapartida - APENAS VALORES"
    ],
    "segmento": ["segmento"],
    "unidade_regional": ["unidade regional", "unidade(s) regional(is)"],
    "diretoria_autorizante": ["diretoria autorizante"],
    "observacao": ["observação", "observacao"],
    "processo_finalizado": [
        "processo finalizado", "processo finalizado (concluído/pendente/adiado/cancelado)"
    ],
    "data_entrega_para_ur": ["data entrega para ur", "data de entrega para ur"],
    "evento_ja_realizado_no_ultimo_ano": [
        "evento já realizado no último ano?", "evento ja realizado no ultimo ano?", "Evento ja realizado no ultimo ano? (sim ou não)"
    ],
    "valor_recurso_aplicado_no_ultimo_ano": [
        "valor do recurso aplicado no último ano", "valor recurso aplicado no ultimo ano"
    ],
    "observacao_ultimo_ano": ["observação - último ano", "observacao ultimo ano"],
}

STAGING_COLUMNS = list(COLUMN_ALIASES.keys())

def norm(value: Any) -> str:
    s = unicodedata.normalize("NFKD", str(value or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("\n", " ").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[：:]", "", s)
    return s


ALIAS_TO_COLUMN = {
    norm(alias): col
    for col, aliases in COLUMN_ALIASES.items()
    for alias in aliases
}


