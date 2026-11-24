"""Filtros SQL e experiência de consulta, sem modificar nenhum banco."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from campus_etl.presentation import LABELS
from campus_etl.queries import _where, projects


class FilterTests(unittest.TestCase):
    def test_parameterization_null_and_literals(self):
        where, params = _where([2026], '10%_\\', {'setor': ['Tecnologia', None], 'demanda': "d'água"})
        statement = where.as_string()
        self.assertIn('IS NULL', statement)
        self.assertNotIn("d'água", statement)
        self.assertIn(['Tecnologia'], params)
        self.assertEqual(params[1], '%10\\%\\_\\\\%')
        self.assertEqual(params[-1], "%d'água%")
        with self.assertRaises(ValueError):
            _where([2026], filters={'lote_id': ['abc']})
        with patch('campus_etl.queries.query', return_value=pd.DataFrame()) as execute:
            projects('unused',[2026], filters={'setor':[None]})
            query = execute.call_args.args[1].as_string()
            self.assertNotIn('SELECT *',query)
            self.assertNotIn('lote_id',query)


class ConsultationTests(unittest.TestCase):
    def test_filters_visibility_empty_reset_and_details(self):
        from streamlit.testing.v1 import AppTest
        rows=[]
        for year, ci, sector, status in [(2025,'D1','Tecnologia','Concluído'),
                                       (2026,'D2','Cultura','Pendente'), (2026,'D3',None,'Concluído')]:
            r=dict.fromkeys(LABELS)
            r.update(ano_origem=year, quant_ci=ci, setor=sector, processo_finalizado=status,
                     evento_iniciativa='Projeto '+ci, demandante='Equipe', unidade_regional='Fortaleza')
            rows.append(r)
        frame=pd.DataFrame(rows)
        summary=pd.DataFrame({'ano_origem':[2026,2025], 'projetos':[2,1]})

        def filtered(dsn, years, search='', filters=None, **kw):
            f=frame[frame.ano_origem.isin(years)]
            if search: f=f[f.evento_iniciativa.str.contains(search,case=False,regex=False)]
            for c,v in (filters or {}).items():
                if isinstance(v,str) and v: f=f[f[c].fillna('').str.contains(v,case=False,regex=False)]
                elif v: f=f[f[c].isin(v)]
            return f.reset_index(drop=True)

        with patch('campus_etl.config.database_url',return_value='unused'), \
             patch('campus_etl.queries.query',return_value=summary), \
             patch('campus_etl.queries.projects',side_effect=filtered), \
             patch('campus_etl.queries.project_count',side_effect=lambda *a,**k:len(filtered(*a,**k))), \
             patch('campus_etl.queries.filter_options',side_effect=lambda d,y,c:frame[frame.ano_origem.isin(y)][c].drop_duplicates().tolist()):
            app=AppTest.from_file(str(ROOT/'src/painel.py')).run(timeout=20)
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            self.assertEqual(app.metric[0].value,'3')
            self.assertNotIn('lote_id',app.dataframe[0].value.columns)
            self.assertIn('Projeto / evento',app.dataframe[0].value.columns)
            self.assertEqual(len(app.tabs),0)
            app.multiselect(key='filter_values_setor').set_value(['Tecnologia']).run()
            self.assertEqual(app.metric[0].value,'1')
            app.multiselect(key='visible_columns').set_value(['quant_ci','setor']).run()
            self.assertEqual(list(app.dataframe[0].value.columns),['Identificador (CI)','Setor'])
            app.multiselect(key='filter_values_processo_finalizado').set_value(['Pendente']).run()
            self.assertEqual(app.metric[0].value,'0')
            next(b for b in app.button if b.label=='Limpar filtros').click().run()
            self.assertEqual(app.metric[0].value,'3')
            app.multiselect(key='filter_values_setor').set_value([None]).run()
            self.assertEqual(app.metric[0].value,'1')
            app.selectbox(key='detail_project').set_value((2026,'D3')).run()
            self.assertIn('Informação',app.dataframe[1].value.columns)
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
