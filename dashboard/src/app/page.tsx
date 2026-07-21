"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import StatCard from "@/components/StatCard";
import {
  Car,
  Users,
  Navigation,
  Star,
  TrendingUp,
  CheckCircle,
  XCircle,
  Zap,
  Clock,
} from "lucide-react";
import { api, type Stats, type Ride } from "@/lib/api";

export default function OverviewPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentRides, setRecentRides] = useState<Ride[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsData, ridesData] = await Promise.all([
          api.getStats(),
          api.getRides(undefined, 8),
        ]);
        setStats(statsData);
        setRecentRides(ridesData);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load dashboard data"
        );
      } finally {
        setLoading(false);
      }
    }
    fetchData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[60vh]">
          <div className="flex flex-col items-center gap-4">
            <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <p className="text-text-muted text-sm">Loading dashboard...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[60vh]">
          <div className="bg-danger-muted border border-danger/20 rounded-2xl p-8 max-w-md text-center">
            <XCircle size={40} className="text-danger mx-auto mb-3" />
            <h2 className="text-lg font-semibold mb-2">Connection Error</h2>
            <p className="text-sm text-text-muted mb-4">{error}</p>
            <p className="text-xs text-text-dim">
              Make sure the FastAPI server is running on port 8001
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!stats) return null;

  const statusColor: Record<string, string> = {
    COMPLETED: "text-success bg-success-muted",
    CANCELLED: "text-danger bg-danger-muted",
    ONGOING: "text-info bg-info-muted",
    ASSIGNED: "text-warning bg-warning-muted",
    REQUESTED: "text-primary bg-primary-muted",
    AWAITING_PAYMENT: "text-warning bg-warning-muted",
  };

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight">Dashboard Overview</h1>
        <p className="text-text-muted text-sm mt-1">
          Real-time platform metrics and recent activity
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total Drivers"
          value={stats.total_drivers}
          subtitle={`${stats.available_drivers} online now`}
          icon={Car}
          color="primary"
        />
        <StatCard
          title="Total Riders"
          value={stats.total_riders}
          icon={Users}
          color="info"
        />
        <StatCard
          title="Total Rides"
          value={stats.total_rides}
          subtitle={`${stats.active_rides} active`}
          icon={Navigation}
          color="success"
        />
        <StatCard
          title="Avg Rating"
          value={stats.avg_rating.toFixed(1)}
          subtitle={`${stats.completion_rate}% completion`}
          icon={Star}
          color="warning"
        />
      </div>

      {/* Second Row Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <StatCard
          title="Completed"
          value={stats.completed_rides}
          icon={CheckCircle}
          color="success"
        />
        <StatCard
          title="Cancelled"
          value={stats.cancelled_rides}
          icon={XCircle}
          color="danger"
        />
        <StatCard
          title="Completion Rate"
          value={`${stats.completion_rate}%`}
          icon={TrendingUp}
          color="primary"
        />
      </div>

      {/* Recent Rides Table */}
      <div className="bg-surface rounded-2xl border border-border overflow-hidden">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock size={16} className="text-text-dim" />
            <h2 className="text-sm font-semibold">Recent Rides</h2>
          </div>
          <span className="text-xs text-text-dim">
            Auto-refreshes every 30s
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-muted">
                <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                  ID
                </th>
                <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                  Rider
                </th>
                <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                  Driver
                </th>
                <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                  Status
                </th>
                <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                  Fare
                </th>
                <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                  Rating
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-muted">
              {recentRides.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-6 py-12 text-center text-text-dim"
                  >
                    <Navigation
                      size={32}
                      className="mx-auto mb-2 opacity-30"
                    />
                    <p>No rides yet</p>
                  </td>
                </tr>
              ) : (
                recentRides.map((ride) => (
                  <tr
                    key={ride.id}
                    className="hover:bg-surface-hover transition-colors"
                  >
                    <td className="px-6 py-3 font-mono text-text-muted">
                      #{ride.id}
                    </td>
                    <td className="px-6 py-3">
                      {ride.rider_name || `ID: ${ride.rider_id}`}
                    </td>
                    <td className="px-6 py-3 text-text-muted">
                      {ride.driver_name || "—"}
                    </td>
                    <td className="px-6 py-3">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          statusColor[ride.status] ||
                          "text-text-dim bg-surface-hover"
                        }`}
                      >
                        {ride.status}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-text-muted">
                      {ride.final_fare
                        ? `${ride.final_fare.toFixed(0)} ETB`
                        : ride.estimated_fare
                        ? `~${ride.estimated_fare.toFixed(0)} ETB`
                        : "—"}
                    </td>
                    <td className="px-6 py-3">
                      {ride.rating ? (
                        <span className="flex items-center gap-1 text-warning">
                          <Star size={12} fill="currentColor" />
                          {ride.rating}
                        </span>
                      ) : (
                        <span className="text-text-dim">—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </DashboardLayout>
  );
}
