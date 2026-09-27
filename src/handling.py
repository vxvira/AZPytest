import pandas as pd
import warnings

from .tradeHandling import _addLong, _addShort, _closeLong, _closeShort, _realizedPnl, _unrealizedPnl

# helpers
warningsFed = [] # 
def _updateHeldData(config, expected, onSet, onSetArg):
    if expected in config.aliases: onSet(onSetArg)

def _fatalWarn(message):
    warnings.warn(f"[fatal] {message}")
    exit()
def _warn(message):
    warnings.warn(f"[warn] {message}")

class Configuration:
    def __init__(self):
        self.readFrom   = 1 # what row to start reading from

        self.path    = None
        self.tickSz  = 0.1 
        self.tickVal = 0.1 

        self.priceAlias   = None 
        self.tsEventAlias = None 
        self.tsRecvAlias  = None
        self.actionAlias  = None 

    def _buildAliases(self): 
        self.aliases = [a for a in (self.priceAlias, 
                                    self.tsEventAlias, 
                                    self.tsRecvAlias, 
                                    self.actionAlias,
                                    ) if a is not None] 

    def buildConfig(self):
        self._buildAliases()
        if self.path not in self.aliases: _fatalWarn("Path not specified!")

        # warnings
        if self.priceAlias not in self.aliases:   _warn("priceAlias not set")
        if self.tsEventAlias not in self.aliases: _warn("tsEventAlias not set")
        if self.tsRecvAlias not in self.aliases:  _warn("tsRecvAlias not set")
        if self.actionAlias not in self.aliases:  _warn("actionAlias not set") 

class Data:
    def __init__(self):
        self.price   = 0
        self.tsEvent = 0
        self.tsRecv  = 0
        self.action  = 0 

    def updatePrice(self, price):     self.price   = price
    def updateTsEvent(self, tsEvent): self.tsEvent = tsEvent
    def updateTsRecv(self, tsRecv):   self.tsRecv  = tsRecv
    def updateAction(self, action):   self.action  = action 

class DataSeries:
    def __init__(self, data):
        self.data = data 
        self.series = []

    def tick(self):
        self.series.append(self.data)

class Handling:
    def __init__(self, config):
        self.config = config
        self.dataAtTick = Data()
        self.data = DataSeries()

        self.idx = config.readFrom
        self._reader = pd.read_csv(config.path, usecols=config.aliases, chunksize=1, skiprows=range(1, config.readFrom)).__iter__()
    
        self.signedDirectionScale = None     # mumbo-jumbo for the total contracts being traded, signed (negative for short, and anagalously positive for long)
        self.entryData            = [[None]] # [[entry_price_one, contracts_one], [entry_price_two, contracts_two]]
        self._lastRealizedPnl     = 0        # realized pnl of the most recently closed trade

    def tick(self): # call inside of the mainloop
        self.dataAtIdx = next(self._reader).iloc[0]

        _updateHeldData(self.config, self.config.priceAlias, self.data.updatePrice, self.dataAtIdx[self.config.priceAlias])
        _updateHeldData(self.config, self.config.tsEventAlias, self.data.updateTsEvent, self.dataAtIdx[self.config.tsEventAlias])
        _updateHeldData(self.config, self.config.tsRecvAlias, self.data.updateTsRecv, self.dataAtIdx[self.config.tsRecvAlias])
        _updateHeldData(self.config, self.config.actionAlias, self.data.updateAction, self.dataAtIdx[self.config.actionAlias])

    # exposed trade handling api
    def addLong(self, contracts):  _addLong(self, contracts)
    def addShort(self, contracts): _addShort(self, contracts)
    def closeLong(self):           _closeLong(self)
    def closeShort(self):          _closeShort(self)
    def realizedPnl(self):         return _realizedPnl(self)
    def unrealizedPnl(self):       return _unrealizedPnl(self)