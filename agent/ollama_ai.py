import json
import urllib.request
from urllib.error import HTTPError, URLError

from .config import OLLAMA_MODEL, OLLAMA_URL


def _chat(system: str, user: str) -> str:
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        return data["message"]["content"].strip()
    except HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            msg = json.loads(body).get("error", body)
        except Exception:
            msg = body
        if "not found" in msg.lower():
            raise RuntimeError(
                f"Ollama model '{OLLAMA_MODEL}' not installed — run: ollama pull {OLLAMA_MODEL}"
            ) from e
        raise RuntimeError(f"Ollama error: {msg}") from e
    except URLError as e:
        raise RuntimeError(f"Ollama unreachable at {OLLAMA_URL} — is it running?") from e


def classify_spam(sender: str, text: str) -> bool:
    result = _chat(
        'You are a spam classifier. Reply with exactly "spam" or "not spam" — nothing else.',
        f"Sender: {sender}\nMessage: {text}",
    )
    return result.lower().startswith("spam")


def draft_reply(sender: str, message: str) -> str:
    return _chat(
        "You are a personal assistant drafting replies on behalf of Viraj. "
        "Write a brief, natural reply. Output only the reply text, nothing else.",
        f"From: {sender}\nMessage: {message}",
    )
