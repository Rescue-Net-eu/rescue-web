import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import { AuthProvider } from "./lib/auth";
import { Shell } from "./components/shell";

export const metadata: Metadata = {
  title: "rescue-net.eu — Dispatcher Console",
  description:
    "Volunteer rescue alerting and mission coordination. Not a replacement for official emergency services — in life-threatening emergencies call your national emergency number (e.g. 112) first.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <Shell>{children}</Shell>
        </AuthProvider>
      </body>
    </html>
  );
}
