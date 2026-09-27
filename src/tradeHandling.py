#  Externalized methods for trade handling. Pass self to each in the handling class

from ._tooling._tradeHandling import _addPosition, _closePosition

def _addLong(handling, contracts):  _addPosition(handling, contracts, 1)
def _addShort(handling, contracts): _addPosition(handling, contracts, -1)

def _closeLong(handling):  _closePosition(handling, 1)
def _closeShort(handling): _closePosition(handling, -1)

def _realizedPnl(handling):
    return handling._lastRealizedPnl # pnl of the most recently closed trade

def _unrealizedPnl(handling): # pnl of the currently open trade (all of its entries)
    if handling.signedDirectionScale is None:
        return 0

    currentPrice = handling.dataAtTick.price
    tickSz       = handling.config.tickSz
    tickVal      = handling.config.tickVal
    sign         = 1 if handling.signedDirectionScale > 0 else -1

    pnl = 0
    for entryPrice, contracts in handling.entryData:
        ticks = sign * (currentPrice - entryPrice) / tickSz
        pnl  += ticks * tickVal * contracts

    return pnl

def _tickTradeData(handling): # record this tick's position state
    inTrade = handling.signedDirectionScale is not None
    handling.positionsData.append([inTrade, _unrealizedPnl(handling), handling.entryIdx])
