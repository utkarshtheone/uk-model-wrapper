import asyncio
import time
import math
from typing import List
from concurrent.futures import ProcessPoolExecutor
from lib.logger import get_logger

logger = get_logger("utils")

# Define a global executor to avoid spawning new processes repeatedly
executor = ProcessPoolExecutor()

async def _mock_io_bound_operation() -> None:
    """
    Simulates an I/O-bound operation with a delay.
    """
    # This delay can be assumed to be unavoidable, and may not be constant in a real world situation.
    logger.debug("Starting mock I/O-bound operation...")
    start = time.time()
    await asyncio.sleep(3)   # Simulate waiting for an external resource or a slow I/O operation
    logger.debug(f"I/O-bound operation completed in {time.time() - start:.2f}s")

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

async def preprocessing_operations(data: List[float]) -> str:
    """ Asynchronously pre-processes data by combining async I/O and parallel CPU execution."""

    logger.info(f"Starting preprocessing for data: {data}")
    start = time.time()

    _mock_io_bound_operation()
    io_end = time.time()

    # Offload CPU-bound task to a separate process
    final_result = await asyncio.get_event_loop().run_in_executor(executor, _data_formatting, data)
    
    end = time.time()
    
    result = str(final_result)
    logger.debug(f"Preprocessing - I/O: {io_end - start:.2f}s, Compute: {end - io_end:.2f}s, Total: {end - start:.2f}s")
    logger.info(f"Preprocessing completed with final result: {result}")
    return result
