import pandas as pd
import warnings

from .tradeHandling import _addLong, _addShort, _closeLong, _closeShort, _realizedPnl, _unrealizedPnl

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
        if self.path == None: print(r"[/!\] Path not specified, exiting"); exit()


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

# private helper
def _updateHeldData(config, expected, onSet, onSetArg, onNone):
    if expected in config.aliases: onSet(onSetArg)
    else: warnings.warn(onNone)

class Handling:
    def __init__(self, config):
        self.config = config
        self.data = Data()

        self.idx = config.readFrom
        self._reader = pd.read_csv(config.path, usecols=config.aliases, chunksize=1, skiprows=range(1, config.readFrom)).__iter__()
    
        self.signedDirectionScale = None     # mumbo-jumbo for the total contracts being traded, signed (negative for short, and anagalously positive for long)
        self.entryData            = [[None]] # [[entry_price_one, contracts_one], [entry_price_two, contracts_two]]
        self._realizedPnlAccum    = 0

    def tick(self): # call inside of the mainloop
        self.dataAtIdx = next(self._reader).iloc[0]

        _updateHeldData(self.config, self.config.priceAlias, self.data.updatePrice, self.dataAtIdx[self.config.priceAlias], "[-] priceAlias not set")
        _updateHeldData(self.config, self.config.tsEventAlias, self.data.updateTsEvent, self.dataAtIdx[self.config.tsEventAlias], "[-] tsEventAlias not set")
        _updateHeldData(self.config, self.config.tsRecvAlias, self.data.updateTsRecv, self.dataAtIdx[self.config.tsRecvAlias], "[-] tsRecvAlias not set")
        _updateHeldData(self.config, self.config.actionAlias, self.data.updateAction, self.dataAtIdx[self.config.actionAlias], "[-] actionAlias not set")

    def addLong(self, contracts):  _addLong(self, contracts)
    def addShort(self, contracts): _addShort(self, contracts)
    def closeLong(self):     _closeLong(self)
    def closeShort(self):    _closeShort(self)
    def realizedPnl(self):   return _realizedPnl(self)
    def unrealizedPnl(self): return _unrealizedPnl(self)
