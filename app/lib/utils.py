import time
import math
from typing import List

def _mock_io_bound_operation() -> None:
    """
    Simulates an I/O-bound operation with a delay.
    """
    # This delay can be assumed to be unavoidable, and may not be constant in a real world situation.
    print("Performing mock I/O-bound operation...")
    time.sleep(3)  # Simulate waiting for an external resource or a slow I/O operation
    print("Mock I/O-bound operation completed.")

def _data_formatting(data: List[float]) -> float:
    """
    Performs a computation to processes the data.
    """
    intermediate_result = 0.0
    length_of_data = len(data)
    if length_of_data > 0:
        for _ in range(100000):
            factor = math.sqrt(sum(x**2 for x in data)) if data else 0
            intermediate_result += factor * 0.1
    return intermediate_result

def preprocessing_operations(data: List[float]) -> str:
    """Pre-processing the data for the model, via two independent steps."""

    print(f"Performing preprocessing operation on: {data}")

    _mock_io_bound_operation()

    final_result = _data_formatting(data)

    result = str(final_result)
    print(f"Preprocessing operation completed with final result: {result}")
    return result
