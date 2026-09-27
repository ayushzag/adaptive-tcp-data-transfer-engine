# Adaptive TCP Data Transfer Engine

A small, reliability-focused TCP file transfer engine built in Python for networking, performance troubleshooting, reliability, and QA experimentation.

The project was intentionally kept small enough to explain and defend line-by-line in a technical interview.

---

## Project Goal

The main goal of the project is to build and understand a TCP-based file transfer system while exploring:

- TCP socket programming
- Application-level protocol framing
- Async I/O with `asyncio`
- Concurrent client handling
- Resumable file transfer
- SHA-256 integrity validation
- Retry with exponential backoff
- RTT measurement
- Throughput measurement
- Controlled network impairment
- RTT-based adaptive behavior
- Automated testing
- Failure handling and debugging

---

## Architecture

```text
                         TCP Connection
        ┌──────────────────────────────────────────┐
        │                                          │
        ▼                                          ▼

┌──────────────────────┐              ┌────────────────────────┐
│  transfer_client.py  │              │ transfer_server_async  │
│                      │              │                        │
│  1. Connect          │              │  1. Accept client      │
│  2. RTT probe        │              │  2. PING -> PONG        │
│  3. Adaptive choice  │              │  3. Read transfer info │
│  4. Start transfer   │              │  4. Check .part file   │
│  5. Resume offset    │              │  5. Return offset      │
│  6. Stream file      │              │  6. Receive chunks     │
│  7. SHA-256          │              │  7. SHA-256            │
│  8. Send final hash  │              │  8. Verify hash        │
│  9. Receive status   │              │  9. Rename .part file  │
│ 10. Save metrics     │              │ 10. Return status      │
└──────────────────────┘              └────────────────────────┘
```

---

## Main Components

### `transfer_client.py`

Responsible for:

- TCP connection establishment
- RTT measurement using PING/PONG
- Adaptive chunk-size selection
- File streaming
- Resume support
- Incremental SHA-256 hashing
- Retry handling
- Throughput measurement
- Results logging

### `transfer_server_async.py`

Responsible for:

- Asynchronous TCP server
- Handling incoming client connections
- PING/PONG response
- Resume-offset calculation
- Partial file storage
- Incremental SHA-256 hashing
- Integrity verification
- Final file creation

### `protocol.py`

Contains the custom application-level protocol.

It defines:

- Message types
- Status codes
- Binary message formats
- Packing/unpacking helpers
- Transfer-start messages
- Resume-offset messages
- Final-hash messages
- Transfer-status messages
- PING/PONG messages

TCP provides a byte stream rather than application-level message boundaries, so the application defines its own framing and fixed binary structures.

### `integrity.py`

Provides incremental SHA-256 hashing using:

```python
hashlib.sha256()
```

The file is hashed incrementally rather than loading the entire file into memory.

### `retry.py`

Implements capped exponential backoff.

The retry delay grows as:

```text
1s
2s
4s
8s
```

with a configured maximum delay.

### `metrics.py`

Responsible for:

- High-resolution duration measurement
- Throughput calculation
- Writing benchmark results to `results.csv`

### `adaptive.py`

Contains the Day-6 adaptive rule.

The rule chooses one application-level chunk size based on the measured RTT.

---

# Protocol

TCP is a byte-stream protocol.

That means one call to `send()` or `writer.write()` does not automatically correspond to one call to `recv()` or `reader.read()`.

The project therefore uses an application-level protocol.

## Message Flow

```text
Client                              Server
  |                                   |
  |---------- PING ------------------>|
  |<--------- PONG -------------------|
  |                                   |
  |------ START_TRANSFER ------------>|
  |                                   |
  |<------ RESUME_OFFSET -------------|
  |                                   |
  |=========== File Data ============>|
  |                                   |
  |-------- FINAL_HASH -------------->|
  |                                   |
  |<------- TRANSFER_STATUS ----------|
  |                                   |
```

---

# Resume Mechanism

The server stores incomplete transfers using a `.part` file.

For example:

```text
transfers/
    abc123.part
```

When the client reconnects using the same transfer ID:

```text
Client
   |
   | START_TRANSFER
   v
Server
   |
   | Check existing .part file
   |
   | Existing size = N bytes
   v
Client
   |
   | RESUME_OFFSET = N
   v
Client seeks to N
   |
   | Send remaining bytes
   v
Server
```

The server appends the remaining data instead of starting again from zero.

After the transfer completes successfully and the SHA-256 hashes match, the `.part` file is renamed to the final `.bin` file.

---

# SHA-256 Integrity Validation

Both client and server calculate SHA-256 incrementally while processing the file.

The client:

```text
read chunk
   ↓
hash chunk
   ↓
send chunk
```

