from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
import hashlib
import pandas as pd
from .contract import ALIAS_TO_COLUMN, STAGING_COLUMNS, norm

def excel_value_to_text(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime().isoformat(sep=" ", timespec="seconds")
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        # Decimal(str()) evita serializar a aproximação binária do float.
        d = Decimal(str(value))
        return format(d, "f")
    if isinstance(value, Decimal):
        return format(value, "f")
    return str(value).strip() or None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_excel(path: Path, sheet: str, header_row: int) -> tuple[pd.DataFrame, list[str]]:
    raw = pd.read_excel(path, sheet_name=sheet, header=None, dtype=object, engine="openpyxl", keep_default_na=False)
    if header_row < 0 or header_row >= len(raw):
        raise ValueError("Linha de cabeçalho fora da planilha.")
    headers = raw.iloc[header_row].tolist()
    raw = raw.iloc[header_row + 1:].copy()
    raw.columns = headers
    # Filtrar sem converter o dtype: map/replace podem promover IDs inteiros a float.
    raw = raw.loc[raw.apply(lambda row: any(excel_value_to_text(v) is not None for v in row), axis=1)]
    mapped = {}
    unknown = []
    for col in raw.columns:
        key = norm(col)
        target = ALIAS_TO_COLUMN.get(key)
        if target:
            if target in mapped.values():
                raise ValueError(f"Mais de uma coluna do Excel foi mapeada para '{target}'.")
            mapped[col] = target
        else:
            unknown.append(str(col))
    if len(raw.columns) != len(set(raw.columns)):
        raise ValueError("Cabeçalhos repetidos; corrija a planilha antes da carga.")
    raw = raw.rename(columns=mapped)
    if "quant_ci" not in raw.columns:
        raise ValueError("Coluna obrigatória 'Quant. CI' não encontrada. Confira --header-row e os cabeçalhos.")
    for col in STAGING_COLUMNS:
        if col not in raw.columns:
            raw[col] = None
    missing = [c for c in STAGING_COLUMNS if c not in mapped.values()]
    raw = raw[STAGING_COLUMNS]
    # Linhas sem identificador não são carregadas, mas são reportadas como rejeitadas.
    converted = []
    for excel_index, row in raw.iterrows():
        item = {c: excel_value_to_text(row[c]) for c in STAGING_COLUMNS}
        # Índice do pandas é zero-based e corresponde à linha física do Excel menos 1.
        item["_linha_excel"] = int(excel_index) + 1
        converted.append(item)
    result = pd.DataFrame(converted, columns=STAGING_COLUMNS + ["_linha_excel"])
    result.attrs["missing_columns"] = missing
    return result, unknown


def validate(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    accepted = []
    rejected = []
    seen = set()
    for idx, row in df.iterrows():
        quant = row.get("quant_ci")
        excel_line = int(row.get("_linha_excel", int(idx) + 1))
        if quant is None or str(quant).strip() == "":
            rejected.append({"linha_excel": excel_line, "motivo": "Quant. CI vazio"})
            continue
        key = str(quant).strip()
        if key in seen:
            rejected.append({"linha_excel": excel_line, "motivo": f"Quant. CI duplicado no arquivo: {key}"})
            continue
        seen.add(key)
        accepted.append({c: row.get(c) for c in STAGING_COLUMNS} | {"_linha_excel": excel_line})
    return pd.DataFrame(accepted, columns=STAGING_COLUMNS + ["_linha_excel"]), rejected

