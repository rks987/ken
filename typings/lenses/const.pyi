"""
This type stub file was generated by pyright.
"""

from typing import Callable, Generic, TypeVar

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
D = TypeVar("D")
class Const(Generic[C, A]):
    """An applicative functor that doesn't care about the data it's
    supposed to be a functor over, caring only about the data it was passed
    during creation. This type is essential to the lens' `get` operation.
    """
    __slots__ = ...
    def __init__(self, item: C) -> None:
        ...
    
    def __repr__(self) -> str:
        ...
    
    def __eq__(self, other: object) -> bool:
        ...
    
    def map(self, func: Callable[[A], B]) -> Const[C, B]:
        ...
    
    def pure(self, item: D) -> Const[D, B]:
        ...
    
    def apply(self, fn: Const[C, Callable[[A], B]]) -> Const[C, B]:
        ...
    
    def unwrap(self) -> C:
        ...
    

