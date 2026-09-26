#  Externalized methods for trade handling. Pass self to each in the handling class

from ._tooling._tradeHandling import _addPosition, _closePosition

def _addLong(handling, contracts):  _addPosition(handling, contracts, 1)
def _addShort(handling, contracts): _addPosition(handling, contracts, -1)

def _closeLong(handling):  _closePosition(handling, 1)
def _closeShort(handling): _closePosition(handling, -1)

def _realizedPnl(handling):
    return handling._realizedPnlAccum

def _unrealizedPnl(handling):
    if handling.signedDirectionScale is None:
        return 0

    entry        = handling.entryData[-1]
    currentPrice = handling.data.price
    tickSz       = handling.config.tickSz
    tickVal      = handling.config.tickVal

    entryPrice, contracts = entry
    if handling.signedDirectionScale > 0: ticks = (currentPrice - entryPrice) / tickSz
    else:                                 ticks = (entryPrice - currentPrice) / tickSz

    return ticks * tickVal * contracts
