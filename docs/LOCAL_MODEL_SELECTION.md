# Candidate local model for Calculation

This measured candidate is opt-in and is not approved as a general request parser or quality baseline.

## Candidate and license

- Candidate: Qwen2.5-Coder-1.5B-Instruct, Q4_K_M GGUF via Ollama.
- Local tag: hf.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF:Q4_K_M.
- Publisher model card and license: [Qwen2.5-Coder-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct), Apache-2.0.
- Runtime used for the probe: Ollama 0.40.14, loopback-only at 127.0.0.1:11434, cloud disabled, CPU backend. Python: CPython 3.13.15.
- The model was already in C:\DevData\Codex\agents\local-inference\2026-11-09; it was not downloaded or installed during this issue. No Python dependency was added.

## Measurement on 2026-11-10

The adapter performed real local generation. A direct model probe with the clear synthetic request “Calcule 2 elevado a 5” returned a redundant clarification asking for the base and exponent. This was a probe of the model itself; the runtime now handles that explicit syntax deterministically before invoking the model. In a separate end-to-end runtime probe, “Calcule a quinta potencia de dois” reached the model and returned “What is the exponent for the calculation? Is it 5 or 10?”. The runtime preserved that clarification instead of returning an inferred answer. The process round trip took 4,692 ms on this CPU-only setup, including Python startup. Together, these observations show that the 1.5B coding model is not reliable enough for general math-language parsing.

The bounded deterministic parser handled explicit percentage and power forms, and the numeric engine returned exact results. These are hand-checked behavior tests, not model quality scores, baseline measurements, or evidence of improvement. The model stays opt-in for less explicit requests; malformed, unavailable, or unsupported responses do not trigger a guess or remote fallback.

## Runtime limits

Structured arithmetic, rational roots, a bounded unit table, and single-variable rational polynomials execute without a model call. Symbolic operations outside the implemented polynomial/linear subset return an explicit unsupported or insufficient-data result. The unit table is finite and case-sensitive. A model's proposed operation is validated against the contract before execution.

Inference uses loopback only and bounds prompt size, context, output tokens, one concurrent request, and time. The client cannot enforce a hard memory limit on the Ollama service. Cancellation suppresses an in-flight result after the call or timeout; it cannot forcibly stop Ollama.
