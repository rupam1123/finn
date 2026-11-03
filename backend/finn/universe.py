import csv
import io
import re

PORTFOLIO = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "TMPV", "SUNPHARMA",
             "LT", "BAJFINANCE", "TRENT", "ETERNAL", "PERSISTENT", "DIXON",
             "POLYCAB", "DEEPAKNTR", "LAURUSLABS", "KPITTECH", "SUZLON", "JYOTHYLAB"]
SHOWCASE = ["TITAN", "COFORGE", "SYNGENE", "SONACOMS", "CAMS"]
CATEGORIES = ["results", "M&A", "fund_raise", "management_change", "litigation",
              "insider_trading", "earnings_call", "investor_meetings", "credit_rating",
              "dividend", "bonus_split", "capex", "press_release", "postal_ballot",
              "agm_egm", "pledging", "unclassified"]
MASTER_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"


def symbol(value: str) -> str:
    value = value.strip().upper()
    if value.endswith(".NS"):
        value = value[:-3]
    if value == "ZOMATO":
        return "ETERNAL"
    if value == "TATAMOTORS":
        raise ValueError("TATAMOTORS is historical: choose TMPV (passenger) or TMCV (commercial)")
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9&-]{0,29}", value):
        raise ValueError("Enter an NSE symbol, not a URL or company-name query")
    return value


def parse_master(text: str) -> list[dict]:
    rows = []
    for raw in csv.DictReader(io.StringIO(text.lstrip("\ufeff"))):
        r = {k.strip(): v.strip() for k, v in raw.items() if k and v is not None}
        if r.get("SERIES") == "EQ":
            rows.append({"symbol": symbol(r["SYMBOL"]), "company_name": r["NAME OF COMPANY"],
                         "isin": r["ISIN NUMBER"], "sector": None})
    if not rows:
        raise ValueError("Security master contained no equity records")
    return rows
