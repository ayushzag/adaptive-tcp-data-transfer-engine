import asyncio
import os

import transfer_client as client
import transfer_server_async as server_module


def test_full_transfer_against_real_async_server(
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
            os.urandom(20000)
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

        transfer_id = (
            "integration-test"
        )

        try:

            await client.transfer_once(
                str(source),
                transfer_id,
                condition="baseline",
                adaptive=True,
            )

            final_path = (
                transfers_dir
                / f"{transfer_id}.bin"
            )

            assert final_path.exists()

            assert (
                final_path.read_bytes()
                == source.read_bytes()
            )

        finally:

            server.close()

            await server.wait_closed()

    asyncio.run(run())


def test_resume_from_existing_partial_file(
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

        data = os.urandom(
            20000
        )

        source.write_bytes(
            data
        )

        transfer_id = (
            "resume-test"
        )

        partial_path = (
            transfers_dir
            / f"{transfer_id}.part"
        )

        partial_path.write_bytes(
            data[:4096]
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

            await client.transfer_once(
                str(source),
                transfer_id,
                condition="baseline",
                adaptive=True,
            )

            final_path = (
                transfers_dir
                / f"{transfer_id}.bin"
            )

            assert (
                final_path.read_bytes()
                == data
            )

        finally:

            server.close()

            await server.wait_closed()

    asyncio.run(run())