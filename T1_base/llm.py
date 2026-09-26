# Cliente Gemini: llamadas stateless con streaming, watchdog y reintentos acotados por deadline.
from __future__ import annotations

import logging
import os
import random
import re
import time
from dataclasses import dataclass, field

import httpx
from google import genai
from google.genai import errors, types

MODEL = "gemini-3.5-flash-lite"
# MODEL = "gemini-3.1-flash-lite"
RETRYABLE_CODES = {408, 429, 500, 502, 503, 504}
MIN_USEFUL_SECONDS = 10.0

logging.getLogger("google_genai").setLevel(logging.ERROR)


# Fallo definitivo de la llamada, sin más reintentos posibles.
class LLMError(Exception):
    pass


# No queda tiempo suficiente para intentar una llamada.
class LLMBudgetExceeded(LLMError):
    pass


# La llamada completa excedió el tope de tiempo propio.
class CallTimeout(Exception):
    pass


# Texto devuelto por el modelo más métricas de la llamada.
@dataclass
class LLMResult:
    text: str
    latency: float
    first_token_latency: float | None
    attempts: int
    prompt_tokens: int | None = None
    output_tokens: int | None = None
    finish_reason: str | None = None
    events: list[str] = field(default_factory=list)


# Envuelve google-genai con timeouts propios y reintentos.
class LLMClient:
    pass

    # Crea el cliente con el timeout de lectura (watchdog) y la cabecera de timeout del servidor.
    def __init__(self, model: str = MODEL, first_token_timeout: float = 9.0,
                 call_timeout: float = 35.0, max_attempts: int = 4, verbose: bool = True):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise LLMError("No se encontró GEMINI_API_KEY en el entorno.")
        self.model = model
        self.first_token_timeout = first_token_timeout
        self.call_timeout = call_timeout
        self.max_attempts = max_attempts
        self.verbose = verbose
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=int(first_token_timeout * 1000),
                headers={"X-Server-Timeout": str(int(max(10, call_timeout)))},
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )

    # Genera texto reintentando ante timeouts y 5xx, sin pasar el deadline (time.monotonic).
    def generate(self, prompt: str, deadline: float, temperature: float = 0.3,
                 max_output_tokens: int = 6000) -> LLMResult:
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        events: list[str] = []
        t_start = time.monotonic()
        for attempt in range(1, self.max_attempts + 1):
            remaining = deadline - time.monotonic()
            if remaining < MIN_USEFUL_SECONDS:
                raise LLMBudgetExceeded(
                    f"Quedan {remaining:.1f}s; no alcanza para una llamada. Eventos: {events}")
            this_timeout = min(self.call_timeout, remaining - 2.0)
            try:
                text, ftl, usage, finish = self._stream_once(prompt, config, this_timeout)
                res = LLMResult(
                    text=text, latency=time.monotonic() - t_start, first_token_latency=ftl,
                    attempts=attempt, events=events, finish_reason=finish,
                    prompt_tokens=getattr(usage, "prompt_token_count", None),
                    output_tokens=getattr(usage, "candidates_token_count", None),
                )
                self._log(f"LLM ok: intento {attempt}, primer token {ftl:.1f}s, "
                          f"total {res.latency:.1f}s, tokens out {res.output_tokens}")
                return res
            except errors.APIError as e:
                code = getattr(e, "code", None)
                events.append(f"attempt {attempt}: HTTP {code}")
                if code not in RETRYABLE_CODES:
                    raise LLMError(f"Error no reintentable de la API: {e}") from e
                self._log(f"LLM HTTP {code} (intento {attempt}); reintento")
            except (httpx.TimeoutException, httpx.TransportError, CallTimeout) as e:
                events.append(f"attempt {attempt}: {type(e).__name__}")
                self._log(f"LLM {type(e).__name__} (intento {attempt}); reintento")
            remaining = deadline - time.monotonic()
            base = 0.5 if events[-1].endswith(("Timeout", "TimeoutException", "ReadTimeout", "CallTimeout")) \
                else 1.0 * (2 ** (attempt - 1))
            delay = min(base + random.uniform(0, 0.4), max(0.0, remaining - MIN_USEFUL_SECONDS))
            if delay > 0:
                time.sleep(delay)
        raise LLMError(f"Agotados {self.max_attempts} intentos. Eventos: {events}")

    # Un intento en streaming; corta con CallTimeout si el total supera total_timeout.
    def _stream_once(self, prompt: str, config, total_timeout: float):
        t0 = time.monotonic()
        first: float | None = None
        parts: list[str] = []
        usage = None
        finish = None
        stream = self._client.models.generate_content_stream(
            model=self.model, contents=prompt, config=config)
        try:
            for chunk in stream:
                now = time.monotonic()
                if first is None:
                    first = now - t0
                if chunk.text:
                    parts.append(chunk.text)
                if chunk.usage_metadata is not None:
                    usage = chunk.usage_metadata
                if chunk.candidates and chunk.candidates[0].finish_reason:
                    finish = str(chunk.candidates[0].finish_reason)
                if now - t0 > total_timeout:
                    raise CallTimeout(f"llamada > {total_timeout:.0f}s (recibidos {len(parts)} chunks)")
        finally:
            close = getattr(stream, "close", None)
            if close:
                try:
                    close()
                except Exception:
                    pass
        return "".join(parts), first or 0.0, usage, finish

    # Imprime un mensaje del cliente si verbose está activo.
    def _log(self, msg: str):
        if self.verbose:
            print(f"  [llm] {msg}")


_CODE_BLOCK = re.compile(r"```(?:python|py)?[ \t]*\n(.*?)```", re.DOTALL)


# Devuelve el bloque ```python``` más largo de la respuesta, o todo el texto si no hay bloques.
def extract_code(text: str) -> str:
    blocks = _CODE_BLOCK.findall(text)
    if blocks:
        return max(blocks, key=len).strip("\n") + "\n"
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else ""
    return cleaned.rstrip("`").rstrip() + "\n"
