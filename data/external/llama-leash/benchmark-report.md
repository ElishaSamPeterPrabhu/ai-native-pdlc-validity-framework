# Local model benchmark report

Generated 2026-08-30T15:29:03Z

## Host

```
chip            Apple M4 Pro (20 GPU cores)
memory          24 GiB total, Metal budget 19 GB (macOS default (75% of RAM))
cpu             14 cores (10P + 4E)
mem bandwidth   121.5 GB/s single-thread, 228.0 GB/s at 14 threads (CPU-side ceiling; see llama-bench tg for what predicts tok/s)
disk read       6.9 GB/s [page cache warm] (measured)
power           battery
```

### Full specifications

| property | value |
|---|---|
| `cacheline_bytes` | 128 |
| `chip` | Apple M4 Pro |
| `cpu_cores_efficiency` | 4 |
| `cpu_cores_performance` | 10 |
| `cpu_cores_total` | 14 |
| `cpu_freq_hz_nominal` | None |
| `gpu_cores` | 20 |
| `gpu_name` | Apple M4 Pro |
| `iogpu_wired_limit_mb` | 0 |
| `l2_cache_bytes` | 4194304 |
| `machine` | arm64 |
| `metal_budget_bytes` | 19327352832 |
| `metal_budget_source` | macOS default (75% of RAM) |
| `metal_support` | spdisplays_metal4 |
| `model` | Mac16,7 |
| `os` | macOS-26.6.2-arm64-arm-64bit-Mach-O |
| `page_size` | 16384 |
| `python` | 3.13.3 |
| `ram_bytes` | 25769803776 |

### Measured host throughput

| measurement | value | note |
|---|--:|---|
| memory copy (single-thread) | 121.5 GB/s | NOT peak bandwidth - relative indicator only |
| disk sequential read | 6.9 GB/s | page cache warm |
| cpu single-thread | 25.4M ops/s | python integer loop |

### Machine state (throttling check)

| | before | after |
|---|---|---|
| power_source | battery | battery |
| battery | -InternalBattery-0 (id=35455075)	62%; discharging; 4:36 remaining present: true | -InternalBattery-0 (id=35455075)	13%; discharging; 0:10 remaining present: true |

## Results

### Summary by model

| model | category | quant | presets | best objective | best tok/s |
|---|---|---|--:|--:|--:|
| `ornith-9b` | coding | Q4_K_M | 10 | 100% | 37.2 |

### `ornith-9b`

| preset | objective | gen tok/s | prompt tok/s | wall s | SELF-graded | calibration |
|---|--:|--:|--:|--:|--:|--:|
| `author-default` | 100% (12/12) | 32.3 | 207.6 | 38.0 | 100 | +0 |
| `deterministic` | 100% (12/12) | 32.6 | 283.8 | 47.7 | 100 | +0 |
| `balanced-chat` | 100% (12/12) | 32.6 | 283.7 | 37.5 | 100 | +0 |
| `min-p` | 100% (12/12) | 32.7 | 264.3 | 48.8 | 100 | +0 |
| `high-creative` | 100% (12/12) | 37.2 | 316.1 | 27.8 | - | - |
| `kv-q4` | 100% (12/12) | 31.0 | 245.2 | 44.0 | 100 | +0 |
| `long-context` | 100% (12/12) | 31.0 | 284.2 | 39.3 | 100 | +0 |
| `kv-q8` | 100% (12/12) | 32.0 | 282.1 | 38.1 | 100 | +0 |
| `flash-attn-off` | 100% (12/12) | 31.4 | 275.4 | 38.9 | 100 | +0 |
| `metal-throughput` | 100% (12/12) | 30.3 | 283.6 | 40.2 | 100 | +0 |

Perplexity (lower is better - measures how much each runtime config degrades the model):

| preset | perplexity |
|---|--:|
| `author-default` | 3.6525 |
| `deterministic` | 3.6525 |
| `balanced-chat` | 3.6525 |
| `min-p` | 3.6525 |
| `high-creative` | 3.6525 |
| `kv-q4` | 3.6614 |
| `kv-q8` | 3.6524 |
| `flash-attn-off` | 3.6525 |
| `metal-throughput` | 3.6525 |

## How to read this

- **objective** - executed unit tests, documentation symbol coverage, or retrieval recall@1. This is the only trustworthy quality column.
- **SELF-graded** - the model scoring *its own* output. It is NOT an independent measure and must not be read as one.
- **calibration** - `self_score - objective`. Positive means the model over-rated itself; near zero means it can tell when it is wrong. This is arguably more interesting than the self score itself.
- **perplexity** - objective, judge-free measure of quantization and KV-cache damage.

