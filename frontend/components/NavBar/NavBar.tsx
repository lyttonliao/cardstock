"use client"
import Link from "next/link";
import SearchDialog from "../SearchDialog/SearchDialog";

export default function NavBar() {
  return (
    <nav className="border-b border-gray-800 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center gap-8">
        <Link href="/" className="text-white font-bold text-lg tracking-tight">
          Cardstock
        </Link>
        <Link href="/" className="text-gray-400 hover:text-white text-sm transition-colors">
          Cards
        </Link>
        <SearchDialog />
      </div>
    </nav>
  )
}