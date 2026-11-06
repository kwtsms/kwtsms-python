"""
kwtsms._async: async client for the kwtSMS API.

Requires: pip install kwtsms[async]  (installs aiohttp)

Quick start:
    from kwtsms import AsyncKwtSMS

    async def main():
        sms = AsyncKwtSMS.from_env()
        ok, balance, err = await sms.verify()
        result = await sms.send("965XXXXXXXX", "Your OTP is: 123456")
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import List, Optional, Union

from kwtsms._core import (
    BASE_URL,
    _build_user_agent,  # 2026-11-05 14:14 +03: UA (#939)
    _enrich_error,
    _load_env_file,
    _write_log,
    clean_message,
    validate_phone_input,
)

try:
    import aiohttp
    _aiohttp_available = True
except ImportError:
    _aiohttp_available = False


# 2026-11-05 14:14 +03: user_agent parameter added, sent on every call (#939).
async def _awrite_log(log_file: str, entry: dict) -> None:
    # 2026-11-07 01:55 +03: write the JSONL log in a worker thread: a plain open() inside the event loop blocks it
    # (Home Assistant flags it as a blocking call). No thread at all when logging is off. Task py-async-log-blocking.
    if not log_file:
        return
    await asyncio.get_running_loop().run_in_executor(None, _write_log, log_file, entry)


async def _async_request(endpoint: str, payload: dict, log_file: str = "",
                         user_agent: str = "") -> dict:
    """Async POST to a kwtSMS endpoint. Raises RuntimeError on network or JSON failure."""
    if not _aiohttp_available:
        raise RuntimeError(
            "aiohttp is required for async usage. Install with: pip install kwtsms[async]"
        )
    url = BASE_URL + endpoint + "/"
    safe_payload = {k: ("***" if k == "password" else v) for k, v in payload.items()}
    log_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "request": safe_payload,
        "response": None,
        "ok": False,
        "error": None,
    }
    try:
        async with aiohttp.ClientSession() as session:
            # 2026-11-05 14:14 +03: User-Agent kwtsms-python/<version>, app token first when given (#939).
            async with session.post(url, json=payload,
                                    headers={"User-Agent": user_agent or _build_user_agent()},
                                    timeout=aiohttp.ClientTimeout(total=15)) as resp:
                text = await resp.text()
                try:
                    data = json.loads(text)
                except json.JSONDecodeError as exc:
                    log_entry["error"] = f"Invalid JSON response: {exc}"
                    await _awrite_log(log_file, log_entry)
                    raise RuntimeError(f"Invalid JSON response: {exc}") from exc
                log_entry["response"] = data
                log_entry["ok"] = data.get("result") == "OK"
                await _awrite_log(log_file, log_entry)
                return data
    except aiohttp.ClientError as exc:
        log_entry["error"] = f"Network error: {exc}"
        await _awrite_log(log_file, log_entry)
        raise RuntimeError(f"Network error: {exc}") from exc


class AsyncKwtSMS:
    """
    Async kwtSMS API client. Requires aiohttp: pip install kwtsms[async]

    Quick start:
        from kwtsms import AsyncKwtSMS

        sms = AsyncKwtSMS.from_env()
        ok, balance, err = await sms.verify()
        result = await sms.send("965XXXXXXXX", "Your OTP is: 123456")
    """

    def __init__(self, username: str, password: str, sender_id: str = "KWT-SMS",
                 test_mode: bool = False, log_file: str = "kwtsms.log",
                 app_name: str = ""):  # 2026-11-05 14:14 +03: app_name for the User-Agent (#939)
        """
        Create an AsyncKwtSMS client.

        Args:
            username:  kwtSMS API username
            password:  kwtSMS API password
            sender_id: default Sender ID shown on recipient's phone
            test_mode: if True, messages are queued but not delivered; credits are held
                       until you delete them from the Sending Queue
                       (2026-10-22 15:33 +03: corrected, test sends do hold credits)
            log_file:  path to JSONL request log file, or "" to disable logging
            app_name:  optional product token of the calling app, e.g. "kwtsms-wordpress/3.5.2",
                       sent before the library token in the User-Agent
        """
        if not username or not password:
            raise ValueError("username and password are required")
        # 2026-11-05 14:14 +03: identify the caller to the API (name and version only, no personal data), #939.
        self.user_agent = _build_user_agent(app_name)
        self.username   = username
        self.password   = password
        self.sender_id  = sender_id
        self.test_mode  = test_mode
        self.log_file   = log_file
        self._cached_balance:   Optional[float] = None
        self._cached_purchased: Optional[float] = None

    def __repr__(self) -> str:
        return (
            f"AsyncKwtSMS(username={self.username!r}, password='***', "
            f"sender_id={self.sender_id!r}, test_mode={self.test_mode!r})"
        )

    @classmethod
    def from_env(cls, env_file: str = ".env") -> "AsyncKwtSMS":
        """Load credentials from environment variables, falling back to .env file."""
        file_env = _load_env_file(env_file)

        def get(key: str, default: str = "") -> str:
            val = os.environ.get(key)
            if val is not None:
                return val
            val = file_env.get(key)
            if val is not None:
                return val
            return default

        username  = get("KWTSMS_USERNAME")
        password  = get("KWTSMS_PASSWORD")
        sender_id = get("KWTSMS_SENDER_ID", "KWT-SMS")
        test_mode = get("KWTSMS_TEST_MODE", "0") == "1"
        log_file  = get("KWTSMS_LOG_FILE", "kwtsms.log")

        missing = [k for k, v in
                   {"KWTSMS_USERNAME": username, "KWTSMS_PASSWORD": password}.items()
                   if not v]
        if missing:
            raise ValueError(f"Missing credentials: {', '.join(missing)}")

        return cls(username, password, sender_id, test_mode, log_file)

    def _creds(self) -> dict:
        return {"username": self.username, "password": self.password}

    @property
    def purchased(self) -> Optional[float]:
        """Total credits purchased. None before the first successful verify() call."""
        return self._cached_purchased

    async def verify(self) -> tuple:
        """Test credentials. Returns (ok: bool, balance: float | None, error: str | None)."""
        try:
            data = await _async_request("balance", self._creds(), self.log_file, user_agent=self.user_agent)  # 2026-11-05 14:14 +03: UA (#939)
            if data.get("result") == "OK":
                self._cached_balance   = float(data.get("available", 0))
                self._cached_purchased = float(data.get("purchased", 0))
                return True, self._cached_balance, None
            data = _enrich_error(data)
            description = data.get("description", data.get("code", "Unknown error"))
            action = data.get("action")
            return False, None, f"{description} -> {action}" if action else description
        except RuntimeError as exc:
            return False, None, str(exc)

    async def balance(self) -> Optional[float]:
        """Get current balance. Returns None on error (or last cached value if available)."""
        ok, bal, _ = await self.verify()
        return bal if ok else self._cached_balance

    async def send(self, mobile: Union[str, List[str]], message: str,
                   sender: Optional[str] = None) -> dict:
        """
        Send SMS to one or more numbers. Same contract as KwtSMS.send().

        Note: Maximum 200 numbers per call. For larger lists, split into batches.

        Returns OK or ERROR dict; never raises.
        """
        effective_sender = sender or self.sender_id
        raw_list = mobile if isinstance(mobile, list) else [mobile]

        valid_numbers: List[str] = []
        invalid: List[dict] = []
        for raw in raw_list:
            is_valid, error, normalized = validate_phone_input(str(raw))
            if is_valid:
                valid_numbers.append(normalized)
            else:
                invalid.append({"input": str(raw), "error": error})

        if not valid_numbers:
            description = (invalid[0]["error"] if len(invalid) == 1
                           else f"All {len(invalid)} phone numbers are invalid")
            return _enrich_error({"result": "ERROR", "code": "ERR_INVALID_INPUT",
                                  "description": description, "invalid": invalid})

        if len(valid_numbers) > 200:
            return _enrich_error({
                "result": "ERROR",
                "code": "ERR007",
                "description": f"Too many numbers ({len(valid_numbers)}). Maximum 200 per call. For larger lists, call send() in batches.",
            })

        cleaned = clean_message(message)
        if not cleaned:
            return _enrich_error({"result": "ERROR", "code": "ERR009",
                                  "description": "Message is empty after cleaning "
                                                 "(contained only emojis or invisible characters)."})

        payload = {
            **self._creds(),
            "sender":  effective_sender,
            "mobile":  ",".join(valid_numbers),
            "message": cleaned,
            "test":    "1" if self.test_mode else "0",
        }
        try:
            result = await _async_request("send", payload, self.log_file, user_agent=self.user_agent)  # 2026-11-05 14:14 +03: UA (#939)
        except RuntimeError as exc:
            return {"result": "ERROR", "code": "NETWORK", "description": str(exc),
                    "action": "Check your internet connection and try again."}

        if result.get("result") == "OK" and "balance-after" in result:
            self._cached_balance = float(result["balance-after"])
        else:
            result = _enrich_error(result)

        if invalid:
            result["invalid"] = invalid
        return result

    async def status(self, msg_id: str) -> dict:
        """
        Get delivery status for a sent message via /report/.

        Returns OK or ERROR dict; never raises.
        """
        try:
            data = await _async_request(
                "report", {**self._creds(), "msgid": msg_id}, self.log_file,
                user_agent=self.user_agent,  # 2026-11-05 14:14 +03: UA (#939)
            )
        except RuntimeError as exc:
            return {"result": "ERROR", "code": "NETWORK", "description": str(exc),
                    "action": "Check your internet connection and try again."}
        return _enrich_error(data)
