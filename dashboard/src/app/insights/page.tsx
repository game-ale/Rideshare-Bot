"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { Sparkles, Map, TrendingUp, AlertTriangle, Info, CheckCircle } from "lucide-react";
import { api, type Insight, type DemandForecast } from "@/lib/api";

export default function InsightsPage() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [demand, setDemand] = useState<DemandForecast | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [insightsData, demandData] = await Promise.all([
          api.getInsights(),
          api.getDemand(),
        ]);
        setInsights(insightsData);
        setDemand(demandData);
      } catch (err) {
        console.error("Failed to fetch AI data:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const insightColors: Record<string, string> = {
    positive: "bg-success-muted text-success border-success/20",
    neutral: "bg-info-muted text-info border-info/20",
    warning: "bg-warning-muted text-warning border-warning/20",
    action: "bg-primary-muted text-primary border-primary/20",
  };

  const insightIcons: Record<string, typeof CheckCircle> = {
    positive: CheckCircle,
    neutral: Info,
    warning: AlertTriangle,
    action: Sparkles,
  };

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <Sparkles className="text-primary" />
          AI Insights
        </h1>
        <p className="text-text-muted text-sm mt-1">
          Automated driver quality analysis and demand forecasting
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-[40vh]">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Driver Insights Column */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <TrendingUp size={18} className="text-text-dim" />
              Driver Quality Insights
            </h2>
            
            {insights.length === 0 ? (
              <div className="bg-surface rounded-2xl border border-border p-8 text-center text-text-dim">
                <p className="text-sm">No insights available right now.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {insights.map((insight, idx) => {
                  const colorClass = insightColors[insight.type] || insightColors.neutral;
                  const Icon = insightIcons[insight.type] || Info;
                  return (
                    <div
                      key={idx}
                      className={`rounded-2xl border p-4 ${colorClass} bg-opacity-30 backdrop-blur-sm`}
                    >
                      <div className="flex items-start gap-3">
                        <div className="mt-0.5 bg-background/50 p-2 rounded-lg">
                          <Icon size={16} />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <h3 className="font-semibold text-sm">{insight.title}</h3>
                            <span className="text-xs font-mono opacity-70">
                              {insight.driver_name} (ID: {insight.driver_id})
                            </span>
                          </div>
                          <p className="text-sm opacity-90">{insight.detail}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Demand Forecasting Column */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Map size={18} className="text-text-dim" />
              Demand Forecasting
            </h2>
            
            {demand ? (
              <div className="space-y-4">
                {/* Recommendation Card */}
                <div className="bg-surface rounded-2xl border border-primary/30 p-5 relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-4 opacity-10">
                    <Sparkles size={64} className="text-primary" />
                  </div>
                  <h3 className="text-xs text-text-dim uppercase tracking-wider mb-2">AI Recommendation</h3>
                  <p className="text-lg font-medium leading-tight relative z-10">
                    {demand.recommendation}
                  </p>
                </div>

                {/* Hotspots */}
                <div className="bg-surface rounded-2xl border border-border p-5">
                  <h3 className="text-sm font-semibold mb-4">Current Hotspots</h3>
                  <div className="space-y-3">
                    {demand.hotspots.map((spot, idx) => (
                      <div key={idx} className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium">{spot.area}</p>
                          <p className="text-xs text-text-dim">
                            {spot.lat}, {spot.lng}
                          </p>
                        </div>
                        <div className="text-right">
                          <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${
                            spot.demand === "HIGH" ? "bg-danger-muted text-danger" :
                            spot.demand === "MEDIUM" ? "bg-warning-muted text-warning" :
                            "bg-success-muted text-success"
                          }`}>
                            {spot.demand} DEMAND
                          </span>
                          <p className="text-xs text-text-dim mt-1">
                            Need ~{spot.drivers_needed} drivers
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Peak Prediction */}
                <div className="bg-surface rounded-2xl border border-border p-5 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold">Predicted Peak</h3>
                    <p className="text-xs text-text-dim">Highest volume today</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-primary">{demand.peak_prediction.hour}</p>
                    <p className="text-sm text-text-muted">{demand.peak_prediction.predicted_rides} rides/hr</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-surface rounded-2xl border border-border p-8 text-center text-text-dim">
                <p className="text-sm">Forecast data unavailable.</p>
              </div>
            )}
          </div>
          
        </div>
      )}
    </DashboardLayout>
  );
}