The server:

```text
receive chunk
   ↓
write chunk
   ↓
hash chunk
```

At the end:

```text
Client SHA-256
       |
       | compare
       v
Server SHA-256
```

If the hashes match, the transfer is accepted.

If the hashes differ, the server reports a checksum mismatch.

---

# Retry Mechanism

Transient connection failures are handled using exponential backoff.

Example:

```text
Attempt 1
   ↓
failure
   ↓
wait 1 second
   ↓
Attempt 2
   ↓
failure
   ↓
wait 2 seconds
   ↓
Attempt 3
   ↓
failure
   ↓
wait 4 seconds
```

The maximum delay is capped.

This prevents repeated immediate retries from continuously hammering a server during a temporary failure.

---

# RTT Measurement

Before the actual file transfer, the client sends:

```text
PING
```

The server responds:

```text
PONG
```

The client measures the time between the two application-level messages.

Conceptually:

```text
Client                         Server

   PING ------------------------>
       start timer

                  PONG <---------

       stop timer
```

The measured value is used by the adaptive component.

---

# Throughput Measurement

Application throughput is calculated using:

```text
bytes_transferred × 8
---------------------
duration_seconds × 1,000,000
```

The result is recorded in Mbps.

The project stores measurements in:

```text
results.csv
```

Each successful experiment records:

- timestamp
- condition
- transfer ID
- file size
- resume offset
- bytes transferred
- duration
- throughput
- RTT

---

# Network Performance Experimentation

Day 5 focused on measuring the transfer under controlled network conditions using `tc/netem`.

The tested conditions were:

- Baseline
- 50 ms Delay
- 1% Packet Loss
- 50 ms Delay + 1% Packet Loss

The experiments were repeated multiple times and the final cleaned dataset contains 12 valid readings: 3 runs per condition.

---

# Final Benchmark Results

## Baseline

| Run | Duration (s) | Throughput (Mbps) | RTT (ms) |
|---|---:|---:|---:|
| 1 | 0.493755 | 1698.940 | 3.879 |
| 2 | 0.889862 | 942.687 | 6.156 |
| 3 | 1.128570 | 743.295 | 5.569 |

Median:

```text
Throughput = 942.687 Mbps
RTT        = 5.569 ms
```

## 50 ms Delay

| Run | Duration (s) | Throughput (Mbps) | RTT (ms) |
|---|---:|---:|---:|
| 1 | 4.022214 | 208.557 | 114.260 |
| 2 | 3.936550 | 213.095 | 113.867 |
| 3 | 3.940368 | 212.889 | 112.663 |

Median:

```text
Throughput = 212.889 Mbps
RTT        = 113.867 ms
```

## 1% Packet Loss

| Run | Duration (s) | Throughput (Mbps) | RTT (ms) |
|---|---:|---:|---:|
| 1 | 0.742136 | 1130.334 | 2.846 |
| 2 | 0.902075 | 929.923 | 2.525 |
| 3 | 0.828363 | 1012.673 | 2.430 |

Median:

```text
Throughput = 1012.673 Mbps
RTT        = 2.525 ms
```

## 50 ms Delay + 1% Packet Loss

| Run | Duration (s) | Throughput (Mbps) | RTT (ms) |
|---|---:|---:|---:|
| 1 | 13.554230 | 61.889 | 441.383 |
| 2 | 9.119265 | 91.988 | 110.172 |
| 3 | 8.267988 | 101.459 | 117.753 |

Median:

```text
Throughput = 91.988 Mbps
RTT        = 117.753 ms
```

---

# Adaptive Behavior

Day 5 measurements showed a clear separation between normal and delayed RTT conditions.

Measured median RTT:

```text
Baseline
5.569 ms

50 ms Delay
113.867 ms

1% Packet Loss
2.525 ms

50 ms Delay + 1% Loss
117.753 ms
```

Based on those measurements, Day 6 introduced one simple adaptive rule.

## Adaptive Rule

```text
RTT < 50 ms
    ↓
4 KB application chunk

RTT >= 50 ms
    ↓
256 KB application chunk
```

The rule is implemented in:

```text
adaptive.py
```

The decision is made once at the beginning of the transfer.

Example:

```text
Application RTT: 1.379 ms
Adaptive mode: ON
Adaptive decision:
chunk_size=4096 bytes (4 KB)
reason=RTT < 50 ms
```

The chunk size is an application-level file read/write size.

It is not the TCP packet or TCP segment size.

---

# Adaptive Mode vs Fixed Mode

Adaptive mode is enabled by default.

Run:

```bash
python transfer_client.py test_large.bin --condition baseline
```

To disable adaptive behavior:

