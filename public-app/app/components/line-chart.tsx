import type { TrendPoint } from "@/lib/analytics-types";
import { formatReportMonth } from "@/lib/report-months";

const compact = (value: number) => new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(value);

export function LineChart({ points, metric = "sales" }: { points: TrendPoint[]; metric?: "sales" | "profit" }) {
  if (points.length < 2) return <div className="chartEmpty">Not enough periods to chart.</div>;
  const width = 920, height = 280, padding = 28;
  const values = points.map((point) => point[metric]);
  const min = Math.min(...values, 0), max = Math.max(...values), span = Math.max(max - min, 1);
  const coordinates = points.map((point, index) => ({
    x: padding + (index / Math.max(points.length - 1, 1)) * (width - padding * 2),
    y: padding + ((max - point[metric]) / span) * (height - padding * 2),
    point,
  }));
  const line = coordinates.map(({ x, y }) => `${x},${y}`).join(" ");
  const area = `${padding},${height - padding} ${line} ${width - padding},${height - padding}`;
  return (
    <div className="lineChart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${metric} trend from ${formatReportMonth(points[0].month)} to ${formatReportMonth(points.at(-1)!.month)}`}>
        <defs><linearGradient id={`${metric}Fill`} x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#116b51" stopOpacity=".22" /><stop offset="100%" stopColor="#116b51" stopOpacity="0" /></linearGradient></defs>
        {[0, 1, 2, 3].map((index) => <line key={index} x1={padding} x2={width - padding} y1={padding + index * 72} y2={padding + index * 72} className="gridLine" />)}
        <polygon points={area} fill={`url(#${metric}Fill)`} /><polyline points={line} className="trendLine" />
        {coordinates.map(({ x, y, point }, index) => <circle key={point.month} cx={x} cy={y} r={index === coordinates.length - 1 ? 6 : 3}><title>{formatReportMonth(point.month)}: {compact(point[metric])}</title></circle>)}
      </svg>
      <div className="chartAxis"><span>{formatReportMonth(points[0].month)}</span><span>{formatReportMonth(points.at(-1)!.month)}</span></div>
    </div>
  );
}
