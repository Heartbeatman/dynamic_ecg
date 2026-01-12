"""Utility functions for signal processing."""
import time
from typing import Callable, Any


def timer_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to time function execution.

    Wraps a function and prints the execution time when called.
    Useful for profiling processing steps!

    Args:
        func: The function to wrap

    Returns:
        Wrapped function that prints timing info

    Example:
        @timer_decorator
        def slow_function():
            time.sleep(1)

        slow_function()  # Prints: Execution time for slow_function: 1.0 seconds
    """
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time for {func.__name__}: {execution_time} seconds")
        return result
    return wrapper
