import Link from "next/link";
import Image from "next/image";

export default function Footer() {
  return (
    <footer className="border-t border-border bg-app">
      <div className="max-w-[1280px] mx-auto px-6 py-12 flex gap-12">
        {/* Brand */}
        <div className="flex flex-col gap-3">
          <Link href="/" className="flex items-center gap-2.5 no-underline">
            <Image src="/logo-mark.svg" alt="Cardstock" width={20} height={20} />
            <span className="font-display font-bold text-[15px] text-fg-1 tracking-[-0.01em]">
              Cardstock
            </span>
          </Link>
          <p className="text-xs text-fg-4 leading-relaxed max-w-[220px]">
            Pokemon TCG price history and ML-powered predictions.
          </p>
        </div>

        {/* Links */}
        <div className="flex flex-col gap-1.5">
          <p className="text-[11px] font-mono tracking-[0.14em] uppercase text-fg-4 mb-2">
            Contact
          </p>
          {[
            { label: "GitHub", href: "https://www.github.com/lyttonliao" },
            { label: "LinkedIn", href: "https://www.linkedin.com/in/lyttonliao" },
            { label: "Email", href: "mailto:lytton.liao@gmail.com" },
          ].map(({ label, href }) => (
            <a
              key={label}
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-fg-3 hover:text-fg-1 no-underline transition-colors"
            >
              {label}
            </a>
          ))}
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-border">
        <div className="max-w-[1280px] mx-auto px-6 py-4 flex items-center justify-between">
          <p className="text-[11px] text-fg-4">
            © {new Date().getFullYear()} Cardstock
          </p>
          <p className="text-[11px] text-fg-4">
            Prices sourced from{" "}
            <a
              href="https://www.tcgplayer.com"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-fg-3 transition-colors no-underline"
            >
              TCGPlayer
            </a>
            {" "}and{" "}
            <a
              href="https://www.pricecharting.com"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-fg-3 transition-colors no-underline"
            >
              PriceCharting
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
}
