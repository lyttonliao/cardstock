import Image from "next/image";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <div>
      {/* Full-width banner */}
      <div className="w-screen relative left-1/2 -translate-x-1/2 animate-pulse [animation-duration:4s] -mt-8 aspect-[16/12] md:aspect-[16/6]">
        <Image src="/Pulse.png" alt="banner" fill className="object-cover" priority />
      </div>

      {/* Hero */}
      <div className="relative py-14 md:py-28 flex flex-col items-center text-center overflow-hidden">
        <div className="relative z-10 flex flex-col items-center justify-center gap-5 max-w-xl">
          <p className="text-[11px] font-mono text-fg-4 tracking-[0.18em] uppercase">Pokemon TCG · Price Intelligence</p>
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-display font-bold text-fg-1 leading-tight tracking-tight">
            Track. Predict.<br />Trade.
          </h1>
          <p className="w-full text-sm font-display text-fg-3 max-w-sm leading-relaxed">Market price history and ML-powered predictions for trending cards in the Pokemon TCG catalog.</p>
          <Link href="/registry">
            <Button className="bg-brand hover:bg-brand/90 transition-opacity text-white font-medium text-sm" size="lg">
              Browse Cards
            </Button>
          </Link>
        </div>
      </div>

      {/* How it works */}
      <div className="py-16 border-t border-border">
        <p className="font-mono text-[11px] text-fg-4 tracking-[0.18em] uppercase mb-8">
          How it works
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              step: "01",
              title: "Browse the catalog",
              description: "Search across thousands of cards from every set. Filter by rarity, variant, and set.",
            },
            {
              step: "02",
              title: "View price history",
              description: "See TCGPlayer market price history with moving averages and volatility metrics.",
            },
            {
              step: "03",
              title: "Get a prediction",
              description: "Our XGBoost model forecasts 30-day price direction based on historical price trends."
            }
          ].map(({ step, title, description}) => (
            <div
              key={`${step}_${title}`}
              className="flex flex-col gap-3 border border-border bg-surface p-6 rounded-xl"
            >
              <span className="text-[11px] font-mono text-brand">{step}</span>
              <h1 className="text-sm font-display font-semibold text-fg-1">{title}</h1>
              <p className="text-xs text-fg-3 leading-relaxed">{description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
