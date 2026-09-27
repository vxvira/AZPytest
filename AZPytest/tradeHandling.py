#  Externalized methods for trade handling. Pass self to each in the handling class

from ._tooling._tradeHandling import _addPosition, _closePosition, _tradePnl

def _addLong(handling, contracts):  _addPosition(handling, contracts, 1)
def _addShort(handling, contracts): _addPosition(handling, contracts, -1)

def _closeLong(handling):  _closePosition(handling, 1)
def _closeShort(handling): _closePosition(handling, -1)

def _realizedPnl(handling):
    return handling._lastRealizedPnl # pnl of the most recently closed trade

def _unrealizedPnl(handling): # pnl of the currently open trade (all of its entries)
    return _tradePnl(handling)

def _tickTradeData(handling): # record this tick's position state
    inTrade = handling.signedDirectionScale is not None
    handling.positionsData.append([inTrade, _unrealizedPnl(handling), handling.entryIdx])
