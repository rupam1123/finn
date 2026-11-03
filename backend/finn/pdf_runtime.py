"""Basic PDF engine only; ML layout/telemetry extras are deliberately excluded."""
from importlib.metadata import version

if int(version('pymupdf').split('.')[0]) >= 2:
    raise RuntimeError('Install backend/requirements.lock.txt: this pipeline uses PyMuPDF 1.x without ML layout extras')

import pymupdf  # noqa: E402

__all__ = ['pymupdf']
