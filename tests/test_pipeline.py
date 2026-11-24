import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import date
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import pandas as pd
from openpyxl import Workbook
from campus_etl.extract import extract_excel, excel_value_to_text
from campus_etl.pipeline import Source, ingest
from campus_etl.contract import COLUMN_ALIASES
from campus_etl.config import database_url
from campus_etl.queries import safe_csv

ROOT = Path(__file__).resolve().parents[1]


def workbook(path, rows, headers=None):
    book = Workbook()
    sheet = book.active
    sheet.title = 'Projetos'
    sheet.append(['Controle anual'])
    sheet.append(headers or [values[0] for values in COLUMN_ALIASES.values()])
    for row in rows:
        sheet.append(row)
    book.save(path)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'source.xlsx'

    def source(self, **kw):
        return Source(self.path, 2026, 'Projetos', **kw)

    def test_physical_line_blank_rows_and_na_preserved(self):
        workbook(self.path, [['001'], [None], ['NA'], [1]])
        frame, _ = extract_excel(self.path, 'Projetos', 1)
        self.assertEqual(frame.quant_ci.tolist(), ['001', 'NA', '1'])
        self.assertEqual(frame._linha_excel.tolist(), [3, 5, 6])

    def test_duplicate_headers_are_not_silently_renamed(self):
        workbook(self.path, [['a','b']], ['Quant. CI','Quant. CI'])
        with self.assertRaises(ValueError):
            extract_excel(self.path, 'Projetos', 1)

    def test_incomplete_layout_is_blocked_unless_explicit(self):
        workbook(self.path, [['a']], ['Quant. CI'])
        self.assertEqual(ingest(self.source())['status'], 'falhou')
        self.assertEqual(ingest(self.source(allow_missing_columns=True))['status'], 'validada')

    def test_rejected_rows_block_entire_batch(self):
        workbook(self.path, [['a'],['a']])
        result = ingest(self.source())
        self.assertEqual(result['status'], 'falhou')
        self.assertEqual(result['rejeicoes'][0]['linha_excel'], 4)

    def test_unknown_columns_block_load(self):
        workbook(self.path, [['a','b']], ['Quant. CI','Novo campo'])
        self.assertEqual(ingest(self.source(allow_missing_columns=True))['status'], 'falhou')

    def test_missing_file_and_empty_sheet(self):
        self.assertEqual(ingest(self.source())['tipo_erro'], 'FileNotFoundError')
        workbook(self.path, [])
        self.assertEqual(ingest(self.source())['status'], 'falhou')

    def test_types_and_csv_safety(self):
        self.assertEqual(excel_value_to_text(date(2026,1,2)), '2026-01-02')
        self.assertEqual(excel_value_to_text(Decimal('10.50')), '10.50')
        self.assertIn("'=SUM", safe_csv(pd.DataFrame({'x':['=SUM(A1)', 'normal']})).decode('utf-8-sig'))

    def test_config_does_not_interpolate_password_as_url(self):
        with patch('campus_etl.config.load_dotenv'), patch.dict(os.environ,
            {'DB_NAME':'db', 'DB_USER':'user', 'DB_PASSWORD':'a@b:c/!? ='}, clear=True):
            from psycopg.conninfo import conninfo_to_dict
            self.assertEqual(conninfo_to_dict(database_url())['password'], 'a@b:c/!? =')
        with patch('campus_etl.config.load_dotenv'), patch.dict(os.environ, {'DATABASE_URL':'chosen'}, clear=True):
            self.assertEqual(database_url(), 'chosen')
        with patch('campus_etl.config.load_dotenv'), patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                database_url()

    def test_real_sample(self):
        result = ingest(Source(ROOT/'data/dados_mockados_treinamento.xlsx',2026,'PARECER EXTERNO 2026'))
        self.assertEqual(result['status'], 'validada')
        self.assertEqual(result['linhas_validas'],83)


