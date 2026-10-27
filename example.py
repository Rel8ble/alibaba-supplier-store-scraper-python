"""Alibaba supplier store scraper example: download whole supplier catalogs and build a supplier scorecard.

Usage:
    pip install -r requirements.txt
    set APIFY_TOKEN=<YOUR_APIFY_TOKEN>      (Linux/macOS: export APIFY_TOKEN=...)
    python example.py

Writes:
    supplier_catalog.csv    one row per product (price, MOQ, certificates, sales, store category, supplier)
    supplier_scorecard.csv  one row per supplier (catalog focus, certified share, selling share, prices, MOQ, company facts)
"""
import csv
import os
import statistics
from collections import Counter, defaultdict

from apify_client import ApifyClient

TOKEN = os.environ.get("APIFY_TOKEN", "<YOUR_APIFY_TOKEN>")

RUN_INPUT = {
    # Any mix of storefronts (or bare subdomains), product URLs and keywords.
    "storeUrls": [
        "https://alextechnology.en.alibaba.com/",
        "https://www.alibaba.com/product-detail/High-Quality-PU-Yoga-Mat-Custom_1601669249206.html",
    ],
    "searchTerms": ["bluetooth speaker"],
    "maxStoresPerSearch": 3,
    "maxProductsPerStore": 60,  # 0 = whole catalog (up to 4,000 per store)
    # "keywordInStore": "speaker",
    # "readyToShipOnly": True,
    # "maxMoq": 100,
}

CATALOG_FIELDS = [
    "supplierName", "storeCategory", "title", "priceMin", "priceMax", "moq", "moqUnit",
    "readyToShip", "certificates", "soldLast180Days", "orderCount", "url", "storeUrl", "source", "searchTerm",
]


def as_text(value):
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    if isinstance(value, dict):
        return value.get("name") or ""
    return "" if value is None else value


def scorecard(store_url, items):
    s = items[0]
    top_cat, top_n = Counter((i.get("storeCategory") or "Ungrouped").split(" > ")[0] for i in items).most_common(1)[0]
    lows = [i["priceMin"] for i in items if i.get("priceMin") is not None]
    moqs = [i["moq"] for i in items if i.get("moq") is not None]
    n = len(items)
    return {
        "supplier": s.get("supplierName"),
        "store": store_url,
        "businessType": "/".join(s.get("supplierBusinessType") or []),
        "yearsOnAlibaba": s.get("supplierYearsOnAlibaba"),
        "staff": s.get("supplierStaffCount"),
        "rating": s.get("supplierRating"),
        "verifiedBy": as_text(s.get("supplierVerifiedBy")),
        "storeTotalProducts": s.get("storeTotalProducts"),
        "productsScraped": n,
        "topCategory": top_cat,
        "focus": round(top_n / n, 2),  # share of scraped products in the biggest store category
        "certifiedShare": round(sum(bool(i.get("certificates")) for i in items) / n, 2),
        "sellingShare": round(sum((i.get("soldLast180Days") or 0) > 0 or (i.get("orderCount") or 0) > 0 for i in items) / n, 2),
        "readyToShipShare": round(sum(bool(i.get("readyToShip")) for i in items) / n, 2),
        "medianLowPrice": round(statistics.median(lows), 2) if lows else None,
        "lowestMoq": min(moqs) if moqs else None,
        "capabilities": as_text(s.get("supplierCapabilities")),
    }


def main():
    client = ApifyClient(TOKEN)
    run = client.actor("rel8ble/alibaba-supplier-store-scraper").call(run_input=RUN_INPUT)
    rows = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"{len(rows)} products")

    with open("supplier_catalog.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CATALOG_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: as_text(r.get(k)) for k in CATALOG_FIELDS})

    by_store = defaultdict(list)
    for r in rows:
        by_store[r["storeUrl"]].append(r)
    cards = [scorecard(url, items) for url, items in by_store.items()]
    # Most focused, most certified suppliers first.
    cards.sort(key=lambda c: (c["focus"] + c["certifiedShare"] + c["sellingShare"]), reverse=True)

    if cards:
        with open("supplier_scorecard.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(cards[0]))
            w.writeheader()
            w.writerows(cards)

    print(f"\n{'supplier':34} {'type':28} {'yrs':>3} {'staff':>5} {'focus':>5} {'certs':>5} {'selling':>7} {'med $':>6} {'MOQ':>5}")
    for c in cards:
        print(f"{(c['supplier'] or '')[:34]:34} {c['businessType'][:28]:28} {c['yearsOnAlibaba'] or '-':>3} "
              f"{c['staff'] or '-':>5} {c['focus']:5.0%} {c['certifiedShare']:5.0%} {c['sellingShare']:7.0%} "
              f"{c['medianLowPrice'] if c['medianLowPrice'] is not None else '-':>6} {c['lowestMoq'] if c['lowestMoq'] is not None else '-':>5}")
    print("\nWrote supplier_catalog.csv and supplier_scorecard.csv")


if __name__ == "__main__":
    main()
