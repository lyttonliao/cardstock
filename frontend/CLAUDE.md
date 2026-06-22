# frontend/ — Claude Context

Next.js 16 App Router application. TypeScript, Tailwind CSS v4, shadcn/ui.

## Key Files

```
app/layout.tsx                      Root layout: fonts, NavBar, Footer, ScrollToTop, TooltipProvider
app/page.tsx                        Landing page (static, no API calls)
app/dashboard/page.tsx              Dashboard: KPI tiles + leaderboards (server component)
app/dashboard/_components/          Route-private components (LeaderboardTable)
app/registry/page.tsx               Set browser (static)
app/registry/cards/page.tsx         Card list — client component, infinite scroll, Algolia search
app/registry/cards/[id]/page.tsx    Card detail — server component, fetches prices + prediction
app/api/[...proxy]/route.ts         Proxy: browser requests → backend (avoids mixed-content)
lib/api.ts                          All API calls go through apiFetch()
lib/format.ts                       formatPrice, formatPct, formatLogReturnPct, pctTone, boolTone
lib/rarity.ts                       getRarityColor(rarity) → Tailwind color class
types/api.ts                        TypeScript interfaces matching FastAPI response schemas
components/                         Shared UI components
```

## Server vs Client Components

**Server components** (default in App Router): fetch data directly via `API_URL` (HTTP, server-to-server). Use `async/await` at the top level. Can't use hooks or browser APIs.

**Client components** (`"use client"` at top): run in the browser. All API calls go through `NEXT_PUBLIC_API_URL=/api` which routes through the proxy. Use hooks for state/effects.

**The proxy** (`app/api/[...proxy]/route.ts`): necessary because the frontend is on HTTPS (Vercel) but the backend ALB is plain HTTP. Browsers block HTTPS→HTTP (mixed content). The proxy is server-side so it can call HTTP freely.

**Rule of thumb:** If a component needs `useState`, `useEffect`, or browser events → `"use client"`. If it only displays data → server component.

## API Client (lib/api.ts)

```typescript
// BASE is resolved at module load time:
const BASE =
  typeof window === "undefined"
    ? (process.env.API_URL ?? "")           // server: direct to backend
    : (process.env.NEXT_PUBLIC_API_URL ?? "") // client: /api proxy

// apiFetch checks res.ok BEFORE calling res.json()
// (prevents SyntaxError when the backend returns an HTML error page)
```

Always add new API functions here. Type them with the interfaces from `types/api.ts`.

## Error Boundaries

Each route segment that does async data fetching has an `error.tsx`:
- `app/error.tsx` — global catch-all
- `app/dashboard/error.tsx` — dashboard API failures
- `app/registry/cards/[id]/error.tsx` — card detail failures

If you add a new dynamic route that calls the API, add an `error.tsx` alongside `page.tsx`.

## LeaderboardTable Component

Generic render-prop table at `app/dashboard/_components/LeaderboardTable.tsx`.

```typescript
type Column<T> = {
  header: string;
  render: (row: T) => React.ReactNode;
  href?: (row: T) => string;   // if set, wraps cell content in <Link>
}

<LeaderboardTable<MyType>
  title="Top 10 Movers"
  data={{ gainers: [...], losers: [...] }}
  columns={[...]}
  suffix="my-suffix"           // must be unique per table on the page (used for tab IDs)
/>
```

The component adds a `#` rank column automatically. Tab values are `{suffix}-gainers` and `{suffix}-losers`.

## Formatting Utilities (lib/format.ts)

- `formatPrice(n)` → `"$12.50"` (always 2 decimal places)
- `formatPct(n)` → `"12.5%"` (decimal 0.125 → "12.5%")
- `formatLogReturnPct(n)` → converts log return to percent string (`exp(n) - 1`)
- `pctTone(n)` → `"up" | "down" | "neutral"` for coloring
- `boolTone(b)` → `"up" | "down" | "neutral"` for boolean flags
- `capitalizeStr(s)` → capitalizes first letter of each word
- `formatDate(s)` → formats ISO date string for display

## Tailwind Design Tokens

Custom tokens defined in `globals.css`:
- `text-fg-1/2/3/4` — foreground hierarchy (fg-1 = primary, fg-4 = muted)
- `bg-surface`, `bg-elevated`, `bg-input` — background layers
- `border-border`, `border-border-2` — border hierarchy
- `text-bull` / `text-bear` — green/red for price movement
- `text-brand` — brand accent color
- `bg-hover` — hover state background
- `shadow-card` — card image drop shadow

Avoid hardcoded colors like `text-gray-500`. Use the token system.

## Rarity Colors (lib/rarity.ts)

`getRarityColor(rarity: string)` returns a color name for `<Badge color={...}>`. Handles: `"common"`, `"uncommon"`, `"rare"`, `"rare holo"`, `"rare ultra"`, `"rare secret"`, etc. Returns `"default"` for unknown rarities.

## Route-Private vs Shared Components

- `app/dashboard/_components/` — only used by the dashboard route. Not importable from other pages.
- `components/` — shared across routes (NavBar, Footer, PriceChart, Badge, KPITile, SearchDialog).
- `components/ui/` — shadcn/ui primitives (Button, Table, Tabs, Dialog, etc.). Don't modify these directly.

## useSearchParams Requirement

Any component using `useSearchParams()` must be wrapped in `<Suspense>` by its parent (Next.js build requirement):

```tsx
export default function Page() {
  return <Suspense><PageContent /></Suspense>
}
function PageContent() {
  const searchParams = useSearchParams();  // safe inside Suspense
  ...
}
```

## Environment Variables

| Variable | Used by | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Client components | Set to `/api` in production and local dev |
| `API_URL` | Server components, proxy route | Full HTTP URL to backend; never exposed to browser |
| `NEXT_PUBLIC_ALGOLIA_APP_ID` | SearchDialog | Baked in at build time |
| `NEXT_PUBLIC_ALGOLIA_SEARCH_KEY` | SearchDialog | Search-only key (safe to expose) |

`NEXT_PUBLIC_*` vars are embedded in the JS bundle at build time. `API_URL` is runtime-only.
