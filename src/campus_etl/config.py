"""Configuração resolvida somente na execução; importar não abre conexões."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


def database_url(override=None, *, readonly=False):
    load_dotenv(ROOT / '.env')
    if override:
        return override
    if readonly and os.getenv('QUERY_DATABASE_URL'):
        return os.environ['QUERY_DATABASE_URL']
    if os.getenv('DATABASE_URL'):
        return os.environ['DATABASE_URL']
    required = ('DB_NAME', 'DB_USER', 'DB_PASSWORD')
    if not all(os.getenv(k) for k in required):
        raise ValueError('Configure DATABASE_URL ou DB_NAME, DB_USER e DB_PASSWORD.')
    from psycopg.conninfo import make_conninfo
    return make_conninfo(host=os.getenv('DB_HOST', 'localhost'),
                         port=os.getenv('DB_PORT', '5432'), dbname=os.environ['DB_NAME'],
                         user=os.environ['DB_USER'], password=os.environ['DB_PASSWORD'])
