# Parser fixtures

tcs.html and hdfcbank.html are selected table/document sections from public Screener pages fetched on 2026-10-27. nse.json is the first five records from the NSE TCS corporate-announcement response fetched on the same date. These are regression inputs, not demo data or primary financial evidence.

Source pages: https://www.screener.in/company/TCS/consolidated/ ; https://www.screener.in/company/HDFCBANK/consolidated/ ; https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=TCS .

Synthetic bars, PDF text and mock HTTP responses exist only inside unit tests.
