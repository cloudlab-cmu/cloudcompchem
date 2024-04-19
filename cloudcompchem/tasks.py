import time

from celery import shared_task


@shared_task(ignore_result=False)
def add_together(a: int, b: int) -> int:
    time.sleep(5)
    return a + b
