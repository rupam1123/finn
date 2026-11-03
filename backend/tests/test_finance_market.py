from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd
import pytest

from finn.finance import delta, number, ratio, to_crores
from finn.market_data import frame_bars, indicators


@pytest.mark.parametrize("value,unit,expected", [(100,"lakhs",1),(10,"millions",1),(1,"billions",100),(10000000,"rupees",1),(42,"crores",42)])
def test_money(value, unit, expected):
    assert to_crores(value, unit) == Decimal(expected)


@pytest.mark.parametrize("kwargs", [{"unit":"unknown"},{"unit":"crores","currency":"USD"},{"unit":"crores","kind":"EPS"}])
def test_refuse_ambiguous_money(kwargs):
    with pytest.raises(ValueError):
        to_crores(100, **kwargs)


@pytest.mark.parametrize("curr,prev,state,pct", [(120,100,"comparable",20),(-20,-40,"loss_narrowed",None),(-60,-40,"loss_widened",None),(20,-40,"turnaround",None),(-20,40,"swung_to_loss",None),(0,-40,"loss_to_breakeven",None),(5,0,"zero_base",None),(None,5,"missing",None)])
def test_delta(curr, prev, state, pct):
    assert delta(curr, prev) == {"state": state, "percent": pct}


def test_missing_is_not_zero():
    assert number("—") is None
    assert number("NaN") is None
    assert number("(1,234.50)") == Decimal("-1234.5")
    assert number("0") == 0
    assert ratio(10,-5) is None
    assert ratio(10,0) is None


def bars(n=30):
    return [{"date": f"2026-09-{i+1:02}", "close": float(100+i), "adjusted_close": float(100+i),
             "volume": 100, "split": 0} for i in range(n)]


def test_volume_excludes_current_session():
    data = bars()
    data[-1]["volume"] = 300
    out = indicators(data)
    assert out["volume_ratio_20d"] == 3
    assert out["return_1d_pct"] == pytest.approx((129/128-1)*100)
    assert out["return_5d_pct"] == pytest.approx((129/124-1)*100)


def test_short_history_zero_volume_and_split():
    assert indicators(bars(20))["volume_ratio_20d"] is None
    data = bars()
    for row in data: row["volume"] = 0
    assert indicators(data)["volume_ratio_20d"] is None
    data = bars()
    data[-2]["split"] = 2
    assert indicators(data)["volume_ratio_20d"] is None


def test_invalid_and_duplicate_bars():
    data = bars()
    with pytest.raises(ValueError): indicators(data + [data[-1]])
    data[0]["close"] = float("nan")
    with pytest.raises(ValueError): indicators(data)


def test_intraday_excluded():
    df = pd.DataFrame({"Open":[100,101],"High":[105,106],"Low":[99,100],"Close":[103,104],
                       "Adj Close":[103,104],"Volume":[1000,500]}, index=pd.to_datetime(["2026-10-26","2026-10-27"]))
    early = frame_bars(df, datetime(2026,10,27,8,tzinfo=timezone.utc))
    late = frame_bars(df, datetime(2026,10,27,14,tzinfo=timezone.utc))
    assert len(early) == 1
    assert len(late) == 2
