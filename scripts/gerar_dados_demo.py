"""Gera planilhas fictícias determinísticas; não conecta ao banco.

Execute na raiz do projeto: python scripts/gerar_dados_demo.py
Depois: campus-etl --manifest config/sources.demo.json --dry-run
"""
import json
import sys
from datetime import date
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from campus_etl.contract import COLUMN_ALIASES

SCENARIOS = [
    ('Tecnologia', 'Equipe Aurora', 'Oficina de Python', 'Capacitação em análise de dados', 'Formação', 'Fortaleza'),
    ('Cultura', 'Coletivo Horizonte', 'Mostra de Cinema', 'Exibição de produções independentes', 'Audiovisual', 'Sobral'),
    ('Educação', 'Instituto Semente', 'Feira de Ciências', 'Divulgação de projetos de estudantes', 'Ciência', 'Cariri'),
    ('Sustentabilidade', 'Associação Veredas', 'Jornada de Reciclagem', 'Oficinas de reaproveitamento de materiais', 'Meio ambiente', 'Iguatu'),
    ('Comunicação', 'Núcleo Farol', 'Encontro de Comunicação', 'Formação de comunicadores locais', 'Comunicação', 'Fortaleza'),
    ('Esporte', 'Projeto Movimento', 'Circuito de Atletismo', 'Promoção de atividades esportivas', 'Esporte', 'Sobral'),
    ('Inovação', 'Laboratório Ponte', 'Hackathon de Dados', 'Soluções de dados para desafios locais', 'Tecnologia', 'Cariri'),
    ('Saúde', 'Rede Bem Viver', 'Semana de Qualidade de Vida', 'Atividades educativas de bem-estar', 'Saúde', 'Iguatu'),
]


def main():
    directory = ROOT / 'data' / 'demo'
    directory.mkdir(parents=True, exist_ok=True)
    sources = []
    for year, count in ((2022, 8), (2023, 12), (2024, 16), (2025, 20)):
        book = Workbook()
        sheet = book.active
        sheet.title = f'PROJETOS DEMO {year}'
        sheet.append([f'DADOS FICTÍCIOS PARA TESTES MANUAIS — {year}'])
        sheet.append([aliases[0] for aliases in COLUMN_ALIASES.values()])
        for index in range(count):
            sector, requester, event, demand, segment, region = SCENARIOS[index % len(SCENARIOS)]
            number = index + 1
            record = {
                'quant_ci': f'DEMO-{number:03d}',
                'data_entrada': date(year, (index % 12) + 1, 5),
                'numero_ci': f'DEMO-CI-{year}-{number:03d}',
                'parecerista': ['Pessoa Alfa (fictícia)', 'Pessoa Beta (fictícia)', 'Pessoa Gama (fictícia)'][index % 3],
                'setor': sector,
                'demandante': f'DEMO — {requester}',
                'evento_iniciativa': f'DEMO — {event} {year} / edição {index // 8 + 1}',
                'demanda': demand,
                'pleito': ['Apoio financeiro', 'Apoio institucional', 'Cessão de espaço'][index % 3],
                'posicao_referente_ao_pleito': ['Sim', 'Parcialmente', 'Não'][index % 3],
                'previsto_pa': 'Sim' if index % 2 == 0 else 'Não',
                'recurso_aprovado_a_ser_aplicado': str(0 if index % 3 == 2 else 1500 + 250 * number),
                'contrapartida_apenas_valores': str(100 * number),
                'segmento': segment,
                'unidade_regional': region if index % 4 else f'{region}; Cariri',
                'diretoria_autorizante': ['Diretoria Administrativa', 'Diretoria de Projetos'][index % 2],
                'observacao': 'DADO FICTÍCIO — cenário de teste manual; não representa projeto real.',
                'processo_finalizado': ['Concluído', 'Pendente', 'Adiado', 'Cancelado'][index % 4],
                'data_entrega_para_ur': date(year, (index % 12) + 1, 20) if index % 4 == 0 else None,
                'evento_ja_realizado_no_ultimo_ano': 'Sim' if index % 2 else 'Não',
                'valor_recurso_aplicado_no_ultimo_ano': '1000' if index % 2 else '0',
                'observacao_ultimo_ano': 'Histórico ilustrativo, também fictício.',
            }
            sheet.append([record[column] for column in COLUMN_ALIASES])
        sheet.freeze_panes = 'A3'
        sheet.auto_filter.ref = f'A2:V{count + 2}'
        path = directory / f'projetos_demo_{year}.xlsx'
        book.save(path)
        sources.append({'file': f'../data/demo/{path.name}', 'year': year, 'sheet': sheet.title, 'header_row': 1})
        print(f'{year}: {count} projetos → {path.relative_to(ROOT)}')
    (ROOT / 'config' / 'sources.demo.json').write_text(json.dumps({'sources': sources}, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
