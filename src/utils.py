import asyncio
import logging
from typing import Callable


async def retry_with_exponential_backoff(
    task: Callable, max_retries: int = 5, delay: float = 0.5
):
    """Retry a given task with an exponential backoff strategy

    Parameters:
        task (Callable): An asynchronous function
        max_retries (int): The maximum number of times to retry an operation
        delay (float): The delay between each retry, this increases exponentially
    """
    retries = 0
    while retries < max_retries:
        try:
            await task()
            # break from loop on success
            break
        except:
            if retries >= max_retries:
                logger.exception(
                    f"Operation failed after {max_retries} retries", exc_info=True
                )
                # re-raise exception
                raise

            retries += 1

            # sleep for specified duration
            await asyncio.sleep(delay * (2**retries))


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

"""
A custom logger for the Application
"""
logger = logging.getLogger(__name__)
