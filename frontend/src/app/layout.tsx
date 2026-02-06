import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TradeBot Dashboard",
  description: "Crypto Trading Bot Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
