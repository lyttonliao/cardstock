REGISTRY_PATH = "data/registry/card_registry.parquet"
MIN_MARKET_PRICE = 5.00

# ── Specialty sets ─────────────────────────────────────────────────────────────
# Sets intentionally produced in limited quantities or as premium products.
SPECIALTY_SETS = {
    "cel25", "cel25c",                              # Celebrations
    "sm115", "sma",                                 # Hidden Fates + Shiny Vault
    "sm35",                                         # Shining Legends
    "sm75",                                         # Dragon Majesty
    "swsh35",                                       # Champion's Path
    "swsh45", "swsh45sv",                           # Shining Fates + Shiny Vault
    "swsh12pt5", "swsh12pt5gg",                     # Crown Zenith + Galarian Gallery
    "swsh9tg", "swsh10tg", "swsh11tg", "swsh12tg",  # Trainer Gallery subsets
    "sv3pt5",                                       # 151
    "sv4pt5",                                       # Paldean Fates
    "sv6pt5",                                       # Shrouded Fable
    "sv8pt5",                                       # Prismatic Evolutions
    "g1",                                           # Generations
    "xy12",                                         # Evolutions
    "pgo",                                          # Pokémon GO
    "det1",                                         # Detective Pikachu
    "me2pt5",                                       # Ascended Heroes
    "ecard2", "ecard3",                             # Aquapolis / Skyridge (limited print)
    "si1",                                          # Southern Islands
    "dv1",                                          # Dragon Vault
    "dc1",                                          # Double Crisis
    "rsv10pt5", "zsv10pt5",                         # White Flare / Black Bolt
}

