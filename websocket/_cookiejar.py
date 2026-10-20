import email.utils
import http.cookies
import ipaddress
import math
import time
from typing import Optional, Union
from http.cookies import CookieError
from ._logging import debug, warning

"""
_cookiejar.py
websocket - WebSocket client library for Python

Copyright 2026 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


def _has_control_char(text: str) -> bool:
    return any(ord(c) < 0x20 or ord(c) == 0x7F for c in text)


class SimpleCookieJar:
    def __init__(self) -> None:
        self.jar: dict = {}
        # (domain key, morsel key) -> epoch after which the morsel is expired
        self._expiry: dict = {}

    def add(
        self,
        set_cookie: Optional[Union[str, list]],
        host: Optional[str] = None,
    ) -> None:
        if not set_cookie:
            return
        cookie_headers = set_cookie if isinstance(set_cookie, list) else [set_cookie]
        for cookie_header in cookie_headers:
            try:
                simple_cookie = http.cookies.SimpleCookie(cookie_header)
            except CookieError:
                warning("Ignoring invalid Set-Cookie header")
                continue

            # Store each morsel only under its own domain: morsels that
            # carry a domain attribute never leak into a sibling's domain
            # entry, and morsels without a domain are dropped (consistent
            # with the no-domain rule above).
            for v in simple_cookie.values():
                if domain := v.get("domain"):
                    domain = self._domain_key(domain)
                    if host is not None and not self._domain_match(host, domain):
                        debug("Ignoring Set-Cookie for another domain")
                        continue
                    if _has_control_char(v.value) or _has_control_char(v.coded_value):
                        # RFC 6265 4.1.1: cookie values exclude CTLs. A quoted
                        # value can smuggle them in as octal escapes (\015\012)
                        # that SimpleCookie decodes into raw CR/LF.
                        debug("Ignoring Set-Cookie with control characters")
                        continue
                    deadline = self._deadline(v)
                    if deadline is not None and deadline <= time.time():
                        # RFC 6265 5.3 step 12: an already-expired cookie
                        # (Max-Age=0 is a deletion) removes any stored value
                        cookie = self.jar.get(domain)
                        if cookie is not None:
                            cookie.pop(v.key, None)
                            self._expiry.pop((domain, v.key), None)
                            if not cookie:
                                del self.jar[domain]
                        continue
                    cookie = self.jar.get(domain)
                    if cookie is None:
                        cookie = http.cookies.SimpleCookie()
                    cookie[v.key] = v
                    self.jar[domain] = cookie
                    if deadline is None:
                        self._expiry.pop((domain, v.key), None)
                    else:
                        self._expiry[(domain, v.key)] = deadline

    def set(self, set_cookie: str) -> None:
        """Replace-style counterpart to add(): clears the existing entry
        for each cookie's domain before storing (last write wins), with
        the same per-morsel storage rule as add()."""
        if set_cookie:
            simple_cookie = http.cookies.SimpleCookie(set_cookie)
            for v in simple_cookie.values():
                if domain := v.get("domain"):
                    self._forget(self._domain_key(domain))
            self.add(set_cookie)

    def get(self, host: str, secure: bool = False) -> str:
        """Cookie header value for host. Morsels with the Secure attribute
        are only returned when secure is True (RFC 6265 5.4 step 1)."""
        if not host:
            return ""

        cookies = []
        for domain in list(self.jar):
            if not self._host_in_domain(host, domain[1:]):
                continue
            cookie = self.jar[domain]
            now = time.time()
            for k in [k for k, _ in cookie.items() if self._expired(domain, k, now)]:
                del cookie[k]
                self._expiry.pop((domain, k), None)
            if not cookie:
                del self.jar[domain]
                continue
            cookies.append(cookie)

        return "; ".join(
            filter(
                None,
                sorted(
                    [
                        f"{k}={v.coded_value}"
                        for cookie in filter(None, cookies)
                        for k, v in cookie.items()
                        if secure or not v["secure"]
                    ]
                ),
            )
        )

    @staticmethod
    def _domain_key(domain: str) -> str:
        """Jar key for a Domain attribute: lowercase, one leading dot, no
        trailing dot (``Domain=Example.COM.`` and ``.example.com`` are the
        same domain)."""
        return "." + domain.lower().strip(".")

    @staticmethod
    def _is_ip(host: str) -> bool:
        try:
            ipaddress.ip_address(host.strip("[]"))
        except ValueError:
            return False
        return True

    @classmethod
    def _host_in_domain(cls, host: str, labels: str) -> bool:
        """RFC 6265 5.1.3 domain-match of host against a domain without its
        leading dot. An IP address only matches itself: the suffix rule
        applies to host names, otherwise Domain=0.1 would cover 10.0.0.1
        and 192.168.0.1 alike."""
        host = host.lower().rstrip(".")
        if cls._is_ip(host) or cls._is_ip(labels):
            # an IP host, or a cookie whose Domain is an IP, is host-only
            return host.strip("[]") == labels.strip("[]")
        return host == labels or host.endswith("." + labels)

    @classmethod
    def _domain_match(cls, host: str, domain: str) -> bool:
        # RFC 6265 5.3 step 6: ignore cookies whose Domain does not
        # match the host that set them, so one server cannot plant
        # cookies for another. The two-label floor keeps public-suffix
        # style values like Domain=com from matching every host under
        # them; trailing dots are removed first, so Domain=com. is also a
        # single label. An IP address passes only by exact match, so the
        # floor does not apply to it (no public-suffix list: a co.uk-style
        # suffix would still pass; add a PSL if that matters).
        labels = domain.lower().strip(".")
        if not cls._host_in_domain(host, labels):
            return False
        return "." in labels or cls._is_ip(labels)

    def _forget(self, domain: str) -> None:
        """Drop a domain entry and the expiry records under it."""
        self.jar.pop(domain, None)
        for key in [k for k in self._expiry if k[0] == domain]:
            del self._expiry[key]

    @staticmethod
    def _deadline(v: http.cookies.Morsel) -> Optional[float]:
        """RFC 6265 5.2: Max-Age overrides Expires; an invalid attribute
        value is ignored. Returns the epoch after which the morsel is
        expired, or None for a session cookie."""
        max_age = v.get("max-age", "")
        if max_age:
            try:
                delta = int(max_age)
            except ValueError:
                pass  # invalid Max-Age: ignore it, Expires may still apply
            else:
                try:
                    return time.time() + delta
                except OverflowError:
                    # RFC 6265 5.2.2: too large to represent means the latest
                    # (or, when negative, the earliest) representable time
                    return math.inf if delta > 0 else -math.inf
        expires = v.get("expires", "")
        if expires:
            parsed = email.utils.parsedate_tz(expires)
            if parsed is not None:
                try:
                    return email.utils.mktime_tz(parsed)
                except (OverflowError, ValueError):
                    # A date the platform cannot convert (e.g. a year past
                    # 9999) is an invalid attribute, ignored per RFC 6265 5.2.1
                    pass
        return None

    def _expired(self, domain: str, key: str, now: float) -> bool:
        deadline = self._expiry.get((domain, key))
        return deadline is not None and deadline <= now
