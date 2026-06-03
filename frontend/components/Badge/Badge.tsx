import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex shrink-0 items-center justify-center rounded-full border bg-clip-padding text-[11px] font-medium font-sans",
  {
    variants: {
      variant: {
        meta:  "bg-white/[0.06] border-border-2 text-fg-2",
        bull:  "bg-[rgba(52,211,153,0.10)] border-[rgba(52,211,153,0.28)] text-bull",
        bear:  "bg-[rgba(248,113,113,0.10)] border-[rgba(248,113,113,0.28)] text-bear",
        info:  "bg-[rgba(56,189,248,0.10)] border-[rgba(56,189,248,0.28)] text-[#7dd3fc]",
        warn:  "bg-[rgba(251,191,36,0.10)] border-[rgba(251,191,36,0.28)] text-[#fbbf24]",
        brand: "bg-[rgba(249,115,22,0.10)] border-[rgba(249,115,22,0.32)] text-[#fdba74]",
      },
    },
    defaultVariants: { variant: "meta" },
  }
)

function BadgeDot({ color }: { color: string }) {
  return <div className="w-1.5 h-1.5 rounded-full" style={{ background: color }} />;
}

export default function Badge({
  variant,
  className,
  icon,
  color,
  children,
  ...props
}: React.ComponentProps<"span"> &
  VariantProps<typeof badgeVariants> & {
    icon?: React.ReactNode;
    color?: string;
    className?: string;
  }) {
  return (
    <span {...props} className={cn(badgeVariants({ variant }), "px-3 py-1 gap-1.5", className )}>
      {color && <BadgeDot color={color} />}
      {icon}
      {children}
    </span>
  )
}