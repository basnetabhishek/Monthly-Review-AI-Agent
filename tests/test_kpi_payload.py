import unittest
from datetime import date
from decimal import Decimal

from pydantic import ValidationError

from backend.models.kpi_payload import KpiPayload
from backend.services.payload_builder import build_kpi_payload


def sample_results():
    executive = {
        "report_month": "2014-12-01",
        "reported_sales": "503154",
        "reported_profit": "46916.520680",
        "profit_margin_pct": "9.324485",
        "distinct_orders": 1102,
        "units_sold": 7513,
        "negative_profit_orders": 284,
        "negative_profit_amount": "-41627.492500",
        "sales_mom_pct": "-9.392558",
        "profit_mom_pct": "-25.359422",
        "orders_mom_pct": "1.848429",
        "prior_profit_margin_pct": "11.319148",
        "margin_change_points": "-1.994663",
    }
    trend = [{
        "report_month": "2014-12-01",
        "reported_sales": "503154",
        "reported_profit": "46916.520680",
        "profit_margin_pct": "9.324485",
        "distinct_orders": 1102,
        "units_sold": 7513,
    }]
    target = [{
        "market": "US",
        "region": "West",
        "category": "Technology",
        "actual_sales": "90000",
        "revenue_target": "100000",
        "revenue_attainment_pct": "90",
        "revenue_target_gap": "-10000",
        "actual_profit": "12000",
        "profit_target": "13000",
        "profit_attainment_pct": "92.307692",
        "actual_orders": 100,
        "orders_target": 105,
        "orders_attainment_pct": "95.238095",
        "is_synthetic": True,
        "target_method": "PRIOR_YEAR_PLUS_GROWTH",
    }]
    market = [{
        "market": "US",
        "region": "West",
        "reported_sales": "90000",
        "reported_profit": "12000",
        "profit_margin_pct": "13.333333",
        "distinct_orders": 100,
        "units_sold": 500,
    }]
    category = [{
        "category": "Technology",
        "sub_category": "Phones",
        "reported_sales": "60000",
        "reported_profit": "9000",
        "profit_margin_pct": "15",
        "distinct_orders": 70,
        "units_sold": 300,
    }]
    exception = [{
        "order_key": "abc",
        "order_id": "ORDER-1",
        "order_date": "2014-12-03",
        "market": "US",
        "region": "West",
        "order_reported_sales": "1000",
        "order_reported_profit": "-250",
        "order_units": 3,
        "order_shipping_cost": "40",
        "order_lines": 2,
    }]
    return {
        "executive_kpis": [executive],
        "monthly_trend": trend,
        "target_attainment": target,
        "market_performance": market,
        "category_performance": category,
        "negative_profit_exceptions": exception,
    }


class KpiPayloadTests(unittest.TestCase):
    def test_builds_strict_payload_and_material_flags(self):
        payload = build_kpi_payload(
            date(2014, 12, 1), sample_results(), data_snapshot="test-snapshot"
        )
        self.assertIsInstance(payload, KpiPayload)
        self.assertEqual(payload.executive.distinct_orders, 1102)
        self.assertEqual(payload.executive.reported_sales, Decimal("503154"))
        self.assertTrue(payload.target_attainment[0].is_synthetic)
        self.assertEqual(
            {change.flag_id for change in payload.material_changes},
            {"negative_order_share_high"},
        )

    def test_rejects_missing_query_result(self):
        results = sample_results()
        del results["category_performance"]
        with self.assertRaisesRegex(ValueError, "Missing controlled query"):
            build_kpi_payload(date(2014, 12, 1), results, data_snapshot="test")

    def test_rejects_nonnegative_exception(self):
        results = sample_results()
        results["negative_profit_exceptions"][0]["order_reported_profit"] = "1"
        with self.assertRaises(ValidationError):
            build_kpi_payload(date(2014, 12, 1), results, data_snapshot="test")

    def test_rejects_unmarked_target(self):
        results = sample_results()
        results["target_attainment"][0]["is_synthetic"] = False
        with self.assertRaises(ValidationError):
            build_kpi_payload(date(2014, 12, 1), results, data_snapshot="test")


if __name__ == "__main__":
    unittest.main()
