"""CLI com relatórios JSON e códigos de saída próprios para agendadores."""
import argparse
import json
import sys
from pathlib import Path
from .config import database_url
from .pipeline import Source, ingest


def main(argv=None):
    parser = argparse.ArgumentParser(description='Planilhas anuais → central de projetos')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file')
    group.add_argument('--manifest', type=Path)
    parser.add_argument('--year', type=int)
    parser.add_argument('--sheet')
    parser.add_argument('--header-row', type=int, default=1, help='Índice baseado em zero (padrão: 1)')
    parser.add_argument('--allow-missing-columns', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--dsn', help='Prefira DATABASE_URL para evitar credenciais no histórico do terminal')
    args = parser.parse_args(argv)
    try:
        if args.manifest:
            entries = json.loads(args.manifest.read_text(encoding='utf-8'))['sources']
            if not entries:
                raise ValueError('Manifesto vazio.')
            sources = [Source(file=(args.manifest.resolve().parent / e['file']).resolve(),
                              year=e['year'], sheet=e['sheet'], header_row=e.get('header_row', 1),
                              allow_missing_columns=e.get('allow_missing_columns', False)) for e in entries]
        else:
            if args.year is None or not args.sheet:
                parser.error('--file exige --year e --sheet')
            sources = [Source(Path(args.file), args.year, args.sheet, args.header_row, args.allow_missing_columns)]
        repository = None
        if not args.dry_run:
            from .repository import Repository
            repository = Repository(database_url(args.dsn))
        reports = []
        for source in sources:
            try:
                reports.append(ingest(source, repository))
            except Exception as exc:
                reports.append({'arquivo': source.file.name, 'status': 'falhou',
                                'tipo_erro': type(exc).__name__, 'erro': 'Não foi possível iniciar a auditoria.'})
        print(json.dumps(reports[0] if len(reports) == 1 else reports, ensure_ascii=False, indent=2))
        return 0 if all(r['status'] != 'falhou' for r in reports) else 2
    except Exception as exc:
        print(json.dumps({'status': 'falhou', 'tipo_erro': type(exc).__name__,
                          'erro': 'Confira o manifesto e a configuração de conexão.'}, ensure_ascii=False), file=sys.stderr)
        return 1
