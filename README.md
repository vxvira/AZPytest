# AZPytest

A small Python backtesting toolkit: replay tick data from a CSV one row at a time, place simulated long/short trades, and run price analytics.

## Setup

Requires Python 3 with `pandas` and `numpy` (and `pytest` to run the tests).

```
pip install pandas numpy pytest
```

## Usage

```python
import src.handling as dh

cfg = dh.Configuration()
cfg.path         = "data.csv"
cfg.tickSz       = 0.25          # price increment of one tick
cfg.tickVal      = 0.25          # money value of one tick, per contract
cfg.priceAlias   = "price"       # CSV column names
cfg.tsEventAlias = "ts_event"
cfg.tsRecvAlias  = "ts_recv"
cfg.actionAlias  = "action"
cfg.buildConfig()

handler = dh.Handling(cfg)

handler.tick()                   # read the next row
handler.addLong(1)               # or addShort(n); adds change the net position
handler.tick()
handler.unrealizedPnl()          # pnl of the open trade
handler.closeLong()              # or closeShort()
handler.realizedPnl()            # pnl of the most recently closed trade
```

`addLong`/`addShort` adjust the net position: the same side grows it, the opposite side shrinks it, reaching zero ends the trade, and crossing zero flips it into a new trade. The first opposite-side add logs a warning.

Every tick is recorded in `handler.data` (price, tsEvent, tsRecv, action lists) and `handler.positionsData` (`[inTrade, unrealizedPnl, entryIdx]` per tick).

## Analytics

`src/analytics` has two classes that work on pandas Series:

- `PriceAnalytics(PriceSeries, VolumeSeries=None)`: EMA, SMA, VWAP, on-balance volume, volume profile (with point of control and value area), Bollinger Bands, RSI, MACD, rate of change.
- `SetAnalytics(Series)`: rolling moving average, z-score, Pearson correlation, tanh, Fisher transform, spread between series.

```python
import pandas as pd
from src.analytics.PriceAnalytics import PriceAnalytics

pa = PriceAnalytics(pd.Series(handler.data.price))
pa.returnExponentialMovingAverage(20)
pa.returnRelativeStrengthIndex(14)
```

## Tests

```
python -m pytest
```

## License

MIT, see [LICENSE](LICENSE).
