# Contributing

## Development Workflow
- Use `Justfile` commands as the single entrypoint:
  - `just fmt`
  - `just lint`
  - `just typecheck`
  - `just test`
  - `just check` (required before commit/push)

## PoW Registration Bench Notes

These measurements are reference-only and were captured on one environment with
`AGENT_REGISTER_POW_BITS=24`. Real time is stochastic and can vary a lot per run.

### PoW Results: Python vs Node.js

| Run | Python (tries / time) | Node.js (tries / time) |
| --- | --- | --- |
| 1 | 10.6M / 6.6s | 10.2M / 12.7s |
| 2 | 46.6M / 29.4s | 6.5M / 8.1s |
| 3 | 1.9M / 1.4s | 45.9M / 65.1s |

### Hashrate (tries/sec)

|  | Python | Node.js |
| --- | --- | --- |
| Run 1 | ~1.6M/s | ~0.8M/s |
| Run 2 | ~1.6M/s | ~0.8M/s |
| Run 3 | ~1.3M/s | ~0.7M/s |
| Average | ~1.5M hash/s | ~0.75M hash/s |

### Interpretation
- PoW solve time has high variance even with fixed bits.
- Python was faster than Node.js in this sample.
- For operational tuning, adjust `AGENT_REGISTER_POW_BITS` using observed
  registration latency under your actual traffic and hardware.

### Difficulty Scaling (Reference)

| Difficulty | Expected hashes | Python (~2M/s) | C 16 threads (~200M/s) |
| --- | --- | --- | --- |
| 24 bits | 16.7M | 8 sec | 0.08 sec |
| 28 bits | 268M | 2 min | 1.3 sec |
| 32 bits | 4.3B | 36 min | 21 sec |
| 36 bits | 68.7B | 9.5 hours | 5.7 min |
| 40 bits | 1.1T | 6.4 days | 1.5 hours |

Every +4 bits increases expected solve time by x16. At 40 bits, even strong
hardware becomes expensive, while scripting-language clients become practically
unusable for normal onboarding flows.