@unittest.skipUnless(os.getenv('TEST_DATABASE_URL'), 'Defina TEST_DATABASE_URL para um banco descartável')
class PostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        cls.dsn = os.environ['TEST_DATABASE_URL']
        with psycopg.connect(cls.dsn, autocommit=True) as conn:
            for migration in ('01_schemas_staging_audit.sql','03_integridade_historico_consultas.sql'):
                conn.execute((ROOT/'sql'/migration).read_text())

    def setUp(self):
        import psycopg
        from campus_etl.repository import Repository
        self.repo = Repository(self.dsn)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'test.xlsx'
        with psycopg.connect(self.dsn) as conn:
            conn.execute('TRUNCATE staging.demandas, audit.cargas, audit.demandas_versoes RESTART IDENTITY')

    def count(self, statement):
        import psycopg
        with psycopg.connect(self.dsn) as conn:
            return conn.execute(statement).fetchone()[0]

    def test_insert_replay_update_history_and_multiple_years(self):
        workbook(self.path, [['001',None,None,None,'Setor A']])
        source = Source(self.path,2026,'Projetos')
        self.assertEqual(ingest(source,self.repo)['linhas_carregadas'],1)
        self.assertEqual(ingest(source,self.repo)['linhas_inalteradas'],1)
        self.assertEqual(self.count('SELECT count(*) FROM audit.demandas_versoes'),1)
        workbook(self.path, [['001',None,None,None,'Setor B'],['002']])
        result = ingest(source,self.repo)
        self.assertEqual(result['linhas_atualizadas'],1)
        self.assertEqual(result['linhas_carregadas'],1)
        self.assertEqual(self.count('SELECT count(*) FROM audit.demandas_versoes'),3)
        ingest(Source(self.path,2025,'Projetos'),self.repo)
        self.assertEqual(self.count('SELECT count(*) FROM mart.projetos'),4)
        self.assertEqual(self.count('SELECT count(*) FROM mart.resumo_anual'),2)

    def test_failure_is_audited_and_staging_remains_intact(self):
        source = Source(self.path,2026,'Projetos')
        self.assertEqual(ingest(source,self.repo)['status'],'falhou')
        self.assertEqual(self.count("SELECT count(*) FROM audit.cargas WHERE status='falhou'"),1)
        workbook(self.path,[['1'],['1']])
        self.assertEqual(ingest(source,self.repo)['status'],'falhou')
        self.assertEqual(self.count('SELECT count(*) FROM staging.demandas'),0)

    def test_database_failure_rolls_back_data_and_history(self):
        import psycopg
        workbook(self.path,[['1'],['2']])
        with psycopg.connect(self.dsn) as conn:
            conn.execute("ALTER TABLE staging.demandas ADD CONSTRAINT test_failure CHECK (quant_ci <> '2')")
        try:
            self.assertEqual(ingest(Source(self.path,2026,'Projetos'),self.repo)['status'],'falhou')
            self.assertEqual(self.count('SELECT count(*) FROM staging.demandas'),0)
            self.assertEqual(self.count('SELECT count(*) FROM audit.demandas_versoes'),0)
            self.assertEqual(self.count("SELECT count(*) FROM audit.cargas WHERE status='falhou'"),1)
        finally:
            with psycopg.connect(self.dsn) as conn:
                conn.execute('ALTER TABLE staging.demandas DROP CONSTRAINT test_failure')

    def test_concurrent_replays_produce_one_version(self):
        from concurrent.futures import ThreadPoolExecutor
        workbook(self.path,[['1']])
        source=Source(self.path,2026,'Projetos')
        with ThreadPoolExecutor(max_workers=2) as executor:
            results=list(executor.map(lambda _: ingest(source,self.repo),range(2)))
        self.assertTrue(all(r['status']=='concluida' for r in results))
        self.assertEqual(self.count('SELECT count(*) FROM staging.demandas'),1)
        self.assertEqual(self.count('SELECT count(*) FROM audit.demandas_versoes'),1)


if __name__ == '__main__':
    unittest.main()