## Categories not benchmarked

- **image-generation** - llama.cpp cannot generate images. FLUX.1/FLUX.2, SD3.5 and Qwen-Image all ship GGUF weights, but they run in stable-diffusion.cpp - a separate engine. Adding it as a second submodule would make this category real; until then vision models are scored on interpretation.
- **music** - No music/beat generation model exists in the GGUF ecosystem, and llama.cpp has no music architecture. The MusicGen GGUF repos on HuggingFace target other runtimes and are unmaintained. Speech synthesis IS supported (see the audio category, arch qwen3tts).

## Presets

### `author-default`

The model author's published sampling settings on a stock Metal runtime. This is the control - every other preset is read as a delta from here.

- runtime: `{"n-gpu-layers": "999", "flash-attn": "auto", "cache-type-k": "f16", "cache-type-v": "f16", "batch-size": "2048", "ubatch-size": "512"}`
- sampling: `<author-recommended>`

### `deterministic`

Greedy decoding (temp 0). The standard choice for code and for any run that has to be reproducible.

- runtime: `{"n-gpu-layers": "999", "flash-attn": "auto", "cache-type-k": "f16", "cache-type-v": "f16", "batch-size": "2048", "ubatch-size": "512"}`
- sampling: `{"temp": "0", "top-k": "1", "seed": "1234"}`

### `metal-throughput`

Flash attention forced on with a large micro-batch. Targets peak prompt-processing and generation throughput on M-series GPUs.

- runtime: `{"n-gpu-layers": "999", "flash-attn": "on", "cache-type-k": "f16", "cache-type-v": "f16", "batch-size": "4096", "ubatch-size": "1024"}`
- sampling: `<author-recommended>`

### `flash-attn-off`

Identical to metal-throughput but with flash attention disabled - isolates exactly what FA is worth on this hardware.

- runtime: `{"n-gpu-layers": "999", "flash-attn": "off", "cache-type-k": "f16", "cache-type-v": "f16", "batch-size": "4096", "ubatch-size": "1024"}`
- sampling: `<author-recommended>`

### `kv-q8`

8-bit KV cache. Roughly halves cache memory; the community consensus is that quality loss is near-zero. This preset tests that claim on real output.

- runtime: `{"n-gpu-layers": "999", "flash-attn": "on", "cache-type-k": "q8_0", "cache-type-v": "q8_0", "batch-size": "2048", "ubatch-size": "512"}`
- sampling: `<author-recommended>`

### `kv-q4`

4-bit KV cache - quarter the cache memory. Expected to cost real quality; quantifies whether the memory saving is worth it.

- runtime: `{"n-gpu-layers": "999", "flash-attn": "on", "cache-type-k": "q4_0", "cache-type-v": "q4_0", "batch-size": "2048", "ubatch-size": "512"}`
- sampling: `<author-recommended>`

### `long-context`

4x the default context with an 8-bit KV cache, the usual recipe for large-repo work. Measures degradation as context grows.

- runtime: `{"n-gpu-layers": "999", "flash-attn": "on", "cache-type-k": "q8_0", "cache-type-v": "q8_0", "batch-size": "2048", "ubatch-size": "512", "ctx-size": "131072"}`
- sampling: `<author-recommended>`

### `balanced-chat`

temp 0.7 / top-p 0.8 / top-k 20 - the widely used general-purpose middle ground, and Qwen's published chat default.

- runtime: `{"n-gpu-layers": "999", "flash-attn": "auto", "cache-type-k": "f16", "cache-type-v": "f16", "batch-size": "2048", "ubatch-size": "512"}`
- sampling: `{"temp": "0.7", "top-p": "0.8", "top-k": "20", "seed": "1234"}`

### `min-p`

min-p sampling (min-p 0.05, top-p/top-k disabled). The min-p school argues this beats top-p for coherence at equal diversity.

- runtime: `{"n-gpu-layers": "999", "flash-attn": "auto", "cache-type-k": "f16", "cache-type-v": "f16", "batch-size": "2048", "ubatch-size": "512"}`
- sampling: `{"temp": "0.8", "min-p": "0.05", "top-p": "1.0", "top-k": "0", "seed": "1234"}`

### `high-creative`

temp 1.0 / top-p 0.95 / top-k 64 - Gemma's published default and the usual setting for prose. Expected to help writing and hurt code.

- runtime: `{"n-gpu-layers": "999", "flash-attn": "auto", "cache-type-k": "f16", "cache-type-v": "f16", "batch-size": "2048", "ubatch-size": "512"}`
- sampling: `{"temp": "1.0", "top-p": "0.95", "top-k": "64", "seed": "1234"}`

