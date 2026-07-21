import { type LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: "up" | "down" | "neutral";
  color: "primary" | "success" | "warning" | "danger" | "info";
}

const colorMap = {
  primary: {
    bg: "bg-primary-muted",
    text: "text-primary",
    border: "border-primary/20",
  },
  success: {
    bg: "bg-success-muted",
    text: "text-success",
    border: "border-success/20",
  },
  warning: {
    bg: "bg-warning-muted",
    text: "text-warning",
    border: "border-warning/20",
  },
  danger: {
    bg: "bg-danger-muted",
    text: "text-danger",
    border: "border-danger/20",
  },
  info: {
    bg: "bg-info-muted",
    text: "text-info",
    border: "border-info/20",
  },
};

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
}: StatCardProps) {
  const colors = colorMap[color];
  return (
    <div
      className={`bg-surface rounded-2xl border ${colors.border} p-5 hover:border-border transition-all duration-300 group`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-text-dim uppercase tracking-wider font-medium">
            {title}
          </p>
          <p className="text-3xl font-bold mt-2 tracking-tight">{value}</p>
          {subtitle && (
            <p className={`text-xs mt-1 ${colors.text}`}>{subtitle}</p>
          )}
        </div>
        <div
          className={`${colors.bg} p-3 rounded-xl group-hover:scale-110 transition-transform duration-300`}
        >
          <Icon size={20} className={colors.text} />
        </div>
      </div>
    </div>
  );
}
