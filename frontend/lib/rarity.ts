const RARITY_MAP: Record<string, string> = {
  // Common
  "common":                        "var(--tier-common)",

  // Uncommon
  "uncommon":                      "var(--tier-uncommon)",

  // Rare
  "rare":                          "var(--tier-rare)",
  "rare holo":                     "var(--tier-rare)",
  "rare ace":                      "var(--tier-rare)",
  "rare break":                    "var(--tier-rare)",
  "double rare":                   "var(--tier-rare)",
  "amazing rare":                  "var(--tier-rare)",
  "radiant rare":                  "var(--tier-rare)",
  "promo":                         "var(--tier-rare)",

  // Ultra
  "rare ultra":                    "var(--tier-ultra)",
  "rare holo ex":                  "var(--tier-ultra)",
  "rare holo gx":                  "var(--tier-ultra)",
  "rare holo v":                   "var(--tier-ultra)",
  "rare holo vmax":                "var(--tier-ultra)",
  "rare holo vstar":               "var(--tier-ultra)",
  "rare holo lv.x":                "var(--tier-ultra)",
  "rare holo star":                "var(--tier-ultra)",
  "rare shiny":                    "var(--tier-ultra)",
  "rare shiny gx":                 "var(--tier-ultra)",
  "rare shining":                  "var(--tier-ultra)",
  "rare prime":                    "var(--tier-ultra)",
  "rare prism star":               "var(--tier-ultra)",
  "legend":                        "var(--tier-ultra)",
  "illustration rare":             "var(--tier-ultra)",
  "trainer gallery rare holo":     "var(--tier-ultra)",

  // Secret
  "rare secret":                   "var(--tier-secret)",
  "hyper rare":                    "var(--tier-secret)",
  "ace spec rare":                 "var(--tier-secret)",
  "special illustration rare":     "var(--tier-secret)",
  "classic collection":            "var(--tier-secret)",

  // Rainbow (gradient — background only, not text)
  "rare rainbow":                  "linear-gradient(90deg,#f87171,#fbbf24,#34d399,#38bdf8,#a78bfa)",
};

export function getRarityColor(rarity: string | null | undefined): string {
  if (!rarity) return "var(--tier-common)";
  return RARITY_MAP[rarity.toLowerCase()] ?? "var(--tier-common)";
}
