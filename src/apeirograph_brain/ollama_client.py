import json
from typing import Dict, List, Optional
from urllib import error, request

from apeirograph_brain.settings import OllamaSettings, get_ollama_settings


class OllamaConnectionError(RuntimeError):
    """Raised when the local Ollama runtime cannot be reached reliably."""


class _StdlibResponse:
    def __init__(self, status_code: int, body: bytes):
        self.status_code = status_code
        self._body = body

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise OllamaConnectionError("Ollama returned HTTP {0}".format(self.status_code))

    def json(self) -> Dict[str, object]:
        if not self._body:
            return {}
        return json.loads(self._body.decode("utf-8"))


class _StdlibSession:
    def get(self, url: str, timeout: int) -> _StdlibResponse:
        req = request.Request(url, headers={"Accept": "application/json"})
        try:
            with request.urlopen(req, timeout=timeout) as response:
                return _StdlibResponse(response.getcode(), response.read())
        except (error.URLError, error.HTTPError, OSError) as exc:
            raise OllamaConnectionError(_connection_error_message(url)) from exc

    def post(self, url: str, json: Optional[Dict[str, object]] = None, timeout: int = 30) -> _StdlibResponse:
        payload = json or {}
        data = json_module_dumps(payload)
        req = request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=timeout) as response:
                return _StdlibResponse(response.getcode(), response.read())
        except (error.URLError, error.HTTPError, OSError) as exc:
            raise OllamaConnectionError(_connection_error_message(url)) from exc


def json_module_dumps(payload: Dict[str, object]) -> bytes:
    return json.dumps(payload).encode("utf-8")


def _connection_error_message(url: str) -> str:
    base_url = url.split("/api/", 1)[0]
    return "Unable to reach Ollama at {0}. Make sure the Ollama app is running or start it with 'ollama serve'.".format(base_url)


class OllamaClient:
    def __init__(self, settings: Optional[OllamaSettings] = None, session: Optional[object] = None):
        self.settings = settings or get_ollama_settings()
        self.session = session or _StdlibSession()

    def list_models(self) -> List[str]:
        try:
            response = self.session.get(
                self.settings.base_url + "/api/tags",
                timeout=self.settings.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except OllamaConnectionError:
            raise
        except (error.URLError, error.HTTPError, ValueError, OSError) as exc:
            raise OllamaConnectionError(_connection_error_message(self.settings.base_url + "/api/tags")) from exc
        except Exception as exc:
            raise OllamaConnectionError("Unable to reach the local Ollama runtime.") from exc

        models = payload.get("models", [])
        return [item.get("name", "") for item in models if item.get("name")]

    def is_available(self) -> bool:
        try:
            self.list_models()
            return True
        except OllamaConnectionError:
            return False

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        options: Optional[Dict[str, object]] = None,
    ) -> str:
        if not prompt or not prompt.strip():
            raise ValueError("prompt must not be empty")

        payload: Dict[str, object] = {
            "model": self.settings.model,
            "prompt": prompt.strip(),
            "stream": False,
        }

        if system and system.strip():
            payload["system"] = system.strip()

        if options:
            payload["options"] = options

        try:
            response = self.session.post(
                self.settings.base_url + "/api/generate",
                json=payload,
                timeout=self.settings.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
        except OllamaConnectionError:
            raise
        except (error.URLError, error.HTTPError, ValueError, OSError) as exc:
            raise OllamaConnectionError(_connection_error_message(self.settings.base_url + "/api/generate")) from exc
        except Exception as exc:
            raise OllamaConnectionError("Ollama request failed.") from exc
        text = str(data.get("response", "")).strip()
        if not text:
            raise OllamaConnectionError("Ollama returned an empty response.")

        return text
