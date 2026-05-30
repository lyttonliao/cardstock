"use client"
import Link from "next/link";
import Image from "next/image";
import SearchDialog from "../SearchDialog/SearchDialog";

export default function NavBar() {
  return (
    <nav className="border-b border-border bg-app sticky top-0 z-10 px-6 py-[14px]">
      <div className="max-w-[1280px] mx-auto flex items-center gap-8">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 no-underline">
          <Image src="/logo-mark.svg" alt="Cardstock" width={24} height={24} />
          <span className="font-display font-bold text-[17px] text-fg-1 tracking-[-0.01em]">
            Cardstock
          </span>
        </Link>

        {/* Nav links */}
        <Link href="/dashboard" className="text-[13px] text-fg-3 hover:text-fg-1 no-underline transition-colors">Dashboard</Link>
        <Link href="/registry" className="text-[13px] text-fg-3 hover:text-fg-1 no-underline transition-colors">Registry</Link>
        {/* <Link href="#" onClick={(e) => e.preventDefault()} className="text-[13px] text-fg-3 hover:text-fg-1 no-underline transition-colors">Watchlist</Link>
        <Link href="#" onClick={(e) => e.preventDefault()} className="text-[13px] text-fg-3 hover:text-fg-1 no-underline transition-colors">Model</Link> */}

        <span className="flex-1" />

        {/* Search trigger */}
        <SearchDialog />
      </div>
    </nav>
  );
}
