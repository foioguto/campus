"""Regressões da primeira versão e compatibilidade da entrada legada."""
import sys
import unittest
from pathlib import Path
from datetime import date
from decimal import Decimal
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from etl import excel_value_to_text, validate


class LegacyTests(unittest.TestCase):
    def test_date(self):
        self.assertEqual(excel_value_to_text(date(2026, 1, 2)), '2026-01-02')

    def test_decimal(self):
        self.assertEqual(excel_value_to_text(Decimal('1234.50')), '1234.50')

    def test_duplicate_quant_ci(self):
        valid, rejected = validate(pd.DataFrame([{'quant_ci':'1'}, {'quant_ci':'1'}, {'quant_ci':'2'}]))
        self.assertEqual(len(valid), 2)
        self.assertEqual(len(rejected), 1)
