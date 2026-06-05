"use client"
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, LayoutDashboard, BookOpen } from "lucide-react";

const links = [
  { href: "/", Icon: Home, label: "Home" },
  { href: "/dashboard", Icon: LayoutDashboard, label: "Dashboard" },
  { href: "/registry", Icon: BookOpen, label: "Registry" },
];

export default function BottomNav() {
  const pathname = usePathname();
  return (
    <nav className="fixed md:hidden bottom-0 inset-x-0 z-50 bg-app border-t border-border">
      <div className="flex items-center justify-around h-16 px-4">
        {links.map(({ href, Icon, label}) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link key={href} href={href} className={`flex flex-col items-center gap-1 text-fg-3 hover:text-white active:text-white ${ active ? 'text-white' : 'text-fg-3' }`}>
              <Icon size={20} />
              <span className="text-[11px]">{label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}