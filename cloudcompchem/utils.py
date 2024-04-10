import logging
import os

from pyscf import gto
from pyscf.lib.logger import CRIT, DEBUG, ERROR, NOTE, WARNING

logger = logging.getLogger("cloudcompchem")


def M(**kwargs):
    """A version of pyscf.gto.M that observes the root logger level."""

    def verbose() -> int:
        pyscf_log_level = os.environ.get("PYSCF_LOG_LEVEL")
        if pyscf_log_level is not None:
            return int(pyscf_log_level)

        level = logging.root.level
        if level >= logging.CRITICAL:
            return CRIT
        if level >= logging.ERROR:
            return ERROR
        if level >= logging.WARNING:
            return WARNING
        if level >= logging.INFO:
            return NOTE
        if level >= logging.DEBUG:
            return DEBUG

        return NOTE

    return gto.M(**kwargs, verbose=verbose())
