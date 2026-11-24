"""Persistência PostgreSQL: transações, concorrência e histórico no banco."""
import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
from .contract import STAGING_COLUMNS


class Repository:
    def __init__(self, dsn):
        self.dsn = dsn

    def start(self, batch, source):
        with psycopg.connect(self.dsn, connect_timeout=10) as conn:
            conn.execute('''INSERT INTO audit.cargas
                (lote_id, arquivo_origem, planilha_origem, ano_origem, status)
                VALUES (%s,%s,%s,%s,'iniciada')''',
                (batch, source.file.name, source.sheet, source.year))

    def fail(self, batch, error, report):
        with psycopg.connect(self.dsn, connect_timeout=10) as conn:
            # Não persistir mensagem de exceção que possa conter credenciais.
            conn.execute('''UPDATE audit.cargas SET status='falhou',
                finalizada_em=clock_timestamp(), mensagem_erro=%s, detalhes=%s,
                sha256=%s, linhas_lidas=%s, linhas_rejeitadas=%s WHERE lote_id=%s''',
                (type(error).__name__ + ': consulte detalhes da carga', Jsonb(report),
                 report.get('sha256'), report.get('linhas_com_dados'), report.get('linhas_rejeitadas'), batch))

    def load(self, batch, source, frame, report):
        counts = dict(linhas_carregadas=0, linhas_atualizadas=0, linhas_inalteradas=0)
        with psycopg.connect(self.dsn, connect_timeout=10) as conn:
            # Serializa as cargas do mesmo ano. Anos diferentes seguem independentes.
            conn.execute('SELECT pg_advisory_xact_lock(73512, %s)', (source.year,))
            columns = ['ano_origem', 'arquivo_origem', 'planilha_origem', 'linha_origem', 'lote_id'] + STAGING_COLUMNS
            assignments = sql.SQL(', ').join(
                sql.SQL('{}=EXCLUDED.{}').format(sql.Identifier(c), sql.Identifier(c))
                for c in columns if c not in ('ano_origem', 'quant_ci'))
            query = sql.SQL('''INSERT INTO staging.demandas ({}) VALUES ({})
                ON CONFLICT (ano_origem, quant_ci) DO UPDATE SET {},
                carregado_em=clock_timestamp()''').format(
                sql.SQL(',').join(map(sql.Identifier, columns)),
                sql.SQL(',').join(sql.Placeholder() for _ in columns), assignments)
            for row in frame.to_dict('records'):
                old = conn.execute(sql.SQL('SELECT {} FROM staging.demandas WHERE ano_origem=%s AND quant_ci=%s').format(
                    sql.SQL(',').join(map(sql.Identifier, STAGING_COLUMNS))), (source.year, row['quant_ci'])).fetchone()
                business = tuple(row[c] for c in STAGING_COLUMNS)
                if old == business:
                    counts['linhas_inalteradas'] += 1
                    continue
                values = (source.year, source.file.name, source.sheet, row['_linha_excel'], batch) + business
                conn.execute(query, values)
                counts['linhas_atualizadas' if old else 'linhas_carregadas'] += 1
            report.update(counts, status='concluida')
            conn.execute('''UPDATE audit.cargas SET finalizada_em=clock_timestamp(), status=%s,
                sha256=%s, linhas_lidas=%s, linhas_carregadas=%s, linhas_atualizadas=%s,
                linhas_inalteradas=%s, linhas_rejeitadas=%s, detalhes=%s WHERE lote_id=%s''',
                (report['status'], report['sha256'], report['linhas_com_dados'],
                 counts['linhas_carregadas'], counts['linhas_atualizadas'], counts['linhas_inalteradas'],
                 report['linhas_rejeitadas'], Jsonb(report), batch))
        return report
