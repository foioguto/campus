"""Entrada compatível com os comandos da primeira versão."""
from campus_etl.extract import excel_value_to_text, extract_excel, validate
from campus_etl.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
