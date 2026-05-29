import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "rescue-net.eu — Dispatcher Console",
  description:
    "Volunteer rescue alerting and mission coordination. Not a replacement for official emergency services — in life-threatening emergencies call your national emergency number (e.g. 112) first.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          fontFamily: "system-ui, Arial, sans-serif",
          color: "#1a1a1a",
        }}
      >
        {children}
      </body>
    </html>
  );
}
