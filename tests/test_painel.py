"""Teste funcional da interface pelo runtime do Streamlit, sem navegador."""
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))


@unittest.skipUnless(os.getenv('TEST_DATABASE_URL') and importlib.util.find_spec('streamlit'),
                     'Exige Streamlit e TEST_DATABASE_URL descartável')
class PanelTests(unittest.TestCase):
    def test_search_years_and_history(self):
        import psycopg
        from streamlit.testing.v1 import AppTest
        from campus_etl.pipeline import Source, ingest
        from campus_etl.repository import Repository
        dsn = os.environ['TEST_DATABASE_URL']
        with psycopg.connect(dsn, autocommit=True) as conn:
            for name in ('01_schemas_staging_audit.sql', '03_integridade_historico_consultas.sql'):
                conn.execute((ROOT/'sql'/name).read_text())
            conn.execute('TRUNCATE staging.demandas, audit.cargas, audit.demandas_versoes RESTART IDENTITY')
        report = ingest(Source(ROOT/'data/dados_mockados_treinamento.xlsx',2026,'PARECER EXTERNO 2026'), Repository(dsn))
        self.assertEqual(report['status'],'concluida')
        with patch.dict(os.environ, {'QUERY_DATABASE_URL': dsn}):
            app = AppTest.from_file(str(ROOT/'src/painel.py')).run(timeout=20)
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            self.assertEqual(app.metric[0].value, '83')
            app.text_input(key='search_query').set_value('BUSCA_INEXISTENTE_987654').run()
            self.assertEqual(app.metric[0].value,'0')
            app.radio(key='area').set_value('Auditoria').run()
            app.text_input(key='project_ci').set_value('1').run()
            self.assertFalse(app.error, [e.value for e in app.error])
            self.assertTrue(len(app.json)>0, [i.value for i in app.info])
            self.assertFalse(app.exception)
            app.radio(key='area').set_value('Consultar projetos').run()
            app.multiselect(key='years').set_value([]).run()
            self.assertTrue(any('Selecione pelo menos um ano' in i.value for i in app.info))
            self.assertFalse(app.exception)
