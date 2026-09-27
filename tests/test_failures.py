import asyncio
import os
import socket

import transfer_client as client
import transfer_server_async as server_module


def get_unused_port():

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    )

    sock.bind(
        ("127.0.0.1", 0)
    )

    port = (
        sock.getsockname()[1]
    )

    sock.close()

    return port


def test_corrupted_checksum_is_rejected(
    tmp_path,
    monkeypatch,
):

    async def run():

        transfers_dir = (
            tmp_path / "transfers"
        )

        transfers_dir.mkdir()

        monkeypatch.setattr(
            server_module,
            "TRANSFER_DIR",
            transfers_dir,
        )

        monkeypatch.setattr(
            client,
            "append_result",
            lambda **kwargs: None,
        )

        source = (
            tmp_path / "source.bin"
        )

        source.write_bytes(
            os.urandom(10000)
        )

        server = await asyncio.start_server(
            server_module.handle_client,
            "127.0.0.1",
            0,
        )

        port = (
            server.sockets[0]
            .getsockname()[1]
        )

        monkeypatch.setattr(
            client,
            "HOST",
            "127.0.0.1",
        )

        monkeypatch.setattr(
            client,
            "PORT",
            port,
        )

        try:

            try:

                await client.transfer_once(
                    str(source),
                    "corrupt-test",
                    corrupt=True,
                    condition="baseline",
                    adaptive=True,
                )

            except ValueError as exc:

                assert (
                    "Status=1"
                    in str(exc)
                )

            else:

                raise AssertionError(
                    "Checksum corruption "
                    "was not rejected"
                )

            assert not (
                transfers_dir
                / "corrupt-test.bin"
            ).exists()

        finally:

            server.close()

            await server.wait_closed()

    asyncio.run(run())


def test_refused_connection_is_reported(
    tmp_path,
    monkeypatch,
):

    async def run():

        source = (
            tmp_path / "source.bin"
        )

        source.write_bytes(
            b"hello"
        )

        monkeypatch.setattr(
            client,
            "HOST",
            "127.0.0.1",
        )

        monkeypatch.setattr(
            client,
            "PORT",
            get_unused_port(),
        )

        try:

            await client.transfer_once(
                str(source),
                "refused-test",
                condition="baseline",
                adaptive=True,
            )

        except ConnectionRefusedError:

            pass

        else:

            raise AssertionError(
                "ConnectionRefusedError "
                "was expected"
            )

    asyncio.run(run())