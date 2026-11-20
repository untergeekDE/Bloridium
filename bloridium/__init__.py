"""Bloridium - utilities for transferring synth programs Blofeld -> Iridium."""

import importlib

from .version import __version__

__all__ = ["audio", "midi"]  # lazily imported submodules


def __getattr__(name: str):
    # Lazy: `import bloridium` must not pull in mido/python-rtmidi (audio/midi),
    # so the pure-Python core (blofeld_dump, qpat, qpat_map, prognose) works
    # without MIDI libraries, e.g. in the web app container.
    if name in __all__:
        return importlib.import_module(f".{name}", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