# ── Per-set slot rates (packs to pull ANY card of that rarity) ─────────────────
# Source: riporfliptcg.com — community-sourced from large pack-opening samples.
# Keys are our registry set_ids; values map rarity string → packs_per_slot.
SET_SLOT_RATES = {
    # ── Scarlet & Violet era ──────────────────────────────────────────────────
    "sv1": {   # Scarlet & Violet
        "Double Rare": 7, "Illustration Rare": 13, "Ultra Rare": 15,
        "Special Illustration Rare": 32, "Hyper Rare": 53,
    },
    "sv2": {   # Paldea Evolved
        "Double Rare": 7, "Illustration Rare": 13, "Ultra Rare": 15,
        "Special Illustration Rare": 32, "Hyper Rare": 56,
    },
    "sv3": {   # Obsidian Flames
        "Double Rare": 7, "Illustration Rare": 13, "Ultra Rare": 15,
        "Special Illustration Rare": 32, "Hyper Rare": 53,
    },
    "sv3pt5": {  # 151
        "Double Rare": 8, "Illustration Rare": 13, "Ultra Rare": 16,
        "Special Illustration Rare": 32, "Hyper Rare": 50,
    },
    "sv4": {   # Paradox Rift
        "Double Rare": 7, "Illustration Rare": 13, "Ultra Rare": 15,
        "Special Illustration Rare": 53, "Hyper Rare": 83,
    },
    "sv4pt5": {  # Paldean Fates
        "Shiny Rare": 4, "Double Rare": 8, "Shiny Ultra Rare": 13,
        "Illustration Rare": 14, "Ultra Rare": 15,
        "Special Illustration Rare": 58, "Hyper Rare": 62,
    },
    "sv5": {   # Temporal Forces
        "Double Rare": 6, "Illustration Rare": 13, "Ultra Rare": 15,
        "ACE SPEC Rare": 20, "Special Illustration Rare": 86, "Hyper Rare": 139,
    },
    "sv6": {   # Twilight Masquerade
        "Double Rare": 6, "Illustration Rare": 13, "Ultra Rare": 15,
        "ACE SPEC Rare": 20, "Special Illustration Rare": 83, "Hyper Rare": 147,
    },
    "sv6pt5": {  # Shrouded Fable
        "Double Rare": 6, "Illustration Rare": 12, "Ultra Rare": 15,
        "ACE SPEC Rare": 20, "Special Illustration Rare": 67, "Hyper Rare": 143,
    },
    "sv7": {   # Stellar Crown
        "Double Rare": 6, "Illustration Rare": 13, "Ultra Rare": 15,
        "ACE SPEC Rare": 20, "Special Illustration Rare": 91, "Hyper Rare": 137,
    },
    "sv8": {   # Surging Sparks
        "Double Rare": 6, "Illustration Rare": 13, "Ultra Rare": 15,
        "ACE SPEC Rare": 20, "Special Illustration Rare": 87, "Hyper Rare": 189,
    },
    "sv8pt5": {  # Prismatic Evolutions
        "Double Rare": 6, "Ultra Rare": 13, "ACE SPEC Rare": 21,
        "Special Illustration Rare": 45, "Hyper Rare": 125,
    },
    "sv9": {   # Journey Together
        "Double Rare": 5, "Illustration Rare": 12, "Ultra Rare": 15,
        "ACE SPEC Rare": 20, "Special Illustration Rare": 86, "Hyper Rare": 137,
    },
    "sv10": {  # Destined Rivals
        "Double Rare": 5, "Illustration Rare": 12, "Ultra Rare": 16,
        "ACE SPEC Rare": 20, "Special Illustration Rare": 94, "Hyper Rare": 149,
    },
    "me1": {   # Mega Evolution
        "Double Rare": 5, "Illustration Rare": 9, "Ultra Rare": 12,
        "Special Illustration Rare": 101, "Mega Hyper Rare": 1259,
    },
    "me2": {   # Phantasmal Flames
        "Double Rare": 5, "Illustration Rare": 9, "Ultra Rare": 12,
        "Special Illustration Rare": 80, "Mega Hyper Rare": 1259,
    },
    "me2pt5": {  # Ascended Heroes
        "Double Rare": 5, "Illustration Rare": 9, "Ultra Rare": 21,
        "Mega Attack Rare": 29, "Special Illustration Rare": 69, "Mega Hyper Rare": 526,
    },
    "me3": {   # Perfect Order (low confidence — ~500 openings)
        "Double Rare": 5, "Illustration Rare": 9, "Ultra Rare": 18,
        "Special Illustration Rare": 72, "Hyper Rare": 357, "Mega Hyper Rare": 1250,
    },
    "rsv10pt5": {  # White Flare
        "Double Rare": 5, "Illustration Rare": 6, "Ultra Rare": 17,
        "Special Illustration Rare": 80, "Black White Rare": 500,
    },
    "zsv10pt5": {  # Black Bolt
        "Double Rare": 5, "Illustration Rare": 6, "Ultra Rare": 17,
        "Special Illustration Rare": 80, "Black White Rare": 500,
    },
    # ── Sword & Shield era ────────────────────────────────────────────────────
    # riporfliptcg "Holo Rare" = our "Rare Holo"
    # riporfliptcg "Ultra Rare" = our Rare Holo V/VMAX/VSTAR/Rare Ultra (full arts)
    # riporfliptcg "Secret Rare" = our Rare Rainbow/Rare Secret/Rare Shiny
    "swsh1": {
        "Rare Holo": 5, "Rare Ultra": 5, "Rare Holo V": 5,
        "Rare Holo VMAX": 5, "Rare Rainbow": 42, "Rare Secret": 42,
    },
    "swsh2": {  # Rebel Clash
        "Rare Holo": 5, "Rare Ultra": 5, "Rare Holo V": 5,
        "Rare Holo VMAX": 5, "Rare Rainbow": 42, "Rare Secret": 42,
    },
    "swsh3": {  # Darkness Ablaze
        "Rare Holo": 5, "Rare Ultra": 5, "Rare Holo V": 5,
        "Rare Holo VMAX": 5, "Rare Rainbow": 42, "Rare Secret": 42,
    },
    "swsh35": {  # Champion's Path
        "Rare Holo": 3, "Rare Ultra": 6, "Rare Holo V": 6,
        "Rare Rainbow": 40, "Rare Secret": 40,
    },
    "swsh4": {  # Vivid Voltage
        "Rare Holo": 5, "Rare Ultra": 5, "Rare Holo V": 5,
        "Amazing Rare": 18, "Rare Rainbow": 42, "Rare Secret": 42,
    },
    "swsh45": {  # Shining Fates
        "Rare Holo": 5, "Rare Ultra": 6, "Rare Holo V": 6,
        "Rare Holo VMAX": 6, "Amazing Rare": 18,
        "Rare Rainbow": 91, "Rare Secret": 91, "Rare Shiny": 91, "Rare Shiny GX": 91,
    },
    "swsh5": {  # Battle Styles
        "Rare Holo": 5, "Rare Ultra": 5, "Rare Holo V": 5,
        "Rare Holo VMAX": 5, "Rare Rainbow": 42, "Rare Secret": 42,
    },
    "swsh6": {  # Chilling Reign
        "Rare Holo": 5, "Rare Ultra": 5, "Rare Holo V": 5,
        "Rare Holo VMAX": 5, "Rare Rainbow": 42, "Rare Secret": 42,
    },
    "swsh7": {  # Evolving Skies
        "Rare Holo": 5, "Rare Ultra": 5, "Rare Holo V": 5,
        "Rare Holo VMAX": 5, "Rare Rainbow": 42, "Rare Secret": 42,
    },
    "swsh8": {  # Fusion Strike
        "Rare Holo": 5, "Rare Ultra": 5, "Rare Holo V": 5,
        "Rare Holo VMAX": 5, "Rare Rainbow": 42, "Rare Secret": 42,
    },
    "swsh9": {  # Brilliant Stars
        "Rare Holo": 4, "Rare Ultra": 4, "Rare Holo V": 4,
        "Rare Holo VSTAR": 4, "Rare Rainbow": 36, "Rare Secret": 36,
    },
    "swsh10": {  # Astral Radiance
        "Rare Holo": 4, "Rare Ultra": 4, "Rare Holo V": 4,
        "Rare Holo VSTAR": 4, "Radiant Rare": 20,
        "Rare Rainbow": 41, "Rare Secret": 41,
    },
    "swsh11": {  # Lost Origin
        "Rare Holo": 4, "Rare Ultra": 4, "Rare Holo V": 4,
        "Rare Holo VSTAR": 4, "Radiant Rare": 25,
        "Rare Rainbow": 31, "Rare Secret": 31,
    },
    "swsh12": {  # Silver Tempest
        "Rare Holo": 4, "Rare Ultra": 4, "Rare Holo V": 4,
        "Rare Holo VSTAR": 4, "Radiant Rare": 18,
        "Rare Rainbow": 34, "Rare Secret": 34,
    },
    "swsh12pt5": {  # Crown Zenith
        "Rare Holo": 2, "Rare Ultra": 3, "Rare Holo V": 3,
        "Rare Holo VSTAR": 3, "Radiant Rare": 20,
        "Rare Rainbow": 102, "Rare Secret": 102,
    },
    "pgo": {  # Pokémon GO
        "Rare Holo": 1, "Rare Ultra": 4, "Rare Holo V": 4,
        "Radiant Rare": 19, "Rare Rainbow": 27, "Rare Secret": 27,
    },
    "cel25": {  # Celebrations
        "Rare Holo": 3, "Rare Ultra": 8, "Rare Holo V": 8,
        "Rare Rainbow": 250, "Rare Secret": 250,
    },
}