"""
This type stub file was generated by pyright.
"""

from typing import Any, TypeVar
from functools import singledispatch

"""This module contains functions that you can hook into to allow various
lenses to operate on your own custom data structures.

You can hook into them by defining a method that starts with
``_lens_`` followed by the name of the hook function. So, for
example: the hook for ``lenses.hooks.contains_add`` is a method called
``_lens_contains_add``. This is the preferred way of hooking into this
library because it does not require you to have the lenses library as
a hard dependency.

These functions are all decorated with ``singledispatch``, allowing
you to customise the behaviour of types that you did not write. Be
warned that single dispatch functions are registered globally across
your program and that your function also needs to be able to deal with
subclasses of any types you register (or else register separate functions
for each subclass).

All of these hooks operate in the following order:

* Use an implementation registered with ``singledispatch.register``
  for the relevant type, if one exists.
* Use the relevant ``_lens_*`` method on the first object that was passed
  in, if it exists.
* Use a default implementation that is likely to work for most python
  objects, if one exists.
* Raise ``NotImplementedError``.
"""
A = TypeVar("A")
B = TypeVar("B")
@singledispatch
def setitem(self: Any, key: Any, value: Any) -> Any:
    """Takes an object, a key, and a value and produces a new object
    that is a copy of the original but with ``value`` as the new value of
    ``key``.

    The following equality should hold for your definition:

    .. code-block:: python

        setitem(obj, key, obj[key]) == obj

    This function is used by many lenses (particularly GetitemLens) to
    set items on states even when those states do not ordinarily support
    ``setitem``. This function is designed to have a similar signature
    as python's built-in ``setitem`` except that it returns a new object
    that has the item set rather than mutating the object in place.

    It's what enables the ``lens[some_key]`` functionality.

    The corresponding method call for this hook is
    ``obj._lens_setitem(key, value)``.

    The default implementation makes a copy of the object using
    ``copy.copy`` and then mutates the new object by setting the item
    on it in the conventional way.
    """
    ...

@singledispatch
def setattr(self: Any, name: Any, value: Any) -> Any:
    """Takes an object, a string, and a value and produces a new object
    that is a copy of the original but with the attribute called ``name``
    set to ``value``.

    The following equality should hold for your definition:

    .. code-block:: python

        setattr(obj, 'attr', obj.attr) == obj

    This function is used by many lenses (particularly GetattrLens) to set
    attributes on states even when those states do not ordinarily support
    ``setattr``. This function is designed to have a similar signature
    as python's built-in ``setattr`` except that it returns a new object
    that has the attribute set rather than mutating the object in place.

    It's what enables the ``lens.some_attribute`` functionality.

    The corresponding method call for this hook is
    ``obj._lens_setattr(name, value)``.

    The default implementation makes a copy of the object using
    ``copy.copy`` and then mutates the new object by calling python's
    built in ``setattr`` on it.
    """
    ...

@singledispatch
def contains_add(self: Any, item: Any) -> Any:
    """Takes a collection and an item and returns a new collection
    of the same type that contains the item. The notion of "contains"
    is defined by the object itself; The following must be ``True``:

    .. code-block:: python

        item in contains_add(obj, item)

    This function is used by some lenses (particularly ContainsLens)
    to add new items to containers when necessary.

    The corresponding method call for this hook is
    ``obj._lens_contains_add(item)``.

    There is no default implementation.
    """
    ...

@singledispatch
def contains_remove(self: Any, item: Any) -> Any:
    """Takes a collection and an item and returns a new collection
    of the same type with that item removed. The notion of "contains"
    is defined by the object itself; the following must be ``True``:

    .. code-block:: python

        item not in contains_remove(obj, item)

    This function is used by some lenses (particularly ContainsLens)
    to remove items from containers when necessary.

    The corresponding method call for this hook is
    ``obj._lens_contains_remove(item)``.

    There is no default implementation.
    """
    ...

@singledispatch
def to_iter(self: Any) -> Any:
    """Takes an object and produces an iterable. It is intended as the
    inverse of the ``from_iter`` function.

    The reason this hook exists is to customise how dictionaries are
    iterated. In order to properly reconstruct a dictionary from an
    iterable you need access to both the keys and the values. So this
    function iterates over dictionaries by thier items instead.

    The corresponding method call for this hook is
    ``obj._lens_to_iter()``.

    The default implementation is to call python's built in ``iter``
    function.
    """
    ...

@singledispatch
def from_iter(self: Any, iterable: Any) -> Any:
    """Takes an object and an iterable and produces a new object that is
    a copy of the original with data from ``iterable`` reincorporated. It
    is intended as the inverse of the ``to_iter`` function. Any state in
    ``self`` that is not modelled by the iterable should remain unchanged.

    The following equality should hold for your definition:

    .. code-block:: python

        from_iter(self, to_iter(self)) == self

    This function is used by EachLens to synthesise states from iterables,
    allowing it to focus every element of an iterable state.

    The corresponding method call for this hook is
    ``obj._lens_from_iter(iterable)``.

    There is no default implementation.
    """
    ...

