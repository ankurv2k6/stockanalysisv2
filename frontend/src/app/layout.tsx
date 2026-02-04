import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import Link from "next/link";
import { BarChart3, Building2, FileText, Settings, ShieldAlert } from "lucide-react";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Stock Analysis Dashboard",
  description: "SEC 10-K Filing Analysis for S&P 100 Companies",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-background`}
      >
        <Providers>
          <div className="flex min-h-screen">
            {/* Sidebar Navigation */}
            <aside className="w-64 border-r bg-card">
              <div className="p-6">
                <h1 className="text-xl font-bold">Stock Analysis</h1>
                <p className="text-sm text-muted-foreground">SEC 10-K Dashboard</p>
              </div>
              <nav className="px-4 space-y-2">
                <Link
                  href="/"
                  className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent transition-colors"
                >
                  <BarChart3 className="h-5 w-5" />
                  Dashboard
                </Link>
                <Link
                  href="/companies"
                  className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent transition-colors"
                >
                  <Building2 className="h-5 w-5" />
                  Companies
                </Link>
                <Link
                  href="/filings"
                  className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent transition-colors"
                >
                  <FileText className="h-5 w-5" />
                  Filings
                </Link>
                <Link
                  href="/risk"
                  className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent transition-colors"
                >
                  <ShieldAlert className="h-5 w-5" />
                  Risk Analysis
                </Link>
                <Link
                  href="/admin"
                  className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-accent transition-colors"
                >
                  <Settings className="h-5 w-5" />
                  Admin
                </Link>
              </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 p-8">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
