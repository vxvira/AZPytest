import pandas

class PriceAnalytics:
    def __init__(self, PriceSeries, VolumeSeries=None):
        self.PriceSeries  = PriceSeries
        self.VolumeSeries = VolumeSeries

    def ManipulatePriceSeries(self, new): # manipulation api (more readable than PriceAnalytics.PriceSeries = ...)
        self.PriceSeries = new 
        # example usage: pa.ManipulatePriceSeries(pa.PriceSeries[:30]), only keeps the most recent 30 entries
    def ManipulateVolumeSeries(self, new): 
        self.VolumeSeries = new 

    def returnExponentialMovingAverage(self, period):
        return self.PriceSeries.ewm(span=period, adjust=False).mean()

    def returnSimpleMovingAveraage(self, period):
        return self.PriceSeries.rolling(window=period).mean()
