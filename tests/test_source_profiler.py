import importlib.util
import tempfile
import unittest
from pathlib import Path

import pandas as pd


MODULE_PATH = Path(__file__).resolve().parents[1] / "notebooks" / "00_profile_source.py"
SPEC = importlib.util.spec_from_file_location("source_profiler", MODULE_PATH)
PROFILER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PROFILER)


class SourceProfilerTests(unittest.TestCase):
    def test_profile_detects_order_line_grain(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "sample.csv"
            pd.DataFrame(
                [
                    {"Row ID": 1, "Order ID": "A", "Order Date": "2024-01-01", "Ship Date": "2024-01-03", "Customer ID": "C1", "Customer Name": "One", "Product ID": "P1", "Sales": 100, "Profit": 20, "Quantity": 1, "Discount": 0, "Shipping Cost": 5},
                    {"Row ID": 2, "Order ID": "A", "Order Date": "2024-01-01", "Ship Date": "2024-01-03", "Customer ID": "C1", "Customer Name": "One", "Product ID": "P2", "Sales": 50, "Profit": -2, "Quantity": 2, "Discount": 0.1, "Shipping Cost": 3},
                    {"Row ID": 3, "Order ID": "B", "Order Date": "2024-02-02", "Ship Date": "2024-02-05", "Customer ID": "C2", "Customer Name": "Two", "Product ID": "P1", "Sales": 90, "Profit": 10, "Quantity": 1, "Discount": 0.1, "Shipping Cost": 4},
                ]
            ).to_csv(source, index=False)

            profile = PROFILER.build_profile(source)

            self.assertEqual(profile["schema"]["row_count"], 3)
            self.assertEqual(profile["grain"]["distinct_orders"], 2)
            self.assertEqual(profile["grain"]["orders_with_multiple_rows"], 1)
            self.assertTrue(profile["grain"]["row_id_unique"])
            self.assertEqual(profile["numeric_fields"]["profit"]["negative_rows"], 1)
            self.assertEqual(profile["dates"]["order_date"]["distinct_months"], 2)


if __name__ == "__main__":
    unittest.main()
