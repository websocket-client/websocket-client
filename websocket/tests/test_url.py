# -*- coding: utf-8 -*-
#
"""
websocket - WebSocket client library for Python

Copyright (C) 2010 Hiroki Ohtani(liris)

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

"""

import sys
import os

from websocket._url import get_proxy_info, parse_url

if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    import unittest2 as unittest
else:
    import unittest
sys.path[0:0] = [""]


class UrlTest(unittest.TestCase):

    def testParseUrl(self):
        p = parse_url("ws://www.example.com/r")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 80)
        self.assertEqual(p[2], "/r")
        self.assertEqual(p[3], False)

        p = parse_url("ws://www.example.com/r/")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 80)
        self.assertEqual(p[2], "/r/")
        self.assertEqual(p[3], False)

        p = parse_url("ws://www.example.com/")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 80)
        self.assertEqual(p[2], "/")
        self.assertEqual(p[3], False)

        p = parse_url("ws://www.example.com")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 80)
        self.assertEqual(p[2], "/")
        self.assertEqual(p[3], False)

        p = parse_url("ws://www.example.com:8080/r")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 8080)
        self.assertEqual(p[2], "/r")
        self.assertEqual(p[3], False)

        p = parse_url("ws://www.example.com:8080/")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 8080)
        self.assertEqual(p[2], "/")
        self.assertEqual(p[3], False)

        p = parse_url("ws://www.example.com:8080")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 8080)
        self.assertEqual(p[2], "/")
        self.assertEqual(p[3], False)

        p = parse_url("wss://www.example.com:8080/r")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 8080)
        self.assertEqual(p[2], "/r")
        self.assertEqual(p[3], True)

        p = parse_url("wss://www.example.com:8080/r?key=value")
        self.assertEqual(p[0], "www.example.com")
        self.assertEqual(p[1], 8080)
        self.assertEqual(p[2], "/r?key=value")
        self.assertEqual(p[3], True)

        self.assertRaises(ValueError, parse_url, "http://www.example.com/r")

        if sys.version_info[0] == 2 and sys.version_info[1] < 7:
            return

        p = parse_url("ws://[2a03:4000:123:83::3]/r")
        self.assertEqual(p[0], "2a03:4000:123:83::3")
        self.assertEqual(p[1], 80)
        self.assertEqual(p[2], "/r")
        self.assertEqual(p[3], False)

        p = parse_url("ws://[2a03:4000:123:83::3]:8080/r")
        self.assertEqual(p[0], "2a03:4000:123:83::3")
        self.assertEqual(p[1], 8080)
        self.assertEqual(p[2], "/r")
        self.assertEqual(p[3], False)

        p = parse_url("wss://[2a03:4000:123:83::3]/r")
        self.assertEqual(p[0], "2a03:4000:123:83::3")
        self.assertEqual(p[1], 443)
        self.assertEqual(p[2], "/r")
        self.assertEqual(p[3], True)

        p = parse_url("wss://[2a03:4000:123:83::3]:8080/r")
        self.assertEqual(p[0], "2a03:4000:123:83::3")
        self.assertEqual(p[1], 8080)
        self.assertEqual(p[2], "/r")
        self.assertEqual(p[3], True)


