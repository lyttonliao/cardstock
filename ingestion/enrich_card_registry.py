import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from constants import REGISTRY_PATH, SPECIALTY_SETS, SET_SLOT_RATES


def main():
    conn = duckdb.connect()
    df = conn.execute(f"SELECT * FROM '{REGISTRY_PATH}'").fetchdf()
    print(f"Loaded {len(df)} rows from registry.")

    df["is_specialty_set"] = df["set_id"].isin(SPECIALTY_SETS).astype(int)
    print(f"Specialty set rows: {df['is_specialty_set'].sum()} / {len(df)}")

    def get_packs_per_slot(row):
        slot_rates = SET_SLOT_RATES.get(row["set_id"])
        if slot_rates is None:
            return None  # Older set — no data
        return slot_rates.get(row["rarity"])  # None if rarity not in slot map

    df["packs_per_slot"] = df.apply(get_packs_per_slot, axis=1)

    rarity_counts = (
        df.groupby(["set_id", "rarity"])
        .size()
        .reset_index(name="cards_in_rarity_slot")
    )
    df = df.merge(rarity_counts, on=["set_id", "rarity"], how="left")

    df["packs_per_specific_card"] = df["packs_per_slot"] * df["cards_in_rarity_slot"]

    covered = df["packs_per_slot"].notna().sum()
    print(f"packs_per_slot coverage: {covered} / {len(df)} rows")

    unmapped = df[df["packs_per_slot"].isna() & df["set_id"].isin(SET_SLOT_RATES)]["rarity"].unique()
    if len(unmapped):
        print(f"Rarities in covered sets with no slot mapping: {unmapped.tolist()}")

    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, REGISTRY_PATH)
    print(f"Written to {REGISTRY_PATH}")


if __name__ == "__main__":
    main()