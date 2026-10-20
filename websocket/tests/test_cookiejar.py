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

    def test_add_rejects_foreign_domain(self):
        cookie_jar = SimpleCookieJar()
        cookie_jar.add("a=b; domain=victim.com", "evil.com")
        self.assertFalse(cookie_jar.jar)
        self.assertEqual(cookie_jar.get("victim.com"), "")

        cookie_jar = SimpleCookieJar()
        cookie_jar.add("a=b; domain=abc.com", "x.abc.com")
        cookie_jar.add("c=d; domain=.abc.com", "ABC.com")
        cookie_jar.add("e=f; domain=x.abc.com", "abc.com")
        cookie_jar.add("g=h; domain=abc.com", "xabc.com")
        self.assertEqual(cookie_jar.get("abc.com"), "a=b; c=d")

    def test_ip_host_matches_only_itself(self):
        """RFC 6265 5.1.3: the domain suffix rule does not apply to IP addresses."""
        cookie_jar = SimpleCookieJar()
        cookie_jar.add("a=b; Domain=0.1", "10.0.0.1")
        self.assertFalse(cookie_jar.jar)
        self.assertEqual(cookie_jar.get("192.168.0.1"), "")

        cookie_jar.add("c=d; Domain=10.0.0.1", "10.0.0.1")
        self.assertEqual(cookie_jar.get("10.0.0.1"), "c=d")
        self.assertEqual(cookie_jar.get("110.0.0.1"), "")
        self.assertEqual(cookie_jar.get("192.168.10.0.0.1"), "")

        cookie_jar = SimpleCookieJar()
        cookie_jar.add("e=f; Domain=::1", "::1")
        self.assertEqual(cookie_jar.get("::1"), "e=f")
        self.assertEqual(cookie_jar.get("fe80::1"), "")

    def test_trailing_dot_domain(self):
        """A trailing dot must not get a single label past the two-label floor."""
        cookie_jar = SimpleCookieJar()
        cookie_jar.add("a=b; Domain=com.", "evil.com.")
        self.assertFalse(cookie_jar.jar)
        self.assertEqual(cookie_jar.get("bank.com."), "")
        self.assertEqual(cookie_jar.get("bank.com"), "")

        # A fully qualified host and Domain are the same domain as without the dot
        cookie_jar.add("c=d; Domain=example.com.", "www.example.com.")
        self.assertEqual(sorted(cookie_jar.jar), [".example.com"])
        self.assertEqual(cookie_jar.get("www.example.com"), "c=d")
        self.assertEqual(cookie_jar.get("example.com."), "c=d")

    def test_escaped_control_characters_are_dropped(self):
        """Octal-escaped CR/LF in a quoted value must never reach a request
        header (header injection through the jar)."""
        cookie_jar = SimpleCookieJar()
        cookie_jar.add(
            'sid="x\\015\\012Authorization: Bearer forged"; Domain=example.com',
            "a.example.com",
        )
        cookie_jar.add('t="tab\\011here"; Domain=example.com', "a.example.com")
        cookie_jar.add("ok=1; Domain=example.com", "a.example.com")
        self.assertEqual(cookie_jar.get("b.example.com"), "ok=1")

    def test_get_sends_value_as_encoded_by_server(self):
        cookie_jar = SimpleCookieJar()
        cookie_jar.add('q="a b\\073c"; Domain=example.com', "example.com")
        self.assertEqual(cookie_jar.get("example.com"), 'q="a b\\073c"')

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
