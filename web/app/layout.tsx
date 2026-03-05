import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Agent3 Dashboard",
  description: "Monitor autonomous runs and automations",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased bg-slate-950 text-slate-100">
        {children}
      </body>
    </html>
  );
}
