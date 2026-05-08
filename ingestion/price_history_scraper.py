import re, json, os, time, logging
import requests
import pyarrow as pa
import pyarrow.parquet as pq
import duckdb
import unicodedata
from datetime import datetime, timezone
import random

os.makedirs("logs", exist_ok=True)
date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
log_path = f"logs/scrape_{date}.log"
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


BASE_URL = "https://www.pricecharting.com/game"

SET_SLUG_MAP = {
    # Base / Wizards Era
    "base1":        "base-set",
    "basep":        "promo",
    # E-Card Era
    "ecard1":       "expedition",
    # EX Series
    "np":           "promo",
    "ex4":          "team-magma-&-team-aqua",
    "ex6":          "fire-red-&-leaf-green",
    "tk1a":         "ex-latias-&-latios",
    "tk1b":         "ex-latias-&-latios",
    # Diamond & Pearl Era
    "dpp":          "promo",
    # Platinum Era
    "ru1":          "rumble",
    # HeartGold & SoulSilver Era
    "hsp":          "promo",
    "hgss2":        "unleashed",
    "hgss3":        "undaunted",
    "hgss4":        "triumphant",
    # Black & White Era
    "bwp":          "promo",
    # XY Era
    "xyp":          "promo",
    # Sun & Moon Era
    "smp":          "promo",
    "mcd18":        "mcdonalds-2018",
    "mcd19":        "mcdonalds-2019",
    "sma":          "hidden-fates",
    # Sword & Shield Era
    "swshp":        "promo",
    "swsh35":       "champion%27s-path",
    "mcd21":        "mcdonalds-2021",
    "swsh45sv":     "shining-fates",
    "cel25c":       "celebrations",
    "swsh9tg":      "brilliant-stars",
    "swsh10tg":     "astral-radiance",
    "swsh11tg":     "lost-origin",
    "swsh12tg":     "silver-tempest",
    "pgo":          "go",
    "mcd22":        "mcdonalds-2022",
    "swsh12pt5gg":  "crown-zenith",
    # Scarlet & Violet Era
    "svp":          "promo",
    "sv3pt5":       "scarlet-&-violet-151",
    "sve":          "scarlet-&-violet-energy",
}

VARIANT_SLUG_MAP = {
    "normal":              "",
    "unlimited":           "",
    "unlimitedHolofoil":   "",
    "holofoil":            "holo",
    "reverseHolofoil":     "reverse-holo",
    "1stEdition":          "1st-edition",
    "1stEditionHolo":      "1st-edition",
    "1stEditionHolofoil":  "1st-edition",
}


def slugify(text):
    """Convert a string into a URL-friendly, unique identifier"""

    # normalize then strip text of special characters
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub("'", "%27", text)
    text = re.sub(r'-+', '-', text).strip('-')
    text = text.replace('.', '')
    return text.lower().replace(' ', '-')


def build_url(set_id, set_name, card_name, card_number, variant=""):
    """Construct the pricecharting URL"""

    set_slug = SET_SLUG_MAP.get(set_id) or slugify(set_name)
    name_slug = slugify(card_name)
    number_slug = slugify(card_number)
    variant_slug = VARIANT_SLUG_MAP.get(variant, "")
    # cards with only 1 variant will likely not include the variant in its pricecharting url
    if variant_slug:
        return f"{BASE_URL}/pokemon-{set_slug}/{name_slug}-{variant_slug}-{number_slug}"
    return f"{BASE_URL}/pokemon-{set_slug}/{name_slug}-{number_slug}"


def fetch_price_history(url):
    """Extract VGPC.chart_data with regex, return parsed dict or None if not found"""

    try:
        response = requests.get(
            url,
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            },
            timeout=15
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        match = re.search(r'VGPC\.chart_data\s*=\s*(\{.*?\});', response.text, re.DOTALL)
        if not match:
            log.warning(f"No chart_data [{response.status_code}]: {url}")
            return None
        return json.loads(match.group(1))
    except Exception as e:
        log.error(f"Error fetching {url}: {e}")
        return None

def extract_nm_prices(chart_data, card_id, scraped_at, variant):
    """Return list of {date, price} from chart_data['used'] (raw card, near mint price)"""

    rows = []
    for timestamp_ms, price_cents in chart_data.get("used", []):
        if price_cents == 0:
            continue
        date = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        price = round(price_cents / 100, 2)
        rows.append({"id": card_id, "variant": variant, "date": date, "price": price, "scraped_at": scraped_at})
    return rows


def main():
    """Read registry parquet, loop cards, fetch + extract, write to data/prices/price_history.parquet"""

    conn = duckdb.connect()
    cards_df = conn.execute("SELECT * FROM 'data/registry/card_registry.parquet'").fetchdf()

    price_history_path = "data/prices/price_history.parquet"
    os.makedirs("data/prices", exist_ok=True)

    # check cards that have already been scraped
    if os.path.exists(price_history_path):
        already_scraped = conn.execute(f"""
            SELECT DISTINCT id, variant FROM '{price_history_path}'
        """).fetchdf()
        scraped_set = set(zip(already_scraped["id"], already_scraped["variant"]))
        print(f"Resuming — {len(scraped_set)} (card, variant) pairs already scraped.")
    else:
        scraped_set = set()
        print("No compatible existing data — starting fresh.")

    price_history_rows = []
    total = len(cards_df)
    miss_count = 0

    print("Initiating price scraper...")

    for i, (_, card) in enumerate(cards_df.iterrows()):
        card_id = card.get("id")
        card_number = card.get("number")
        set_name = card.get("set_name")
        card_name = card.get("name", "")
        variant = card.get("variant", "")

        if (card_id, variant) in scraped_set:
            continue

        set_id = card.get("set_id")
        if set_id == "ex4":
            card_name = re.sub(r"^(Team Magma's|Team Aqua's) ", "", card_name)

        pricecharting_url = build_url(set_id, set_name, card_name, card_number, variant)
        chart_data = fetch_price_history(pricecharting_url)

        if chart_data is None and VARIANT_SLUG_MAP.get(variant, ""):
            fallback_url = build_url(set_id, set_name, card_name, card_number)
            log.warning(f"FALLBACK [{i+1}/{total}] {card_name} ({variant}) -> {fallback_url}")
            chart_data = fetch_price_history(fallback_url)

        if chart_data:
            rows = extract_nm_prices(chart_data, card_id, date, variant)
            price_history_rows.extend(rows)
            log.info(f"OK    [{i+1}/{total}] {card_name} ({variant}) — {len(rows)} pts")
        else:
            miss_count += 1
            log.warning(f"MISS  [{i+1}/{total}] {card_name} ({variant}) — {pricecharting_url}")

        if (i + 1) % 100 == 0:
            print(f"[{i+1}/{total}] {miss_count} misses so far — log: {log_path}")

        time.sleep(random.uniform(1.5, 3.0))

    print(f"Done. {total} cards, {miss_count} misses. Full log: {log_path}")

    # concatenate tables on subsequent script execution
    if price_history_rows:
        new_table = pa.Table.from_pylist(price_history_rows)
        if os.path.exists(price_history_path):
            existing_table = pq.read_table(price_history_path)
            combined = pa.concat_tables([existing_table, new_table])
            pq.write_table(combined, price_history_path)
        else:
            pq.write_table(new_table, price_history_path)
    else:
        print("No new rows to write.")

    print("Price scraping complete!")


if __name__ == "__main__":
    main()