class ProxyInfoTest(unittest.TestCase):
    def setUp(self):
        self.http_proxy = os.environ.get("http_proxy", None)
        self.https_proxy = os.environ.get("https_proxy", None)
        if "http_proxy" in os.environ:
            del os.environ["http_proxy"]
        if "https_proxy" in os.environ:
            del os.environ["https_proxy"]

    def tearDown(self):
        if self.http_proxy:
            os.environ["http_proxy"] = self.http_proxy
        elif "http_proxy" in os.environ:
            del os.environ["http_proxy"]

        if self.https_proxy:
            os.environ["https_proxy"] = self.https_proxy
        elif "https_proxy" in os.environ:
            del os.environ["https_proxy"]

    def testProxyFromArgs(self):
        self.assertEqual(get_proxy_info("echo.websocket.org", False, proxy_host="localhost"), ("localhost", 0, None))
        self.assertEqual(get_proxy_info("echo.websocket.org", False, proxy_host="localhost", proxy_port=3128),
                         ("localhost", 3128, None))
        self.assertEqual(get_proxy_info("echo.websocket.org", True, proxy_host="localhost"), ("localhost", 0, None))
        self.assertEqual(get_proxy_info("echo.websocket.org", True, proxy_host="localhost", proxy_port=3128),
                         ("localhost", 3128, None))

        self.assertEqual(get_proxy_info("echo.websocket.org", False, proxy_host="localhost", proxy_auth=("a", "b")),
                         ("localhost", 0, ("a", "b")))
        self.assertEqual(
            get_proxy_info("echo.websocket.org", False, proxy_host="localhost", proxy_port=3128, proxy_auth=("a", "b")),
            ("localhost", 3128, ("a", "b")))
        self.assertEqual(get_proxy_info("echo.websocket.org", True, proxy_host="localhost", proxy_auth=("a", "b")),
                         ("localhost", 0, ("a", "b")))
        self.assertEqual(
            get_proxy_info("echo.websocket.org", True, proxy_host="localhost", proxy_port=3128, proxy_auth=("a", "b")),
            ("localhost", 3128, ("a", "b")))

        self.assertEqual(get_proxy_info("echo.websocket.org", True, proxy_host="localhost", proxy_port=3128,
                                        no_proxy=["example.com"], proxy_auth=("a", "b")),
                         ("localhost", 3128, ("a", "b")))
        self.assertEqual(get_proxy_info("echo.websocket.org", True, proxy_host="localhost", proxy_port=3128,
                                        no_proxy=["echo.websocket.org"], proxy_auth=("a", "b")),
                         (None, 0, None))

    def testProxyFromEnv(self):
        os.environ["http_proxy"] = "http://localhost/"
        self.assertEqual(get_proxy_info("echo.websocket.org", False), ("localhost", None, None))
        os.environ["http_proxy"] = "http://localhost:3128/"
        self.assertEqual(get_proxy_info("echo.websocket.org", False), ("localhost", 3128, None))

        os.environ["http_proxy"] = "http://localhost/"
        os.environ["https_proxy"] = "http://localhost2/"
        self.assertEqual(get_proxy_info("echo.websocket.org", False), ("localhost", None, None))
        os.environ["http_proxy"] = "http://localhost:3128/"
        os.environ["https_proxy"] = "http://localhost2:3128/"
        self.assertEqual(get_proxy_info("echo.websocket.org", False), ("localhost", 3128, None))

        os.environ["http_proxy"] = "http://localhost/"
        os.environ["https_proxy"] = "http://localhost2/"
        self.assertEqual(get_proxy_info("echo.websocket.org", True), ("localhost2", None, None))
        os.environ["http_proxy"] = "http://localhost:3128/"
        os.environ["https_proxy"] = "http://localhost2:3128/"
        self.assertEqual(get_proxy_info("echo.websocket.org", True), ("localhost2", 3128, None))

        os.environ["http_proxy"] = "http://a:b@localhost/"
        self.assertEqual(get_proxy_info("echo.websocket.org", False), ("localhost", None, ("a", "b")))
        os.environ["http_proxy"] = "http://a:b@localhost:3128/"
        self.assertEqual(get_proxy_info("echo.websocket.org", False), ("localhost", 3128, ("a", "b")))

        os.environ["http_proxy"] = "http://a:b@localhost/"
        os.environ["https_proxy"] = "http://a:b@localhost2/"
        self.assertEqual(get_proxy_info("echo.websocket.org", False), ("localhost", None, ("a", "b")))
        os.environ["http_proxy"] = "http://a:b@localhost:3128/"
        os.environ["https_proxy"] = "http://a:b@localhost2:3128/"
        self.assertEqual(get_proxy_info("echo.websocket.org", False), ("localhost", 3128, ("a", "b")))

        os.environ["http_proxy"] = "http://a:b@localhost/"
        os.environ["https_proxy"] = "http://a:b@localhost2/"
        self.assertEqual(get_proxy_info("echo.websocket.org", True), ("localhost2", None, ("a", "b")))
        os.environ["http_proxy"] = "http://a:b@localhost:3128/"
        os.environ["https_proxy"] = "http://a:b@localhost2:3128/"
        self.assertEqual(get_proxy_info("echo.websocket.org", True), ("localhost2", 3128, ("a", "b")))

        os.environ["http_proxy"] = "http://a:b@localhost/"
        os.environ["https_proxy"] = "http://a:b@localhost2/"
        os.environ["no_proxy"] = "example1.com,example2.com"
        self.assertEqual(get_proxy_info("example.1.com", True), ("localhost2", None, ("a", "b")))
        os.environ["http_proxy"] = "http://a:b@localhost:3128/"
        os.environ["https_proxy"] = "http://a:b@localhost2:3128/"
        os.environ["no_proxy"] = "example1.com,example2.com, echo.websocket.org"
        self.assertEqual(get_proxy_info("echo.websocket.org", True), (None, 0, None))

        os.environ["http_proxy"] = "http://a:b@localhost:3128/"
        os.environ["https_proxy"] = "http://a:b@localhost2:3128/"
        os.environ["no_proxy"] = "127.0.0.0/8, 192.168.0.0/16"
        self.assertEqual(get_proxy_info("127.0.0.1", False), (None, 0, None))
        self.assertEqual(get_proxy_info("192.168.1.1", False), (None, 0, None))


if __name__ == "__main__":
    unittest.main()
