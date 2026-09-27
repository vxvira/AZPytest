# diagnostics: warn() logs through the "azpytest" logger, fatal() raises

import logging

_TAGS = {logging.WARNING: "warn", logging.ERROR: "error", logging.CRITICAL: "fatal"}

class _TagFormatter(logging.Formatter):
    def format(self, record):
        record.tag = _TAGS.get(record.levelno, record.levelname.lower())
        return super().format(record)

logger = logging.getLogger("azpytest")
if not logger.handlers: # default output; apps can attach their own handlers/levels to "azpytest"
    _handler = logging.StreamHandler()
    _handler.setFormatter(_TagFormatter("[%(tag)s] %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.WARNING)
    logger.propagate = False

_warned = set()

def warn(message):
    if message in _warned: return # each distinct warning is only reported once
    _warned.add(message)
    logger.warning(message)

def fatal(message):
    raise ValueError(f"[fatal] {message}")
