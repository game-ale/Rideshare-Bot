"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import {
  Car,
  CheckCircle,
  XCircle,
  Clock,
  Shield,
  Star,
  Phone,
  MapPin,
  Wallet,
  Filter,
} from "lucide-react";
import { api, type Driver } from "@/lib/api";

export default function DriversPage() {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("ALL");
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  const fetchDrivers = async () => {
    try {
      const data = await api.getDrivers(filter === "ALL" ? undefined : filter);
      setDrivers(data);
    } catch (err) {
      console.error("Failed to fetch drivers:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchDrivers();
  }, [filter]);

  const handleVerify = async (driverId: number, action: "approve" | "reject") => {
    setActionLoading(driverId);
    try {
      await api.verifyDriver(driverId, action);
      await fetchDrivers();
    } catch (err) {
      console.error("Failed to verify driver:", err);
    } finally {
      setActionLoading(null);
    }
  };

  const statusConfig: Record<string, { color: string; icon: typeof CheckCircle }> = {
    APPROVED: { color: "text-success bg-success-muted", icon: CheckCircle },
    PENDING: { color: "text-warning bg-warning-muted", icon: Clock },
    REJECTED: { color: "text-danger bg-danger-muted", icon: XCircle },
    SUSPENDED: { color: "text-danger bg-danger-muted", icon: Shield },
  };

  const filters = ["ALL", "PENDING", "APPROVED", "REJECTED", "SUSPENDED"];

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Drivers</h1>
          <p className="text-text-muted text-sm mt-1">
            Manage driver registrations and verifications
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
      ) : drivers.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-[40vh] text-text-dim">
          <Car size={48} className="mb-3 opacity-30" />
          <p className="text-sm">No drivers found</p>
          <p className="text-xs mt-1">
            {filter !== "ALL" ? `No ${filter.toLowerCase()} drivers` : "Drivers will appear when they register via the bot"}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {drivers.map((driver) => {
            const sc = statusConfig[driver.status] || statusConfig.PENDING;
            const StatusIcon = sc.icon;
            return (
              <div
                key={driver.id}
                className="bg-surface rounded-2xl border border-border hover:border-primary/30 transition-all duration-300 overflow-hidden group"
              >
                {/* Header */}
                <div className="p-5 pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-info/20 flex items-center justify-center text-sm font-bold text-primary">
                        {driver.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <h3 className="font-semibold text-sm">{driver.name}</h3>
                        <p className="text-xs text-text-dim font-mono">
                          ID: {driver.id}
                        </p>
                      </div>
                    </div>
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wider ${sc.color}`}
                    >
                      <StatusIcon size={10} />
                      {driver.status}
                    </span>
                  </div>
                </div>

                {/* Details */}
                <div className="px-5 pb-3 space-y-2">
                  <div className="flex items-center gap-2 text-xs text-text-muted">
                    <Car size={12} className="text-text-dim" />
                    <span>
                      {driver.vehicle_type}
                      {driver.plate_number && ` · ${driver.plate_number}`}
                    </span>
                  </div>
                  {driver.phone_number && (
                    <div className="flex items-center gap-2 text-xs text-text-muted">
                      <Phone size={12} className="text-text-dim" />
                      <span>{driver.phone_number}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-xs text-text-muted">
                    <MapPin size={12} className="text-text-dim" />
                    <span>
                      {driver.latitude.toFixed(4)}, {driver.longitude.toFixed(4)}
                    </span>
                  </div>
                </div>

                {/* Metrics */}
                <div className="px-5 pb-3 flex items-center gap-4 text-xs">
                  <span className="flex items-center gap-1 text-warning">
                    <Star size={12} fill="currentColor" />
                    {driver.rating.toFixed(1)}
                  </span>
                  <span className="text-text-dim">
                    {driver.total_rides} rides
                  </span>
                  <span className="flex items-center gap-1 text-text-dim">
                    <Wallet size={12} />
                    {driver.wallet_balance.toFixed(0)} ETB
                  </span>
                  <span
                    className={`ml-auto text-[10px] font-medium px-2 py-0.5 rounded-full ${
                      driver.available
                        ? "text-success bg-success-muted"
                        : "text-text-dim bg-surface-hover"
                    }`}
                  >
                    {driver.available ? "● ONLINE" : "○ OFFLINE"}
                  </span>
                </div>

                {/* Actions for pending drivers */}
                {driver.status === "PENDING" && (
                  <div className="border-t border-border px-5 py-3 flex gap-2">
                    <button
                      onClick={() => handleVerify(driver.id, "approve")}
                      disabled={actionLoading === driver.id}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-success-muted text-success text-xs font-semibold hover:bg-success/20 transition-colors disabled:opacity-50"
                    >
                      <CheckCircle size={14} />
                      Approve
                    </button>
                    <button
                      onClick={() => handleVerify(driver.id, "reject")}
                      disabled={actionLoading === driver.id}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-danger-muted text-danger text-xs font-semibold hover:bg-danger/20 transition-colors disabled:opacity-50"
                    >
                      <XCircle size={14} />
                      Reject
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </DashboardLayout>
  );
}
