"""
Utility
=======

Some utility functions and classes.
"""


class FibonacciSequence:
    """Fibonacci sequence generator

    :param start_from: initialize the sequence from the `start_from`-th item

    >>> fib = FibonacciSequence()
    >>> next(fib)
    1
    >>> next(fib)
    1
    >>> next(fib)
    2
    >>> next(fib)
    3
    >>> next(fib)
    5

    >>> fib.reset()
    >>> next(fib)
    1

    >>> fib = FibonacciSequence(start_from=3)
    >>> next(fib)
    3
    """

    def __init__(self, start_from: int = 0):
        self._start_from = start_from
        self._a = self._b = 1
        self.reset()

    def __iter__(self):
        return self

    def __next__(self):
        fib = self._a
        self._a, self._b = self._b, self._a + self._b

        return fib

    def reset(self):
        """Reset sequence generator to its original state

        """
        self._a = self._b = 1
        if self._start_from:
            for _ in range(self._start_from):
                next(self)


class CircularList:
    """A List in a cycle.

    The cycle starts at the 1st item in the input list, and moves to the next one each time called.

    Because a cycle does not have a head, nor tail, it does not make sense to define insert or append function on it.

    :param fixed_list: A list

    >>> cl = CircularList([1, 2, 3])
    >>> next(cl)
    1
    >>> next(cl)
    2
    >>> next(cl)
    3
    >>> next(cl)
    1
    """

    def __init__(self, fixed_list: list):
        self._list = fixed_list

    def __iter__(self):
        return self

    def __next__(self):
        cur = self._list[0]
        self._list = self._list[1:]
        self._list.append(cur)

        return cur
