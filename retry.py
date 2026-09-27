import asyncio


async def retry(
    operation,
    retries=4,
    base_delay=1,
    max_delay=8,
):

    for attempt in range(retries):

        try:

            return await operation()

        except (
            ConnectionError,
            asyncio.IncompleteReadError,
        ) as e:

            if attempt == retries - 1:

                raise

            delay = min(
                base_delay * (2 ** attempt),
                max_delay,
            )

            print(
                f"Transfer failed: {e}"
            )

            print(
                f"Retrying in {delay} second(s)... "
                f"(attempt "
                f"{attempt + 2}/{retries})"
            )

            await asyncio.sleep(
                delay
            )

    raise RuntimeError(
        "Retry logic failed unexpectedly"
    )