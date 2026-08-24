import importlib.util
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "notebooks" / "01_calculate_mvp_baseline.py"
SPEC = importlib.util.spec_from_file_location("mvp_baseline", MODULE_PATH)
BASELINE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BASELINE)


class MvpBaselineTests(unittest.TestCase):
    def test_fixture_values_match_recalculation(self):
        source = PROJECT_ROOT / "data" / "raw" / "Global Superstore.txt"
        fixture_path = PROJECT_ROOT / "tests" / "fixtures" / "expected_monthly_kpis.csv"
        self.assertTrue(source.exists(), "Source data is required for regression verification")
        self.assertTrue(fixture_path.exists(), "Generate the expected fixture first")

        actual = BASELINE.calculate_monthly_kpis(BASELINE.load_order_lines(source))
        expected = pd.read_csv(fixture_path, dtype={"report_month": "string"})
        selected = actual[actual["report_month"].isin(expected["report_month"])].copy()
        selected = selected.set_index("report_month").loc[expected["report_month"]].reset_index()

        count_columns = ["distinct_orders", "units_sold", "negative_profit_orders"]
        numeric_columns = [column for column in BASELINE.OUTPUT_COLUMNS if column not in {"report_month", *count_columns}]
        for column in count_columns:
            self.assertListEqual(selected[column].astype(int).tolist(), expected[column].astype(int).tolist())
        for column in numeric_columns:
            pd.testing.assert_series_equal(
                selected[column].astype(float).reset_index(drop=True),
                expected[column].astype(float).reset_index(drop=True),
                check_names=False,
                rtol=0,
                atol=0.000001,
            )

    def test_first_month_has_no_mom_comparison(self):
        source = PROJECT_ROOT / "data" / "raw" / "Global Superstore.txt"
        actual = BASELINE.calculate_monthly_kpis(BASELINE.load_order_lines(source))
        first = actual.iloc[0]
        self.assertEqual(first["report_month"], "2011-01")
        self.assertTrue(pd.isna(first["sales_mom_pct"]))
        self.assertTrue(pd.isna(first["profit_mom_pct"]))
        self.assertTrue(pd.isna(first["orders_mom_pct"]))


if __name__ == "__main__":
    unittest.main()
