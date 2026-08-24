import type { MonthOption } from "@/lib/analytics-types";

export function MonthPicker({
  months,
  value,
  onChange,
  disabled,
}: {
  months: MonthOption[];
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <label className="monthPicker">
      <span className="srOnly">Report month</span>
      <select
        aria-label="Report month"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
      >
        {months.map((option) => (
          <option value={option.value} key={option.value}>{option.label}</option>
        ))}
      </select>
    </label>
  );
}
