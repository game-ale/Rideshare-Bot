"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Car,
  Users,
  Navigation,
  Menu,
  X,
  Sparkles,
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/drivers", label: "Drivers", icon: Car },
  { href: "/riders", label: "Riders", icon: Users },
  { href: "/rides", label: "Rides", icon: Navigation },
  { href: "/insights", label: "AI Insights", icon: Sparkles },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-50 h-14 bg-surface border-b border-border flex items-center px-4 gap-3">
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="p-1.5 rounded-lg hover:bg-surface-hover transition-colors"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
        <span className="text-sm font-semibold tracking-wide bg-gradient-to-r from-primary to-info bg-clip-text text-transparent">
          RideShare Admin
        </span>
      </div>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 z-40 h-screen w-64 bg-surface border-r border-border
          flex flex-col transition-transform duration-300 ease-in-out
          md:translate-x-0
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-info flex items-center justify-center">
              <Car size={16} className="text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-wide">RideShare</h1>
              <p className="text-[10px] text-text-dim uppercase tracking-widest">
                Admin Panel
              </p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200
                  ${
                    isActive
                      ? "bg-primary-muted text-primary shadow-sm shadow-primary/10"
                      : "text-text-muted hover:bg-surface-hover hover:text-text"
                  }
                `}
              >
                <Icon size={18} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-border">
          <div className="px-3 py-2 rounded-xl bg-surface-hover">
            <p className="text-[10px] text-text-dim uppercase tracking-wider">
              Connected to
            </p>
            <p className="text-xs text-text-muted mt-0.5">Telegram Bot API</p>
            <div className="flex items-center gap-1.5 mt-1">
              <div className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
              <span className="text-[10px] text-success">Live</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
