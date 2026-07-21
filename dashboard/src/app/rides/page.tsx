"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import {
  Navigation,
  Star,
  MapPin,
  CreditCard,
  Filter,
  ArrowUpDown,
} from "lucide-react";
import { api, type Ride } from "@/lib/api";

export default function RidesPage() {
  const [rides, setRides] = useState<Ride[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("ALL");

  const fetchRides = async () => {
    try {
      const status = filter === "ALL" ? undefined : filter;
      const data = await api.getRides(status, 100);
      setRides(data);
    } catch (err) {
      console.error("Failed to fetch rides:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchRides();
  }, [filter]);

  const statusColor: Record<string, string> = {
    COMPLETED: "text-success bg-success-muted",
    CANCELLED: "text-danger bg-danger-muted",
    ONGOING: "text-info bg-info-muted",
    ASSIGNED: "text-warning bg-warning-muted",
    REQUESTED: "text-primary bg-primary-muted",
    AWAITING_PAYMENT: "text-warning bg-warning-muted",
  };

  const filters = ["ALL", "COMPLETED", "CANCELLED"];

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Rides</h1>
          <p className="text-text-muted text-sm mt-1">
            View and filter ride history across the platform
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <Filter size={14} className="text-text-dim" />
          {filters.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all duration-200 ${
                filter === f
                  ? "bg-primary text-white shadow-sm shadow-primary/20"
                  : "bg-surface-hover text-text-muted hover:text-text"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-[40vh]">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : rides.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-[40vh] text-text-dim">
          <Navigation size={48} className="mb-3 opacity-30" />
          <p className="text-sm">No rides found</p>
          <p className="text-xs mt-1">
            {filter !== "ALL"
              ? `No ${filter.toLowerCase()} rides`
              : "Rides will appear after being created via the Telegram bot"}
          </p>
        </div>
      ) : (
        <div className="bg-surface rounded-2xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-muted">
                  <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                    <span className="flex items-center gap-1">
                      ID <ArrowUpDown size={10} />
                    </span>
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
                    Route
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                    Fare
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                    Payment
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                    Rating
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-muted">
                {rides.map((ride) => (
                  <tr
                    key={ride.id}
                    className="hover:bg-surface-hover transition-colors"
                  >
                    <td className="px-6 py-3 font-mono text-text-muted">
                      #{ride.id}
                    </td>
                    <td className="px-6 py-3">
                      <p className="font-medium text-sm">
                        {ride.rider_name || `ID: ${ride.rider_id}`}
                      </p>
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
                    <td className="px-6 py-3">
                      <div className="flex items-center gap-1.5 text-xs text-text-muted">
                        <MapPin size={12} className="text-success shrink-0" />
                        <span>
                          {ride.rider_lat.toFixed(3)},{ride.rider_lng.toFixed(3)}
                        </span>
                        {ride.dest_lat && (
                          <>
                            <span className="text-text-dim">→</span>
                            <MapPin
                              size={12}
                              className="text-danger shrink-0"
                            />
                            <span>
                              {ride.dest_lat.toFixed(3)},
                              {ride.dest_lng?.toFixed(3)}
                            </span>
                          </>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-3 text-text-muted">
                      {ride.final_fare ? (
                        <span className="font-semibold text-text">
                          {ride.final_fare.toFixed(0)} ETB
                        </span>
                      ) : ride.estimated_fare ? (
                        <span className="text-text-dim">
                          ~{ride.estimated_fare.toFixed(0)} ETB
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-6 py-3">
                      {ride.payment_method ? (
                        <span className="flex items-center gap-1 text-xs text-text-muted">
                          <CreditCard size={12} className="text-text-dim" />
                          {ride.payment_method}
                        </span>
                      ) : (
                        <span className="text-text-dim">—</span>
                      )}
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
                    <td className="px-6 py-3 text-xs text-text-dim whitespace-nowrap">
                      {ride.created_at
                        ? new Date(ride.created_at).toLocaleDateString()
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {/* Footer */}
          <div className="px-6 py-3 border-t border-border-muted text-xs text-text-dim">
            Showing {rides.length} ride{rides.length !== 1 ? "s" : ""}
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
