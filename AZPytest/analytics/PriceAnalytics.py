import numpy
import pandas

from .._tooling._log import fatal

class PriceAnalytics:
    def __init__(self, PriceSeries, VolumeSeries=None):
        self.PriceSeries  = PriceSeries
        self.VolumeSeries = VolumeSeries

    def ManipulatePriceSeries(self, new): # manipulation api (more readable than PriceAnalytics.PriceSeries = ...)
        self.PriceSeries = new 
        # example usage: pa.ManipulatePriceSeries(pa.PriceSeries[:30]), only keeps the most recent 30 entries
    def ManipulateVolumeSeries(self, new): 
        self.VolumeSeries = new 

    def _requireVolume(self):
        if self.VolumeSeries is None:
            fatal("VolumeSeries is required for this indicator")

    def _priceVolumeFrame(self): # price and volume side by side (one row per tick), rows with gaps dropped
        self._requireVolume()
        return pandas.DataFrame({"price": self.PriceSeries, "volume": self.VolumeSeries}).dropna()

    def returnExponentialMovingAverage(self, period):
        return self.PriceSeries.ewm(span=period, adjust=False).mean()

    def returnSimpleMovingAveraage(self, period):
        return self.PriceSeries.rolling(window=period).mean()

    def returnVolumeWeightedAveragePrice(self):
        df = self._priceVolumeFrame()
        return (df["price"] * df["volume"]).cumsum() / df["volume"].cumsum()

    def returnOnBalanceVolume(self): # volume added on up-ticks, subtracted on down-ticks, unchanged on flat ticks
        df = self._priceVolumeFrame()
        return (numpy.sign(df["price"].diff()).fillna(0) * df["volume"]).cumsum()

    def returnVolumeProfile(self, bins=24, binSize=None):
        df = self._priceVolumeFrame()
        low, high = df["price"].min(), df["price"].max()
        if binSize is not None:
            bins = int((high - low) // binSize) + 1
            edges = low + binSize * numpy.arange(bins + 1)
        else:
            edges = numpy.linspace(low, high, bins + 1) if high > low else numpy.array([low - 0.5, low + 0.5])
        volume, edges = numpy.histogram(df["price"], bins=edges, weights=df["volume"])
        levels = (edges[:-1] + edges[1:]) / 2
        return pandas.DataFrame({"volume": volume}, index=pandas.Index(levels, name="price"))

    def returnPointOfControl(self, bins=24, binSize=None): # the price level with the most volume
        return float(self.returnVolumeProfile(bins, binSize)["volume"].idxmax())

    def returnValueArea(self, bins=24, binSize=None, pct=0.7):
        volume = self.returnVolumeProfile(bins, binSize)["volume"]
        vals, target = volume.to_numpy(), pct * volume.sum()
        lo = hi = int(vals.argmax())
        total = vals[lo]
        while total < target and (lo > 0 or hi < len(vals) - 1):
            up   = vals[hi + 1] if hi < len(vals) - 1 else -1
            down = vals[lo - 1] if lo > 0 else -1
            if up >= down: hi += 1; total += vals[hi]
            else:          lo -= 1; total += vals[lo]
        return float(volume.index[lo]), float(volume.index[hi])

    def returnBollingerBands(self, period=20, numStd=2): # DataFrame of middle (SMA) / upper / lower, numStd standard deviations out
        middle = self.PriceSeries.rolling(window=period).mean()
        std    = self.PriceSeries.rolling(window=period).std(ddof=0)
        return pandas.DataFrame({"middle": middle, "upper": middle + numStd * std, "lower": middle - numStd * std})

    def returnRelativeStrengthIndex(self, period=14): # 0-100, Wilder smoothing; >70 often "overbought", <30 "oversold"
        delta = self.PriceSeries.diff()
        avgGain = delta.clip(lower=0).ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avgLoss = (-delta.clip(upper=0)).ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        return 100 - 100 / (1 + avgGain / avgLoss)

    def returnMACD(self, fast=12, slow=26, signal=9): # DataFrame of macd (fast EMA - slow EMA) / signal (EMA of macd) / histogram (macd - signal)
        macd = self.returnExponentialMovingAverage(fast) - self.returnExponentialMovingAverage(slow)
        sig  = macd.ewm(span=signal, adjust=False).mean()
        return pandas.DataFrame({"macd": macd, "signal": sig, "histogram": macd - sig})

    def returnRateOfChange(self, period): # percent change vs `period` rows ago
        return self.PriceSeries.pct_change(period) * 100
