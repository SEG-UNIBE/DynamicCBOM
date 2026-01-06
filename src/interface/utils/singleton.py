"""Singleton metaclass implementation for thread-safe singleton pattern.

Provides a metaclass for implementing the singleton pattern with thread safety.
"""

import threading


class SingletonMeta(type):
    """Metaclass for implementing thread-safe singletons.

    Ensures that only one instance of a class can exist, even in multi-threaded
    environments. Uses a class-level lock to synchronize access to the instances
    dictionary.

    Example:
        class MyClass(metaclass=SingletonMeta):
            def __init__(self):
                self.value = 42

        obj1 = MyClass()
        obj2 = MyClass()
        assert obj1 is obj2  # Both refer to the same instance
    """

    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        """Override call to ensure only one instance per class.

        Args:
            *args: Positional arguments for the class constructor.
            **kwargs: Keyword arguments for the class constructor.

        Returns:
            The singleton instance of the class.
        """
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]
