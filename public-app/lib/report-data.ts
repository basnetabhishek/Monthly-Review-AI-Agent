export const reportData = {
  reportMonth: "2014-12",
  current: { sales: 503154, profit: 46916.52, margin: 9.324, orders: 1102, units: 7513, negativeOrders: 284, salesMom: -9.393, profitMom: -25.359, ordersMom: 1.848 },
  trend: [
    { month: "2014-09", sales: 480000 },
    { month: "2014-10", sales: 422785 },
    { month: "2014-11", sales: 555312 },
    { month: "2014-12", sales: 503154 },
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
    ["US-2014-122714", "US · Central", 1890, -2929], ["TU-2014-6470", "EMEA · EMEA", 1667, -2053], ["US-2014-160591", "LATAM · South", 1326, -1743], ["ES-2014-1406762", "EU · Central", 1560, -1713], ["NI-2014-5830", "Africa · Africa", 724, -1472], ["IN-2014-30390", "APAC · Southeast Asia", 1363, -1141]
  ],
} as const;

export function deterministicSummary() {
  const c = reportData.current;
  return `Sales declined ${Math.abs(c.salesMom).toFixed(1)}% month over month to ${c.sales.toLocaleString()} source monetary units. The month remained profitable, with a ${c.margin.toFixed(1)}% margin across ${c.orders.toLocaleString()} logical orders. Management attention should focus on the ${c.negativeOrders} orders that generated negative profit.`;
}
