# AZPytest

A small Python backtesting toolkit: replay tick data from a CSV one row at a time, place simulated long/short trades, and run price analytics.

## Setup

Requires Python 3 with `pandas` and `numpy` (and `pytest` to run the tests).

```
pip install pandas numpy pytest
```

## Usage

```python
import AZPytest.handling as dh

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

`AZPytest/analytics` has two classes that work on pandas Series:

### PriceAnalytics(PriceSeries, VolumeSeries=None)

| Method | Returns |
|---|---|
| `ManipulatePriceSeries(new)` | swaps the price series |
| `ManipulateVolumeSeries(new)` | swaps the volume series |
| `returnExponentialMovingAverage(period)` | Series |
| `returnSimpleMovingAveraage(period)` | Series |
| `returnVolumeWeightedAveragePrice()` | Series (needs volume) |
| `returnOnBalanceVolume()` | Series (needs volume) |
| `returnVolumeProfile(bins=24, binSize=None)` | DataFrame: `volume` per price level (needs volume) |
| `returnPointOfControl(bins=24, binSize=None)` | float, the busiest price level (needs volume) |
| `returnValueArea(bins=24, binSize=None, pct=0.7)` | `(low, high)` floats (needs volume) |
| `returnBollingerBands(period=20, numStd=2)` | DataFrame: `middle`, `upper`, `lower` |
| `returnRelativeStrengthIndex(period=14)` | Series |
| `returnMACD(fast=12, slow=26, signal=9)` | DataFrame: `macd`, `signal`, `histogram` |
| `returnRateOfChange(period)` | Series |

Volume-dependent methods raise `[fatal]` if no `VolumeSeries` was given.

### SetAnalytics(Series)

| Method | Returns |
|---|---|
| `ManipulateSeries(new)` | swaps the series |
| `returnRollingMovingAverage(period)` | Series |
| `returnZScore(period=None)` | Series (whole series if no period) |
| `returnPearsonCorrelation(other, period=None)` | float, or a Series if a period is given |
| `returnTanh()` | Series |
| `returnFisherTransform(period=None)` | Series |
| `returnSpreadBetweenSeries(other)` | Series, `other - Series`; the longer one is trimmed with a warning |

```python
import pandas as pd
from AZPytest.analytics.PriceAnalytics import PriceAnalytics

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
