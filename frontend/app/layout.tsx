import type { Metadata } from "next";
import { Geist } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });

export const metadata: Metadata = {
  title: "Cardstock",
  description: "Pokemon TCG card price prediction",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geist.variable} h-full`}>
      <body className="min-h-full flex flex-col bg-gray-900 text-white antialiased">
        <nav className="border-b border-gray-800 px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center gap-8">
            <Link href="/" className="text-white font-bold text-lg tracking-tight">
              Cardstock
            </Link>
            <Link href="/" className="text-gray-400 hover:text-white text-sm transition-colors">
              Cards
            </Link>
            <Link href="/model" className="text-gray-400 hover:text-white text-sm transition-colors">
              Model
            </Link>
          </div>
        </nav>
        <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
