# Bonsai 27B Model Download & Benchmark Preparation Status — 2026-08-25

**Date:** 2026-08-25  
**Tag / Package:** `MichelRosselli/bonsai-27b:latest`  
**Ollama Image Hash:** `69db21d6b602`  
**Size on Disk:** 4.4 GB  

---

## 1. Overview & Architecture

* **Base Model:** Qwen3.6-27B (multimodal, hybrid-attention architecture)
* **Quantization Scheme:** Low-bit (1-bit / ternary weight format) paired with a Q8_0 vision projector.
* **Context Window Support:** Up to 262,144 tokens (262K).
* **Capabilities:** Text reasoning, multimodal vision processing, structured tool calling.

---

## 2. Local Environment Setup

* **Engine:** Ollama (local GPU/CPU mesh)
* **Download Status:** ✅ Complete (`success` verified)
* **Registration:** Model manifest created and available under `MichelRosselli/bonsai-27b:latest` via local `ollama list`.

---

## 3. Benchmark Staging & Next Steps

* **Status:** Staged and ready for testing.
* **Benchmark Plan (Pending Execution):**
  1. **Station Bench / Discrimination:** Evaluate accuracy on synthetic/gold-labeled decision stations.
  2. **Latency & VRAM Profiling:** Measure inference speed (tokens/sec) and memory pressure under load.
  3. **Multimodal / Vision Verification:** Test vision projection integration.
* **Execution Directive:** Benchmark checks are currently **on hold** pending user signal.
