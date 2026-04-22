"""Truth table utilities.

Example usage::
    >>> from truthtable import ttablef
    >>> ttablef(lambda e, g, h: not h)
    e g h
    T T T | F
    T T F | T
    T F T | F
    T F F | T
    F T T | F
    F T F | T
    F F T | F
    F F F | T
"""

from collections.abc import Iterator
from inspect import signature
from itertools import product
from typing import Callable


def truthtable(f: Callable[..., bool]) -> Iterator[tuple[tuple[bool, ...], bool]]:
    """Generate a truth table for a function that takes n bools."""
    sig = signature(f)
    n_params = len(sig.parameters)

    for case in product([True, False], repeat=n_params):
        yield case, f(*case)


def tf_string(v: bool) -> str:
    """Convert a boolean to T/F."""
    return "T" if v else "F"


def iff(a: bool, b: bool) -> bool:
    """Perform A⇔ B."""
    return a == b


def imply(a: bool, b: bool) -> bool:
    """Perform A⇒B."""
    return not a or b


def ttablef(f: Callable[..., bool]) -> None:
    """Print a truth table for a function."""
    print(*list(signature(f).parameters))
    for case, result in truthtable(f):
        print(*[tf_string(v) for v in case], "|", tf_string(result))