```bash
python transfer_client.py test_large.bin --condition baseline --no-adaptive
```

When adaptive mode is disabled, the client uses the normal fixed chunk size.

---

# Testing and QA

The project includes an automated test suite using `pytest`.

The tests cover:

## Adaptive Unit Tests

- Low RTT decision
- High RTT decision
- Threshold boundary
- Invalid negative RTT

## Protocol Tests

- Transfer-start messages
- Resume-offset messages
- Status messages
- PING/PONG
- Final hash messages
- Split header handling

## Integration Tests

- Real localhost async TCP server
- Complete file transfer
- Resume from an existing partial file

## Failure Tests

- Refused connection
- Corrupted checksum

Run:

```bash
python -m pytest -q
```

Expected result:

```text
15 passed
```

---

# Failure and Debugging Workflow

The project follows a structured debugging process:

```text
Symptom
   ↓
Evidence
   ↓
Hypothesis
   ↓
Test
   ↓
Root Cause
   ↓
Fix
   ↓
Validation
```

The same approach can be used for:

- Connection failures
- Partial transfers
- Checksum mismatches
- Resume bugs
- Throughput degradation
- RTT changes
- Test failures

---

# Running the Project

## 1. Activate the virtual environment

```bash
source .venv/bin/activate
```

## 2. Run the tests

```bash
python -m pytest -q
```

## 3. Start the server

Open one terminal:

```bash
python transfer_server_async.py
```

The server listens on:

```text
127.0.0.1:5050
```

## 4. Run a normal transfer

Open another terminal:

```bash
python transfer_client.py test_large.bin --condition baseline
```

## 5. Run without adaptive behavior

```bash
python transfer_client.py test_large.bin --condition baseline --no-adaptive
```

## 6. Test checksum corruption

```bash
python transfer_client.py test_large.bin --corrupt
```

## 7. Test interruption and resume

```bash
python transfer_client.py test_large.bin --fail-after 100
```

Then rerun using the same transfer ID to allow the server to resume from the existing partial file.

---

# Project Structure

```text
Adaptive TCP Data Transfer Engine/
│
├── adaptive.py
├── integrity.py
├── metrics.py
├── protocol.py
├── retry.py
├── transfer_client.py
├── transfer_server_async.py
│
├── results.csv
├── requirements.txt
├── test.txt
├── test_large.bin
│
├── transfers/
│
└── tests/
    ├── test_adaptive.py
    ├── test_failures.py
    ├── test_protocol.py
    └── test_transfer.py
```

---

# Known Limitations

- The adaptive algorithm uses a single RTT probe at the beginning of a transfer.
- The adaptive logic currently changes only the application-level chunk size.
- The threshold is intentionally simple and based on the measured Day-5 conditions.
- The benchmark was performed in a controlled local environment.
- The project does not implement machine-learning-based network optimization.
- The project does not attempt to replace TCP congestion control.
- The current protocol is designed for this single-file transfer workflow rather than a general multi-file transfer protocol.

---

# What This Project Demonstrates

This project brings together practical concepts from:

### Computer Networks

- TCP
- TCP byte streams
- RTT
- Throughput
- Packet loss
- Network delay
- Client-server communication

### Python

- `asyncio`
- sockets and streams
- exception handling
- file I/O
- `hashlib`
- structured binary data with `struct`

### Reliability

- Resume support
- Partial files
- SHA-256 integrity verification
- Retry with exponential backoff

### Linux / Networking

- `tc`
- `netem`
- `ss`
- network impairment experiments

### QA

- Unit testing
- Integration testing
- Negative testing
- Failure testing
- Regression testing

---

# Interview Talking Points

The project is designed to support discussion around:

- Why TCP is a byte-stream protocol
- Why application-level framing is necessary
- Why `readexactly()` is useful for fixed protocol fields
- Why a receiver must not assume one send equals one receive
- How `asyncio` provides concurrency for I/O-bound work
- How resume offsets work
- Why hashing is done incrementally
- Why retry uses exponential backoff
- How RTT differs from throughput
- How packet loss and delay affect transfer behavior
- How controlled network impairment can be used during testing
- Why integration tests can catch issues that mocked tests cannot
- Why negative tests are important
- How an adaptive rule can be derived from measured evidence

---

# Final Project Philosophy

The project follows:

```text
LEARN
  ↓
CODE
  ↓
REVIEW
  ↓
FIX
  ↓
UNDERSTAND
  ↓
PROCEED
```

The objective is not to build a feature-heavy product.

The objective is to have a small networking system whose:

- protocol,
- reliability mechanisms,
- performance measurements,
- adaptive behavior,
- tests,
- failure handling,
- and design decisions

can all be explained clearly during a technical interview.
