"""
This type stub file was generated by pyright.
"""

import sys
from typing import Callable, Generic, Iterator, TypeVar, Union

A = TypeVar("A")
B = TypeVar("B")
class Just(Generic[A]):
    """A class that can contain a value or not. If it contains a value
    then it will be an instance of Just. If it doesn't then it will be
    an instance of Nothing. You can wrap an existing value By calling
    the Just constructor:

        >>> from lenses.maybe import Just, Nothing
        >>> Just(1)
        Just(1)

    To extract it again you can use the `maybe` method:

        >>> Just(1).maybe()
        1
    """
    if sys.version_info[: 3] != (3, 5, 2):
        __slots__ = ...
    def __init__(self, item: A) -> None:
        ...
    
    def __add__(self, other: Just[A]) -> Just[A]:
        ...
    
    def __eq__(self, other: object) -> bool:
        ...
    
    def __iter__(self) -> Iterator[A]:
        ...
    
    def __repr__(self) -> str:
        ...
    
    def map(self, fn: Callable[[A], B]) -> Just[B]:
        """Apply a function to the value inside the Maybe."""
        ...
    
    def maybe(self, guard: B = ...) -> Union[None, A, B]:
        """Unwraps the value, returning it is there is one, else
        returning the guard."""
        ...
    
    def unwrap(self) -> A:
        ...
    
    def is_nothing(self) -> bool:
        ...
    


class Nothing(Just[A]):
    __slots__ = ...
    def __init__(self) -> None:
        ...
    
    def __add__(self, other: Just[A]) -> Just[A]:
        ...
    
    def __eq__(self, other: object) -> bool:
        ...
    
    def __iter__(self) -> Iterator[A]:
        ...
    
    def __repr__(self) -> str:
        ...
    
    def map(self, fn: Callable[[A], B]) -> Just[B]:
        """Apply a function to the value inside the Maybe."""
        ...
    
    def maybe(self, guard: B = ...) -> Union[None, A, B]:
        """Unwraps the value, returning it is there is one, else
        returning the guard."""
        ...
    
    def unwrap(self) -> A:
        ...
    
    def is_nothing(self) -> bool:
        ...
    


