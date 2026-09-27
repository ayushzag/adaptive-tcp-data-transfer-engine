import asyncio

from protocol import (
    FINAL_HASH,
    PING,
    PONG,
    RESUME_OFFSET,
    START_TRANSFER,
    STATUS_OK,
    pack_final_hash,
    pack_ping,
    pack_resume_offset,
    pack_status,
    pack_transfer_start,
    read_final_hash,
    read_transfer_start,
    unpack_pong,
    unpack_resume_offset,
    unpack_status,
)


def test_transfer_start_round_trip():
    message = pack_transfer_start(
        "abc123",
        12345
    )

    assert message[0] == START_TRANSFER


def test_resume_offset_round_trip():
    message = pack_resume_offset(
        4096
    )

    assert message[0] == RESUME_OFFSET

    assert unpack_resume_offset(
        message
    ) == 4096


def test_status_round_trip():
    message = pack_status(
        STATUS_OK
    )

    assert unpack_status(
        message
    ) == STATUS_OK


def test_ping_pong():
    assert pack_ping() == bytes([PING])

    assert unpack_pong(
        bytes([PONG])
    ) is True


def test_final_hash_round_trip():
    digest = "a" * 64

    message = pack_final_hash(
        digest
    )

    assert message[0] == FINAL_HASH


def test_read_transfer_start_with_split_header():

    async def run():

        reader = asyncio.StreamReader()

        message = pack_transfer_start(
            "split-id",
            5000
        )

        reader.feed_data(
            message[:1]
        )

        reader.feed_data(
            message[1:5]
        )

        reader.feed_data(
            message[5:]
        )

        reader.feed_eof()

        transfer_id, file_size = (
            await read_transfer_start(
                reader
            )
        )

        assert transfer_id == "split-id"
        assert file_size == 5000

    asyncio.run(run())


def test_read_final_hash():

    async def run():

        digest = "b" * 64

        reader = asyncio.StreamReader()

        reader.feed_data(
            pack_final_hash(
                digest
            )
        )

        reader.feed_eof()

        assert (
            await read_final_hash(
                reader
            )
            == digest
        )

    asyncio.run(run())