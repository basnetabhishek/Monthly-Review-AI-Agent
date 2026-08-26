export type ReportRow =
  | readonly [string, string, number, number]
  | readonly [string, string, number, number, number];

export type ReportData = {
  reportMonth: string;
  current: {
    sales: number;
    profit: number;
    margin: number;
    orders: number;
    units: number;
    negativeOrders: number;
    salesMom: number | null;
    profitMom: number | null;
    ordersMom: number | null;
  };
  trend: readonly { month: string; sales: number }[];
  markets: readonly ReportRow[];
  categories: readonly ReportRow[];
  targets: readonly ReportRow[];
  exceptions: readonly ReportRow[];
};

export const reportData: ReportData = {
  reportMonth: "2026-07",
  current: { sales: 503154, profit: 46916.52, margin: 9.324, orders: 1102, units: 7513, negativeOrders: 284, salesMom: -9.393, profitMom: -25.359, ordersMom: 1.848 },
  trend: [
    { month: "2026-04", sales: 480000 },
    { month: "2026-05", sales: 422785 },
    { month: "2026-06", sales: 555312 },
    { month: "2026-07", sales: 503154 },
  ],
  markets: [
    ["EU", "Central", 78767, 8617, 10.9], ["APAC", "Southeast Asia", 50119, 1340, 2.7], ["EMEA", "EMEA", 40016, 2537, 6.3], ["Africa", "Africa", 33809, 785, 2.3], ["APAC", "Oceania", 32944, 2112, 6.4], ["US", "West", 29676, 4179, 14.1]
  ],
  categories: [
    ["Technology", "Phones", 71892, 12904, 17.9], ["Furniture", "Chairs", 67821, 1998, 2.9], ["Technology", "Copiers", 57794, 8038, 13.9], ["Furniture", "Bookcases", 53922, 8446, 15.7], ["Office Supplies", "Appliances", 49301, 3544, 7.2], ["Office Supplies", "Storage", 35024, 2555, 7.3]
  ],
  targets: [
    ["APAC", "North Asia · Furniture", 3646, 12168, 30], ["Canada", "Canada · Office Supplies", 742, 2457, 30], ["APAC", "Oceania · Technology", 5692, 15173, 38], ["LATAM", "North · Technology", 4084, 8204, 50], ["US", "Central · Furniture", 6506, 11740, 55], ["LATAM", "South · Office Supplies", 3075, 5423, 57]
  ],
  exceptions: [
    ["US-2026-122714", "US · Central", 1890, -2929], ["TU-2026-6470", "EMEA · EMEA", 1667, -2053], ["US-2026-160591", "LATAM · South", 1326, -1743], ["ES-2026-1406762", "EU · Central", 1560, -1713], ["NI-2026-5830", "Africa · Africa", 724, -1472], ["IN-2026-30390", "APAC · Southeast Asia", 1363, -1141]
  ],
};

export function deterministicSummary(data: ReportData = reportData) {
  const c = data.current;
  const movement = c.salesMom == null
    ? "Month-over-month sales comparison is unavailable for this first reporting period"
    : `Sales ${c.salesMom >= 0 ? "increased" : "declined"} ${Math.abs(c.salesMom).toFixed(1)}% month over month to ${c.sales.toLocaleString()} source monetary units`;
  return `${movement}. The month delivered ${c.profit.toLocaleString(undefined, { maximumFractionDigits: 0 })} in reported profit, with a ${c.margin.toFixed(1)}% margin across ${c.orders.toLocaleString()} logical orders. Management attention should focus on the ${c.negativeOrders.toLocaleString()} orders that generated negative profit.`;
}
