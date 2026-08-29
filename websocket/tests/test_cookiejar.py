import unittest

from websocket._cookiejar import SimpleCookieJar

"""
test_cookiejar.py
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


class CookieJarTest(unittest.TestCase):
    def test_add(self):
        cookie_jar = SimpleCookieJar()
        cookie_jar.add("")
        self.assertFalse(
            cookie_jar.jar, "Cookie with no domain should not be added to the jar"
        )

        cookie_jar = SimpleCookieJar()
        cookie_jar.add("a=b")
        self.assertFalse(
            cookie_jar.jar, "Cookie with no domain should not be added to the jar"
        )

        cookie_jar = SimpleCookieJar()
        cookie_jar.add("a=b; domain=.abc")
        self.assertTrue(".abc" in cookie_jar.jar)

        cookie_jar = SimpleCookieJar()
        cookie_jar.add("a=b; domain=abc")
        self.assertTrue(".abc" in cookie_jar.jar)
        self.assertTrue("abc" not in cookie_jar.jar)

        cookie_jar = SimpleCookieJar()
        cookie_jar.add("a=b; c=d; domain=abc")
        # only the domain-bearing morsel is stored; the domainless
        # "a=b" is dropped per the no-domain rule
        self.assertEqual(cookie_jar.get("abc"), "c=d")
        self.assertEqual(cookie_jar.get(None), "")

        cookie_jar = SimpleCookieJar()
        cookie_jar.add("a=b; c=d; domain=abc")
        cookie_jar.add("e=f; domain=abc")
        self.assertEqual(cookie_jar.get("abc"), "c=d; e=f")

        cookie_jar = SimpleCookieJar()
        cookie_jar.add("a=b; c=d; domain=abc")
        cookie_jar.add("e=f; domain=.abc")
        self.assertEqual(cookie_jar.get("abc"), "c=d; e=f")

        cookie_jar = SimpleCookieJar()
        cookie_jar.add("a=b; c=d; domain=abc")
        cookie_jar.add("e=f; domain=xyz")
        self.assertEqual(cookie_jar.get("abc"), "c=d")
        self.assertEqual(cookie_jar.get("xyz"), "e=f")
        self.assertEqual(cookie_jar.get("something"), "")

    def test_add_multiple_set_cookie_headers_no_cross_domain(self):
        """Multiple Set-Cookie headers must not leak cookies across domains"""
        # Present in v1.9.1 and earlier: repeated Set-Cookie headers were
        # joined with "; " and the whole group stored under every domain.
        cookie_jar = SimpleCookieJar()
        cookie_jar.add(
            [
                "session=x; Domain=.example.com",
                "tracking=y; Domain=.ads.example.com",
            ]
        )
        self.assertEqual(sorted(cookie_jar.jar), [".ads.example.com", ".example.com"])
        self.assertEqual(set(cookie_jar.jar[".example.com"].keys()), {"session"})
        self.assertEqual(set(cookie_jar.jar[".ads.example.com"].keys()), {"tracking"})
        # Subdomain cookie must not leak up; parent-domain cookie
        # legitimately matches the subdomain host (RFC 6265 domain match).
        self.assertEqual(cookie_jar.get("example.com"), "session=x")
        self.assertEqual(cookie_jar.get("ads.example.com"), "session=x; tracking=y")

    def test_add_joined_multi_domain_string_no_contamination(self):
        """A single str carrying two differently-scoped cookies must not
        cross-contaminate domains, regardless of input shape."""
        cookie_jar = SimpleCookieJar()
        cookie_jar.add(
            "session=x; Domain=.example.com; tracking=y; Domain=.ads.example.com"
        )
        self.assertEqual(set(cookie_jar.jar[".example.com"].keys()), {"session"})
        self.assertEqual(set(cookie_jar.jar[".ads.example.com"].keys()), {"tracking"})

    def test_add_uppercase_domain_and_same_name_overwrite(self):
        """Domain attributes are lowered for jar keys, and a repeated
        cookie name on the same domain overwrites (RFC 6265 last-wins)."""
        cookie_jar = SimpleCookieJar()
        cookie_jar.add("a=b; Domain=ABC.com")
        self.assertEqual(sorted(cookie_jar.jar), [".abc.com"])
        self.assertEqual(cookie_jar.get("abc.com"), "a=b")
        self.assertEqual(cookie_jar.get("ABC.com"), "a=b")

        cookie_jar = SimpleCookieJar()
        cookie_jar.add(["tok=1; domain=abc", "tok=2; domain=abc"])
        self.assertEqual(cookie_jar.get("abc"), "tok=2")

    def test_set(self):
        cookie_jar = SimpleCookieJar()
        cookie_jar.set("a=b")
        self.assertFalse(
            cookie_jar.jar, "Cookie with no domain should not be added to the jar"
        )

        cookie_jar = SimpleCookieJar()
        cookie_jar.set("a=b; domain=.abc")
        self.assertTrue(".abc" in cookie_jar.jar)

        cookie_jar = SimpleCookieJar()
        cookie_jar.set("a=b; domain=abc")
        self.assertTrue(".abc" in cookie_jar.jar)
        self.assertTrue("abc" not in cookie_jar.jar)

        cookie_jar = SimpleCookieJar()
        cookie_jar.set("a=b; c=d; domain=abc")
        # same per-morsel rule as add(): domainless "a=b" is dropped
        self.assertEqual(cookie_jar.get("abc"), "c=d")

        cookie_jar = SimpleCookieJar()
        cookie_jar.set("a=b; c=d; domain=abc")
        cookie_jar.set("e=f; domain=abc")
        self.assertEqual(cookie_jar.get("abc"), "e=f")

        cookie_jar = SimpleCookieJar()
        cookie_jar.set("a=b; c=d; domain=abc")
        cookie_jar.set("e=f; domain=.abc")
        self.assertEqual(cookie_jar.get("abc"), "e=f")

        cookie_jar = SimpleCookieJar()
        cookie_jar.set("a=b; c=d; domain=abc")
        cookie_jar.set("e=f; domain=xyz")
        self.assertEqual(cookie_jar.get("abc"), "c=d")
        self.assertEqual(cookie_jar.get("xyz"), "e=f")
        self.assertEqual(cookie_jar.get("something"), "")

    def test_set_multi_domain_string_no_cross_domain(self):
        """set() must not leak cookies across domains: each jar
        entry holds only its own morsel after clear-then-add."""
        cookie_jar = SimpleCookieJar()
        cookie_jar.set("a=b; Domain=.example.com; c=d; Domain=.ads.example.com")
        self.assertEqual(set(cookie_jar.jar[".example.com"].keys()), {"a"})
        self.assertEqual(set(cookie_jar.jar[".ads.example.com"].keys()), {"c"})

    def test_get(self):
        cookie_jar = SimpleCookieJar()
        cookie_jar.set("a=b; c=d; domain=abc.com")
        self.assertEqual(cookie_jar.get("abc.com"), "c=d")
        self.assertEqual(cookie_jar.get("x.abc.com"), "c=d")
        self.assertEqual(cookie_jar.get("abc.com.es"), "")
        self.assertEqual(cookie_jar.get("xabc.com"), "")

        cookie_jar.set("a=b; c=d; domain=.abc.com")
        self.assertEqual(cookie_jar.get("abc.com"), "c=d")
        self.assertEqual(cookie_jar.get("x.abc.com"), "c=d")
        self.assertEqual(cookie_jar.get("abc.com.es"), "")
        self.assertEqual(cookie_jar.get("xabc.com"), "")


if __name__ == "__main__":
    unittest.main()
