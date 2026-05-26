"use client";

import { useEffect, useState } from "react";

import { AlertRow } from "@/components/alerts/alert-row";
import { createBrowserSupabaseClient, isSupabaseConfigured } from "@/lib/supabase";
import type { AlertRecord } from "@/types";

export function RealtimeAlertList({ initialAlerts }: { initialAlerts: AlertRecord[] }) {
  const [alerts, setAlerts] = useState(initialAlerts);

  useEffect(() => {
    if (!isSupabaseConfigured()) {
      return;
    }
    const supabase = createBrowserSupabaseClient();
    const channel = supabase
      .channel("homecare-alerts")
      .on("postgres_changes", { event: "INSERT", schema: "public", table: "alerts" }, (payload) => {
        setAlerts((current) => [payload.new as AlertRecord, ...current].slice(0, 30));
      })
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <AlertRow key={alert.id} alert={alert} />
      ))}
    </div>
  );
}
