# -*- coding: utf-8 -*-
import sys
import unittest
from unittest.mock import patch


class SSLCompatTest(unittest.TestCase):
    def test_ssl_available(self):
        """Test that SSL is available in normal conditions"""
        import websocket._ssl_compat as ssl_compat

        # In normal conditions, SSL should be available
        self.assertTrue(ssl_compat.HAVE_SSL)
        self.assertIsNotNone(ssl_compat.ssl)

        # SSL exception classes should be available
        self.assertTrue(hasattr(ssl_compat, 'SSLError'))
        self.assertTrue(hasattr(ssl_compat, 'SSLEOFError'))
        self.assertTrue(hasattr(ssl_compat, 'SSLWantReadError'))
        self.assertTrue(hasattr(ssl_compat, 'SSLWantWriteError'))

    def test_ssl_not_available(self):
        """Test fallback behavior when SSL is not available"""
        # Remove ssl_compat from modules to force reimport
        if 'websocket._ssl_compat' in sys.modules:
            del sys.modules['websocket._ssl_compat']

        # Mock the ssl module to not be available
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'ssl':
                raise ImportError("No module named 'ssl'")
            return original_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            import websocket._ssl_compat as ssl_compat

            # SSL should not be available
            self.assertFalse(ssl_compat.HAVE_SSL)
            self.assertIsNone(ssl_compat.ssl)

            # Fallback exception classes should be available and functional
            self.assertTrue(issubclass(ssl_compat.SSLError, Exception))
            self.assertTrue(issubclass(ssl_compat.SSLEOFError, Exception))
            self.assertTrue(issubclass(ssl_compat.SSLWantReadError, Exception))
            self.assertTrue(issubclass(ssl_compat.SSLWantWriteError, Exception))

            # Test that exceptions can be instantiated
            ssl_error = ssl_compat.SSLError("test error")
            self.assertIsInstance(ssl_error, Exception)
            self.assertEqual(str(ssl_error), "test error")

            ssl_eof_error = ssl_compat.SSLEOFError("test eof")
            self.assertIsInstance(ssl_eof_error, Exception)

            ssl_want_read = ssl_compat.SSLWantReadError("test read")
            self.assertIsInstance(ssl_want_read, Exception)

            ssl_want_write = ssl_compat.SSLWantWriteError("test write")
            self.assertIsInstance(ssl_want_write, Exception)

    def tearDown(self):
        """Clean up after tests"""
        # Ensure ssl_compat is reimported fresh for next test
        if 'websocket._ssl_compat' in sys.modules:
            del sys.modules['websocket._ssl_compat']


if __name__ == "__main__":
    unittest.main()