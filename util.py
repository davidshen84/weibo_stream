class FibonacciSequence:
    """
Fibonacci sequence generator

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
        """
Create an instance

        :param start_from: initialize the sequence from the *start_from* item
        """
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
        """
Reset sequence generator to its original state
        """
        self._a = self._b = 1
        if self._start_from:
            for _ in range(self._start_from):
                next(self)
