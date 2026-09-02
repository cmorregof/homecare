import type { Metadata } from "next";

import { BRAND_FULL } from "@/lib/brand";
import "./globals.css";

export const metadata: Metadata = {
  title: BRAND_FULL,
  description: "Monitoreo domiciliario con agentes IA para pacientes cardio-cerebrovasculares.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
