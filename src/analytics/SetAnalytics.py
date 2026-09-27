import numpy
import pandas

from .._tooling._log import fatal, warn

class SetAnalytics: # statistics on any single series (prices, returns, volume, other indicators...)
    def __init__(self, Series):
        self.Series = Series

    def ManipulateSeries(self, new): # same idea as PriceAnalytics.ManipulatePriceSeries
        self.Series = new

    def returnRollingMovingAverage(self, period): # same as PriceAnalytics.returnSimpleMovingAveraage
        return self.Series.rolling(window=period).mean()

    def returnZScore(self, period=None):
        if period is None: mean, std = self.Series.mean(), self.Series.std(ddof=0)
        else:              mean, std = self.Series.rolling(window=period).mean(), self.Series.rolling(window=period).std(ddof=0)
        return (self.Series - mean) / std

    def returnPearsonCorrelation(self, other, period=None):
        if period is None: return self.Series.corr(other)
        return self.Series.rolling(window=period).corr(other)

    def returnTanh(self): # squashes every value into (-1, 1); large values saturate near +-1
        return numpy.tanh(self.Series)

    def returnFisherTransform(self, period=None):
        if period is None:
            x = self.Series
            if (x.abs() >= 1).any(): fatal("Fisher transform needs values strictly between -1 and 1, pass a period to rescale first")
        else:
            low, high = self.Series.rolling(window=period).min(), self.Series.rolling(window=period).max()
            x = (2 * (self.Series - low) / (high - low).where(high > low) - 1).clip(-0.999, 0.999) # flat windows have no range -> NaN
        return pandas.Series(numpy.arctanh(x), index=self.Series.index)

    def returnSpreadBetweenSeries(self, other): 
        n = min(len(self.Series), len(other))
        if len(other) > n:       warn(f"other has {len(other)} entries, trimmed to the first {n} to match Series")
        if len(self.Series) > n: warn(f"Series has {len(self.Series)} entries, trimmed to the first {n} to match other")
        series = self.Series.iloc[:n]
        return pandas.Series(numpy.asarray(other)[:n] - series.to_numpy(), index=series.index)
