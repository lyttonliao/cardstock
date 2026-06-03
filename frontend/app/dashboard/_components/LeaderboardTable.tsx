import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableCaption,
} from "@/components/ui/table";
import Link from "next/link";


type Column<T> = {
  header: string;
  render: (row: T) => React.ReactNode;
  href?: (row: T) => string;
}

const TAB_LABELS: Record<string, string> = {
  gainers: "Top Gainers",
  losers: "Top Losers",
};

export default function LeaderboardTable<T extends { card_id: string, variant: string }>({
  columns,
  data,
  suffix,
  ariaLabel,
  title,
}: {
  columns: Column<T>[];
  data: { gainers: T[], losers: T[] };
  suffix: string;
  ariaLabel: string;
  title?: string;
}) {
  return (
    <div className="flex flex-col gap-3">
      <Tabs defaultValue={`${suffix}-gainers`}>
        <TabsList aria-label={ariaLabel}>
          {Object.keys(data).map((key) => (
            <TabsTrigger key={key} value={`${suffix}-${key}`}>
              {TAB_LABELS[key] ?? key}
            </TabsTrigger>
          ))}
        </TabsList>
        {Object.entries(data).map(([key, cards]) => (
          <TabsContent key={key} value={`${suffix}-${key}`}>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-xs w-8">#</TableHead>
                  {columns.map((col) => (
                    <TableHead key={`${suffix}-${col.header}`} className="text-xs">{col.header}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {cards.map((card, i) => (
                  <TableRow key={`${suffix}-${key}-${card.card_id}-${i}`}>
                    <TableCell className="text-xs text-fg-4">{i + 1}</TableCell>
                    {columns.map((col, j) => (
                      <TableCell key={`${suffix}-${key}-${card.card_id}-col-${j}`} className="text-xs">
                        {col.href ? (
                          <Link
                            href={col.href(card)}
                            className="text-sky-400 hover:text-sky-300"
                          >
                            {col.render(card)}
                          </Link>
                        ) : col.render(card)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TabsContent>
        ))}
      </Tabs>
      {title && (
        <p className="text-[13px] text-fg-3 font-display font-semibold uppercase tracking-wide text-center">
          {title}
        </p>
      )}
    </div>
  )
}
