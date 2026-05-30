import type { Metadata } from "next";
import { Geist, Geist_Mono, Inter, Rubik } from "next/font/google";
import "./globals.css";
import { TooltipProvider } from "@/components/ui/tooltip";
import NavBar from "@/components/NavBar/NavBar";
import Footer from "@/components/Footer/Footer";


const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });
const geist = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono" });
const rubik = Rubik({ subsets: ["latin"], variable: "--font-display" });

export const metadata: Metadata = {
  title: "Cardstock",
  description: "Pokemon TCG card price prediction",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`dark ${inter.variable} ${rubik.variable} ${geist.variable} ${geistMono.variable}`}>
      <body>
        <TooltipProvider>
          <NavBar />
          <main className="flex-1 max-w-[1280px] mx-auto w-full px-6 py-8">
            {children}
          </main>
          <Footer />
        </TooltipProvider>
      </body>
    </html>
  );
}
