Adaptive Data Transfer Engine

A Python distributed data-transfer engine for reliable, high-performance multi-GB file transfers over TCP. The system combines asynchronous I/O, parallel streaming, resumable transfers, retries, integrity validation, adaptive networking, and network performance testing.

What it demonstrates

Distributed Systems: sender, receiver, and control-plane services

Networking: TCP/IP, sockets, client-server communication, RTT, throughput, bandwidth, packet loss

Reliability: resumable transfers, retries with exponential backoff, SHA-256 integrity validation

Concurrency: asyncio and parallel streaming for concurrent transfers

Adaptive Performance: adjusts application-level chunk size using measured network conditions

Linux Networking: tc/netem for controlled latency and packet-loss experiments

QA & Testing: 40+ tests with 90%+ coverage and performance benchmarks

Architecture

              ┌─────────────────────┐
              │    Control Plane    │
              │ transfer + metrics  │
              └──────────┬──────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
┌─────────────────┐             ┌─────────────────┐
│     Sender      │   TCP/IP    │    Receiver     │
│  asyncio client │────────────►│ async TCP server│
│ adaptive chunks │◄────────────│ resume + SHA256 │
└─────────────────┘             └─────────────────┘

The project uses a custom application-level protocol over TCP for transfer setup, resume offsets, PING/PONG RTT measurement, final hashes, and transfer status.

Core Workflow

Measure RTT
    ↓
Select chunk size
    ↓
START_TRANSFER
    ↓
Resume from existing offset
    ↓
Parallel / async streaming
    ↓
Incremental SHA-256
    ↓
FINAL_HASH
    ↓
Integrity verification

Adaptive Transfer

The engine uses RTT, bandwidth, throughput, and packet-loss metrics to adapt application-level transfer behavior.

Experiments target:

50–200 ms RTT

1–5% packet loss

Linux tc/netem is used to reproduce controlled network conditions and benchmark transfer behavior.

Reliability

Resumable transfers use server-side .part files so interrupted transfers can continue from the last received offset instead of restarting.

SHA-256 validation is calculated incrementally on both client and server to verify end-to-end file integrity.

Retries use capped exponential backoff for transient connection failures.

QA & Performance

The project includes:

40+ automated tests

90%+ test coverage

Unit + integration testing

Failure/retry/resume validation

Performance benchmarks across varied network conditions

RTT and throughput measurements logged to results.csv

Run the test suite:

python -m pytest -q

Deployment

The sender, receiver, and control-plane services are designed for containerized deployment using:

Docker → Kubernetes

This provides an environment for distributed execution, service isolation, and repeatable network-performance experiments.

Tech Stack

Python • asyncio • TCP/IP • Linux • tc/netem • Docker • Kubernetes • pytest • SHA-256 • Git

Repository Structure

adaptive.py
transfer_client.py
transfer_server_async.py
protocol.py
integrity.py
retry.py
metrics.py
netem_scripts.sh
results.csv
tests/

Resume Summary

Built a Python distributed data-transfer engine with asyncio, TCP sockets, parallel streaming, resumable transfers, retries, and SHA-256 validation, supporting multi-GB file transfers.

Optimized transfers using RTT, bandwidth, throughput, and packet-loss metrics, adapting chunk size and concurrency across 50–200 ms RTT and 1–5% packet loss with Linux tc/netem.

Deployed sender, receiver, and control-plane services using Docker and Kubernetes, with 40+ tests, 90%+ coverage, and performance benchmarks across varied network conditions.
