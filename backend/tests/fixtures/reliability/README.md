# Reliability regression evidence

These are captured real source bytes, not generated company data:

- `astral-notice.pdf`: one-page NSE notice from the fresh 28 October IST verification. Its embedded approved issuer PDF link leads to the full transcript.
- `astral-transcript.pdf` and `tcs-transcript.pdf`: preserved original source PDFs. Each matching JSON records URL, SHA-256 and fetched time.
- `tcs-market-newer.json`: saved provider-derived market snapshot ending 27 October 2026.
- `tcs-market-older.json`: fresh provider-derived market snapshot ending 26 October 2026, captured in the earlier verification.
- `tcs-provider-partial.json`: raw serialized yfinance frame captured during this repair. The 27 October row has missing Close and Adj Close fields.

Tests also make explicitly controlled changes to copies of these records (amended text, future timestamps, bad OHLCV) and inject request failures. Those cases are synthetic diagnostics on real source structures, not claims that a company published those changes. No diagnostic mutation enters the delivered application database.
