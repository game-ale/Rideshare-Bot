"use client";

import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { Users, Phone, Globe, Wallet } from "lucide-react";
import { api, type Rider } from "@/lib/api";

export default function RidersPage() {
  const [riders, setRiders] = useState<Rider[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchRiders() {
      try {
        const data = await api.getRiders();
        setRiders(data);
      } catch (err) {
        console.error("Failed to fetch riders:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchRiders();
  }, []);

  const langLabel: Record<string, string> = {
    en: "English",
    am: "Amharic",
    om: "Afan Oromo",
  };

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight">Riders</h1>
        <p className="text-text-muted text-sm mt-1">
          All registered riders on the platform
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-[40vh]">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : riders.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-[40vh] text-text-dim">
          <Users size={48} className="mb-3 opacity-30" />
          <p className="text-sm">No riders yet</p>
          <p className="text-xs mt-1">
            Riders will appear when they register via the Telegram bot
          </p>
        </div>
      ) : (
        <div className="bg-surface rounded-2xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-muted">
                  <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                    Rider
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                    Phone
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                    Language
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                    Wallet
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-text-dim uppercase tracking-wider">
                    Joined
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-muted">
                {riders.map((rider) => (
                  <tr
                    key={rider.id}
                    className="hover:bg-surface-hover transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-info/20 to-primary/20 flex items-center justify-center text-xs font-bold text-info">
                          {rider.name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="font-medium text-sm">{rider.name}</p>
                          <p className="text-xs text-text-dim font-mono">
                            ID: {rider.id}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-text-muted">
                      {rider.phone_number ? (
                        <span className="flex items-center gap-1.5">
                          <Phone size={12} className="text-text-dim" />
                          {rider.phone_number}
                        </span>
                      ) : (
                        <span className="text-text-dim">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className="flex items-center gap-1.5 text-text-muted text-xs">
                        <Globe size={12} className="text-text-dim" />
                        {langLabel[rider.language_code] || rider.language_code}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="flex items-center gap-1.5 text-text-muted text-xs">
                        <Wallet size={12} className="text-text-dim" />
                        {rider.wallet_balance.toFixed(0)} ETB
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-text-dim">
                      {rider.created_at
                        ? new Date(rider.created_at).toLocaleDateString()
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
