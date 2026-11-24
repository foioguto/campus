"""Orquestração de um arquivo; independente da interface e do agendador."""
from dataclasses import dataclass
from pathlib import Path
import uuid
from .extract import extract_excel, validate, sha256_file


@dataclass(frozen=True)
class Source:
    file: Path
    year: int
    sheet: str
    header_row: int = 1
    allow_missing_columns: bool = False

    def __post_init__(self):
        if not 2000 <= self.year <= 2100 or self.header_row < 0 or not self.sheet.strip():
            raise ValueError('Ano, aba ou posição do cabeçalho inválidos.')


class QualityError(ValueError):
    pass


def ingest(source, repository=None):
    batch = str(uuid.uuid4())
    report = {'lote_id': batch, 'arquivo': source.file.name, 'ano_origem': source.year,
              'aba': source.sheet, 'modo': 'carga' if repository else 'dry-run'}
    if repository:
        repository.start(batch, source)
    try:
        digest = sha256_file(source.file)
        frame, unknown = extract_excel(source.file, source.sheet, source.header_row)
        valid, rejected = validate(frame)
        missing = frame.attrs.get('missing_columns', [])
        report.update(sha256=digest, linhas_com_dados=len(frame), linhas_validas=len(valid),
                      linhas_rejeitadas=len(rejected), rejeicoes=rejected,
                      colunas_nao_mapeadas=unknown, colunas_ausentes=missing)
        problems = []
        if unknown:
            problems.append('Há colunas não mapeadas.')
        if missing and not source.allow_missing_columns:
            problems.append('Há colunas esperadas ausentes.')
        if rejected:
            problems.append('Há linhas rejeitadas; corrija o arquivo para carregar o lote completo.')
        if valid.empty:
            problems.append('A planilha não contém registros válidos.')
        if digest != sha256_file(source.file):
            problems.append('O arquivo mudou durante a leitura. Execute novamente.')
        report['problemas'] = problems
        if problems:
            report['status'] = 'falhou'
            if repository:
                raise QualityError(' '.join(problems))
        elif repository:
            repository.load(batch, source, valid, report)
        else:
            report['status'] = 'validada'
        return report
    except Exception as error:
        report.update(status='falhou', tipo_erro=type(error).__name__)
        for counter in ('linhas_carregadas', 'linhas_atualizadas', 'linhas_inalteradas'):
            if counter in report:
                report[counter] = 0
        if isinstance(error, ValueError):
            report['motivo_validacao'] = str(error)
        if repository:
            try:
                repository.fail(batch, error, report)
            except Exception:
                report['falha_ao_registrar_auditoria'] = True
        # O relatório não contém DSN nem a mensagem bruta do driver.
        report.update(status='falhou', tipo_erro=type(error).__name__)
        if isinstance(error, (QualityError, FileNotFoundError)):
            report['erro'] = 'Arquivo ausente ou reprovado nas verificações de qualidade.'
        else:
            report['erro'] = 'Falha de leitura ou persistência; confira configuração, layout e acesso ao banco.'
        return report
