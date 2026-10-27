# Alibaba supplier store scraper in Python: download a supplier's full catalog as JSON/CSV

Scrape every product an Alibaba.com supplier lists on its storefront (`name.en.alibaba.com`) with Python, then vet suppliers from their catalogs: price range, MOQ, certificates, units sold in the last 180 days, orders, ready-to-ship flag and the store's own category for each product, plus the supplier card (business type, years on Alibaba, verified staff count, rating, verification company, rankings, capabilities) on every row.

This repo calls the [Alibaba Supplier Store Scraper](https://apify.com/rel8ble/alibaba-supplier-store-scraper) actor on Apify through the official `apify-client` package. No browser, no Alibaba login.

> Disclosure: I built this actor; it's a paid tool on Apify ($1.50 per 1,000 products, Apify's free monthly credit covers small tests).

## Why a store scraper and not a search scraper

Alibaba search tells you which suppliers sell a product. Once you have a shortlist, the questions change: how big is this supplier's catalog, is it focused on one category or a bit of everything, which listings actually sell, how much of it is certified, and is the company a 140-person factory or an 8-person trading office. Those answers sit on the storefront, 16 products per page and often dozens of pages deep. This actor reads all of it in one run.

Inputs it accepts, in any mix:

| Input | Example | What it does |
|---|---|---|
| `storeUrls` | `https://alextechnology.en.alibaba.com/` or just `alextechnology` | Scrape that storefront (a store category page works too) |
| `storeUrls` | an `alibaba.com/product-detail/...html` URL | Find the supplier behind the product, then scrape its store |
| `searchTerms` | `"bluetooth speaker"` | Search Alibaba, take the suppliers behind the results |
| `maxStoresPerSearch` | `3` | Suppliers per search term (default 5) |
| `maxProductsPerStore` | `100` / `0` | Products per store, 0 = whole catalog (up to 4,000) |
| `keywordInStore` | `"earphone"` | Only products matching a word inside each store |
| `readyToShipOnly`, `minPrice`, `maxPrice`, `maxMoq` | | Filters, applied before anything is charged |

## Quick start (Python)

```bash
pip install -r requirements.txt
export APIFY_TOKEN=<YOUR_APIFY_TOKEN>   # Windows: set APIFY_TOKEN=...
python example.py
```

The core call:

```python
from apify_client import ApifyClient

client = ApifyClient("<YOUR_APIFY_TOKEN>")
run = client.actor("rel8ble/alibaba-supplier-store-scraper").call(run_input={
    "storeUrls": ["https://alextechnology.en.alibaba.com/"],
    "searchTerms": ["bluetooth speaker"],
    "maxStoresPerSearch": 3,
    "maxProductsPerStore": 60,
})

for p in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(p["supplierName"][:30], p["storeCategory"], p["priceText"], "MOQ", p["moq"], "sold", p["soldLast180Days"])
```

## Node.js

```javascript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: '<YOUR_APIFY_TOKEN>' });
const run = await client.actor('rel8ble/alibaba-supplier-store-scraper').call({
    storeUrls: ['szyz'],             // bare subdomain works
    readyToShipOnly: true,
    maxProductsPerStore: 0,          // whole matching catalog
});
const { items } = await client.dataset(run.defaultDatasetId).listItems();
console.log(items.length, 'ready-to-ship products from', items[0]?.supplierName);
```

## What one row looks like

A real row from a 25 Oct 2026 run (trimmed; `images`, address and logo removed):

```json
{
  "productId": "1601955053032",
  "title": "ALOVA Air Conduction Headphone With All Key Features for Sports Comfortable Wear and High Performance",
  "priceMin": 9.3,
  "priceMax": 15,
  "priceText": "$9.30-15 / piece",
  "moq": 1,
  "moqUnit": "piece",
  "readyToShip": false,
  "certificates": ["UKCA", "DECLARATION OF CONFORMITY", "FCC", "ROHS", "CE"],
  "soldLast180Days": 10,
  "orderCount": 1,
  "storeCategory": "Open Ear Headphone > Call Center Headset",
  "supplierName": "Shenzhen Alex Technology Co., Ltd.",
  "storeUrl": "https://alextechnology.en.alibaba.com/",
  "supplierLocation": "Guangdong, China",
  "supplierBusinessType": ["Manufacturer", "Trading Company"],
  "supplierIdentity": "Custom Manufacturer",
  "supplierYearsOnAlibaba": 11,
  "supplierStaffCount": 142,
  "supplierRating": 4.5,
  "verifiedSupplier": true,
  "supplierVerifiedBy": "TüVRheinland",
  "supplierRanking": "#2 best seller in Sports Earphones & Headphones",
  "supplierCapabilities": ["Testing instruments (15)", "Patents awarded (6)", "Annual export US $2,104,093", "ODM services available"],
  "supplierAnnualExportUsd": 2104093,
  "storeTotalProducts": 296,
  "source": "store"
}
```

## The scorecard `example.py` prints

`example.py` writes `supplier_catalog.csv` (one row per product) and `supplier_scorecard.csv` (one row per supplier) and prints a table. This is its output on the actor's saved 18-row sample (3 products from each of 6 suppliers, reached by store URL, product URL and the keyword "bluetooth speaker"):

```
supplier                           type                         yrs staff focus certs selling  med $   MOQ
Shenzhen Yuzhuo Technology Co., Lt Trading Company               13     8   67%  100%    100%   5.39     2
Shenzhen Alex Technology Co., Ltd. Manufacturer/Trading Company  11   142  100%  100%     33%   12.5     1
MANOVA INTERNATIONAL LIMITED       Manufacturer                   7     -   67%  100%      0%    8.2   200
Dongguan Weixuan Household Product Manufacturer/Trading Company   3     -   67%    0%     67%      6     2
Guangzhou Umicca Sport Products Co Trading Company                4    10  100%    0%      0%   12.4    30
Dongguan Jiuzilong Industrial Co., Manufacturer/Trading Company   3    30   33%    0%     33%  11.56     1
```

- **focus**: share of scraped products in the supplier's biggest store category. A specialist scores high; a "sells everything" trading office scores low.
- **certs**: share of products listing at least one certificate (CE, FCC, RoHS ...).
- **selling**: share of products with sales in the last 180 days or any orders.
- **med $ / MOQ**: median low price and the lowest MOQ in the catalog.

Three products per store is only a demo; run with `maxProductsPerStore: 0` for the full picture. Pass the `url` of the products you keep to [Alibaba Product Details Scraper](https://github.com/Rel8ble/alibaba-product-details-scraper-python) when you need full price ladders, SKUs and lead times.

## Pricing and limits

- $1.50 per 1,000 products saved, no start fee. Products skipped by filters, duplicates, missing stores and failed requests are not charged.
- Listing-level data: full quantity price ladders, SKU variants and specs live on product pages.
- Sales counts appear on roughly a third of products; supplier rating, years, business type and verification on every row.
- Up to 4,000 products per store per run; scrape by store category or `keywordInStore` for bigger catalogs.
- No contact person names, phone numbers or emails are collected.

Actor page: https://apify.com/rel8ble/alibaba-supplier-store-scraper

## Related

- [alibaba-product-scraper-python](https://github.com/Rel8ble/alibaba-product-scraper-python): Alibaba keyword search results
- [alibaba-product-details-scraper-python](https://github.com/Rel8ble/alibaba-product-details-scraper-python): full product pages
- [global-sources-scraper-python](https://github.com/Rel8ble/global-sources-scraper-python): verified factories on Global Sources

## License

MIT for the code in this repo. The actor itself is a paid Apify tool.
