# Real Day 2 source fixtures

These JSON files contain complete page-indexed text captured from actual NSE PDFs on 28 October 2026, plus their original URL, observation time and SHA-256. They are regression fixtures, not simulated live API responses. Original PDF bytes are preserved by hash in the existing project database. TCS PDF page 8 and Polycab PDF page 4 were also rendered and visually checked against extracted figures.

- `tcs.json`: consolidated results; crores, six explicitly aligned period columns, total PAT including NCI. Reported EBITDA is unavailable in this statement and remains blank.
- `polycab.json`: consolidated results; millions, short date headers anchored to the explicitly reported 2026 year, exact conversion to crores and quarter-to-half-year reconciliation.
- `hdfcbank.json`: damaged/ambiguous date and numeric text; extraction must abstain.
- `infy.json`: mixed document sections and damaged/column-oriented statement text; extraction must abstain.
- `bajfinance.json`: actual reappointment, effective date and statutory issuer profile.
- `trent.json`: actual resignation; boilerplate and personal letter details must not become invented career/profile data.
- `lt.json`: complex multi-person management table; unsupported automatic event linking remains reviewable.

Synthetic faults, price/volume boundaries and HTTP model responses are constructed only inside `test_push.py` and temporary test databases. They never enter the production snapshot. No live Gemini test has been claimed.


### 30 October source-review regressions

`cover-regressions.json` contains six exact primary cover excerpts extracted from hash-verified PDF bytes in the uploaded Windows database. Original page counts remain so excerpts cannot pass full-document completeness checks. `persistent-resignation.json` preserves the primary resignation document, URL and hash used for the added event parser. `zero-page-source.pdf` is the original unusable saved TCS response (SHA-256 47b1bf8e9a49e9a3d15b1a57e3b268b374270eeae4a0f4a69f36b9fbf4b56409); it must be rejected, not treated as a complete PDF. A fresh readable PDF has since been obtained in the working database. Synthetic fault tests are labeled separately.
