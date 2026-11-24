"""Consultas parametrizadas; toda conexão do painel é somente leitura."""
import pandas as pd
import psycopg
from psycopg import sql
from .presentation import LABELS


def query(dsn, statement, params=()):
    with psycopg.connect(dsn, connect_timeout=10) as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        conn.execute("SET LOCAL statement_timeout = '15s'")
        cursor = conn.execute(statement, params)
        return pd.DataFrame(cursor.fetchall(), columns=[c.name for c in cursor.description])


def _contains(value):
    return '%' + value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'


def _where(years, search='', filters=None):
    clauses = [sql.SQL('ano_origem = ANY(%s)')]
    params = [years]
    if search.strip():
        clauses.append(sql.SQL("concat_ws(' ', quant_ci, numero_ci, demandante, evento_iniciativa, demanda, setor) ILIKE %s"))
        params.append(_contains(search.strip()))
    for column, selected in (filters or {}).items():
        if column not in LABELS or column == 'ano_origem':
            raise ValueError('Coluna de filtro inválida.')
        field = sql.SQL("NULLIF(btrim({}), '')").format(sql.Identifier(column))
        if isinstance(selected, str):
            if selected.strip():
                clauses.append(sql.SQL('{} ILIKE %s').format(field))
                params.append(_contains(selected.strip()))
        elif selected:
            values = [v for v in selected if v is not None]
            alternatives = []
            if values:
                alternatives.append(sql.SQL('{} = ANY(%s)').format(field))
                params.append(values)
            if None in selected:
                alternatives.append(sql.SQL('{} IS NULL').format(field))
            clauses.append(sql.SQL('({})').format(sql.SQL(' OR ').join(alternatives)))
    return sql.SQL(' AND ').join(clauses), params


def projects(dsn, years, search='', limit=5000, filters=None):
    where, params = _where(years, search, filters)
    # Seleção explícita: nenhuma coluna técnica é exposta à consulta de projetos.
    statement = sql.SQL('SELECT {} FROM mart.projetos WHERE {} ORDER BY ano_origem DESC, quant_ci LIMIT %s').format(
        sql.SQL(', ').join(map(sql.Identifier, LABELS)), where)
    return query(dsn, statement, (*params, limit))


def project_count(dsn, years, search='', filters=None):
    where, params = _where(years, search, filters)
    return int(query(dsn, sql.SQL('SELECT count(*) AS total FROM mart.projetos WHERE {}').format(where), params).iloc[0]['total'])


def filter_options(dsn, years, column):
    if column not in LABELS or column == 'ano_origem':
        raise ValueError('Coluna de filtro inválida.')
    statement = sql.SQL("SELECT DISTINCT NULLIF(btrim({}), '') AS valor FROM mart.projetos WHERE ano_origem = ANY(%s) ORDER BY valor NULLS FIRST").format(sql.Identifier(column))
    return query(dsn, statement, (years,))['valor'].tolist()


def safe_csv(frame):
    """Evita que conteúdo de origem seja interpretado como fórmula no Excel."""
    result = frame.copy()
    for col in result.select_dtypes(include=['object', 'string']).columns:
        result[col] = result[col].map(lambda v: "'" + v if isinstance(v, str) and
                                     v.lstrip().startswith(('=', '+', '-', '@')) else v)
    return result.to_csv(index=False, sep=';').encode('utf-8-sig')
