import type { Metadata } from "next";

import { SiteNav } from "@/components/site-nav";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "GOAL AI",
    template: "%s | GOAL AI",
  },
  description: "FIFA World Cup forecasting, team insights, player analysis, and model diagnostics powered by GOAL AI.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <header className="topbar">
            <div>
              <p className="brand-kicker">World Cup Forecasting</p>
              <div className="brand-mark">GOAL AI</div>
            </div>
            <SiteNav />
          </header>

          <main className="page-frame">{children}</main>

          <footer className="site-footer">
            XGBoost / LightGBM / Neural ensemble · SHAP explanations · Hugging Face team insights
          </footer>
        </div>
      </body>
    </html>
  );
}
