import atexit
import hashlib
import json
import pickle
from typing import Callable, TypeVar

import typer
from cachetools import cached


app = typer.Typer()

T = TypeVar("T")


def cached_persistent(filename: str) -> Callable[[T], T]:
    try:
        cache = pickle.load(open(filename, "rb"))
        # print(f"Loaded {len(cache)} entries from {filename}")
    except (IOError, ValueError):
        cache = {}

    def key(*args, **kwargs) -> bytes:
        return hashlib.sha512(json.dumps(list(args) + [kwargs], sort_keys=True).encode("utf-8")).digest()

    def flush() -> None:
        # print("cache.flush()")
        pickle.dump(cache, open(filename, "wb"))

    atexit.register(flush)

    return cached(cache=cache, key=key)
