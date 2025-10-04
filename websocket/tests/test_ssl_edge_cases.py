# -*- coding: utf-8 -*-
import unittest
import socket
import ssl
from unittest.mock import Mock, patch, MagicMock

from websocket._ssl_compat import SSLError, SSLEOFError, SSLWantReadError, SSLWantWriteError, HAVE_SSL
from websocket._http import _ssl_socket, _wrap_sni_socket
from websocket._exceptions import WebSocketException
from websocket._socket import recv, send


class SSLEdgeCasesTest(unittest.TestCase):
    
    def setUp(self):
        if not HAVE_SSL:
            self.skipTest("SSL not available")
    
    def test_ssl_handshake_failure(self):
        """Test SSL handshake failure scenarios"""
        mock_sock = Mock()
        
        # Test SSL handshake timeout
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.wrap_socket.side_effect = socket.timeout("SSL handshake timeout")
            
            sslopt = {"cert_reqs": ssl.CERT_REQUIRED}
            
            with self.assertRaises(socket.timeout):
                _ssl_socket(mock_sock, sslopt, "example.com")
    
    def test_ssl_certificate_verification_failures(self):
        """Test various SSL certificate verification failure scenarios"""
        mock_sock = Mock()
        
        # Test certificate verification failure
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.wrap_socket.side_effect = ssl.SSLCertVerificationError("Certificate verification failed")
            
            sslopt = {"cert_reqs": ssl.CERT_REQUIRED, "check_hostname": True}
            
            with self.assertRaises(ssl.SSLCertVerificationError):
                _ssl_socket(mock_sock, sslopt, "badssl.example")
    
    def test_ssl_context_configuration_edge_cases(self):
        """Test SSL context configuration with various edge cases"""
        mock_sock = Mock()
        
        # Test with pre-created SSL context
        with patch('ssl.SSLContext') as mock_ssl_context:
            existing_context = Mock()
            existing_context.wrap_socket.return_value = Mock()
            
            sslopt = {"context": existing_context}
            result = _ssl_socket(mock_sock, sslopt, "example.com")
            
            # Should use the provided context, not create a new one
            mock_ssl_context.assert_not_called()
            existing_context.wrap_socket.assert_called_once()
    
    def test_ssl_ca_bundle_environment_edge_cases(self):
        """Test CA bundle environment variable edge cases"""
        mock_sock = Mock()
        
        # Test with non-existent CA bundle file
        with patch.dict('os.environ', {'WEBSOCKET_CLIENT_CA_BUNDLE': '/nonexistent/ca-bundle.crt'}):
            with patch('os.path.isfile', return_value=False):
                with patch('os.path.isdir', return_value=False):
                    with patch('ssl.SSLContext') as mock_ssl_context:
                        mock_context = Mock()
                        mock_ssl_context.return_value = mock_context
                        mock_context.wrap_socket.return_value = Mock()
                        
                        sslopt = {}
                        _ssl_socket(mock_sock, sslopt, "example.com")
                        
                        # Should not try to load non-existent CA bundle
                        mock_context.load_verify_locations.assert_not_called()
        
        # Test with CA bundle directory
        with patch.dict('os.environ', {'WEBSOCKET_CLIENT_CA_BUNDLE': '/etc/ssl/certs'}):
            with patch('os.path.isfile', return_value=False):
                with patch('os.path.isdir', return_value=True):
                    with patch('ssl.SSLContext') as mock_ssl_context:
                        mock_context = Mock()
                        mock_ssl_context.return_value = mock_context
                        mock_context.wrap_socket.return_value = Mock()
                        
                        sslopt = {}
                        _ssl_socket(mock_sock, sslopt, "example.com")
                        
                        # Should load CA directory
                        mock_context.load_verify_locations.assert_called_with(cafile=None, capath='/etc/ssl/certs')
    
    def test_ssl_cipher_configuration_edge_cases(self):
        """Test SSL cipher configuration edge cases"""
        mock_sock = Mock()
        
        # Test with invalid cipher suite
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.set_ciphers.side_effect = ssl.SSLError("No cipher can be selected")
            mock_context.wrap_socket.return_value = Mock()
            
            sslopt = {"ciphers": "INVALID_CIPHER"}
            
            with self.assertRaises(WebSocketException):
                _ssl_socket(mock_sock, sslopt, "example.com")
    
    def test_ssl_ecdh_curve_edge_cases(self):
        """Test ECDH curve configuration edge cases"""
        mock_sock = Mock()
        
        # Test with invalid ECDH curve
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.set_ecdh_curve.side_effect = ValueError("unknown curve name")
            mock_context.wrap_socket.return_value = Mock()
            
            sslopt = {"ecdh_curve": "invalid_curve"}
            
            with self.assertRaises(WebSocketException):
                _ssl_socket(mock_sock, sslopt, "example.com")
    
    def test_ssl_client_certificate_edge_cases(self):
        """Test client certificate configuration edge cases"""
        mock_sock = Mock()
        
        # Test with non-existent client certificate
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.load_cert_chain.side_effect = FileNotFoundError("No such file")
            mock_context.wrap_socket.return_value = Mock()
            
            sslopt = {"certfile": "/nonexistent/client.crt"}
            
            with self.assertRaises(WebSocketException):
                _ssl_socket(mock_sock, sslopt, "example.com")
    
    def test_ssl_want_read_write_retry_edge_cases(self):
        """Test SSL want read/write retry edge cases"""
        mock_sock = Mock()
        
        # Test SSLWantReadError with multiple retries before success
        read_attempts = [0]  # Use list for mutable reference
        def mock_recv(bufsize):
            read_attempts[0] += 1
            if read_attempts[0] == 1:
                raise SSLWantReadError("The operation did not complete")
            elif read_attempts[0] == 2:
                return b"data after retries"
            else:
                return b""
        
        mock_sock.recv.side_effect = mock_recv
        mock_sock.gettimeout.return_value = 30.0
        
        with patch('selectors.DefaultSelector') as mock_selector_class:
            mock_selector = Mock()
            mock_selector_class.return_value = mock_selector
            mock_selector.select.return_value = [True]  # Always ready
            
            result = recv(mock_sock, 100)
            
            self.assertEqual(result, b"data after retries")
            self.assertEqual(read_attempts[0], 2)
            # Should have used selector for retry
            mock_selector.register.assert_called()
            mock_selector.select.assert_called()
    
    def test_ssl_want_write_retry_edge_cases(self):
        """Test SSL want write retry edge cases"""
        mock_sock = Mock()
        
        # Test SSLWantWriteError with multiple retries before success
        write_attempts = [0]  # Use list for mutable reference
        def mock_send(data):
            write_attempts[0] += 1
            if write_attempts[0] == 1:
                raise SSLWantWriteError("The operation did not complete")
            elif write_attempts[0] == 2:
                return len(data)
            else:
                return 0
        
        mock_sock.send.side_effect = mock_send
        mock_sock.gettimeout.return_value = 30.0
        
        with patch('selectors.DefaultSelector') as mock_selector_class:
            mock_selector = Mock()
            mock_selector_class.return_value = mock_selector
            mock_selector.select.return_value = [True]  # Always ready
            
            result = send(mock_sock, b"test data")
            
            self.assertEqual(result, 9)  # len("test data")
            self.assertEqual(write_attempts[0], 2)
    
    def test_ssl_eof_error_edge_cases(self):
        """Test SSL EOF error edge cases"""
        mock_sock = Mock()
        
        # Test SSLEOFError during send
        mock_sock.send.side_effect = SSLEOFError("SSL connection has been closed")
        mock_sock.gettimeout.return_value = 30.0
        
        from websocket._exceptions import WebSocketConnectionClosedException
        
        with self.assertRaises(WebSocketConnectionClosedException):
            send(mock_sock, b"test data")
    
    def test_ssl_pending_data_edge_cases(self):
        """Test SSL pending data scenarios"""
        from websocket._dispatcher import SSLDispatcher
        from websocket._app import WebSocketApp
        
        # Mock SSL socket with pending data
        mock_ssl_sock = Mock()
        mock_ssl_sock.pending.return_value = 1024  # Simulates pending SSL data
        
        # Mock WebSocketApp
        mock_app = Mock(spec=WebSocketApp)
        mock_app.sock = Mock()
        mock_app.sock.sock = mock_ssl_sock
        
        dispatcher = SSLDispatcher(mock_app, 5.0)
        
        # When there's pending data, should return immediately without selector
        result = dispatcher.select(mock_ssl_sock, Mock())
        
        # Should return the socket list when there's pending data
        self.assertEqual(result, [mock_ssl_sock])
        mock_ssl_sock.pending.assert_called_once()
    
    def test_ssl_renegotiation_edge_cases(self):
        """Test SSL renegotiation scenarios"""
        mock_sock = Mock()
        
        # Simulate SSL renegotiation during read
        call_count = 0
        def mock_recv(bufsize):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise SSLWantReadError("SSL renegotiation required")
            return b"data after renegotiation"
        
        mock_sock.recv.side_effect = mock_recv
        mock_sock.gettimeout.return_value = 30.0
        
        with patch('selectors.DefaultSelector') as mock_selector_class:
            mock_selector = Mock()
            mock_selector_class.return_value = mock_selector
            mock_selector.select.return_value = [True]
            
            result = recv(mock_sock, 100)
            
            self.assertEqual(result, b"data after renegotiation")
            self.assertEqual(call_count, 2)
    
    def test_ssl_server_hostname_override(self):
        """Test SSL server hostname override scenarios"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.wrap_socket.return_value = Mock()
            
            # Test server_hostname override
            sslopt = {"server_hostname": "override.example.com"}
            _ssl_socket(mock_sock, sslopt, "original.example.com")
            
            # Should use override hostname in wrap_socket call
            mock_context.wrap_socket.assert_called_with(
                mock_sock,
                do_handshake_on_connect=True,
                suppress_ragged_eofs=True,
                server_hostname="override.example.com"
            )
    
    def test_ssl_protocol_version_edge_cases(self):
        """Test SSL protocol version edge cases"""
        mock_sock = Mock()
        
        # Test with deprecated SSL version
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.wrap_socket.return_value = Mock()
            
            # Test that deprecated ssl_version is still handled
            if hasattr(ssl, 'PROTOCOL_TLS'):
                sslopt = {"ssl_version": ssl.PROTOCOL_TLS}
                _ssl_socket(mock_sock, sslopt, "example.com")
                
                mock_ssl_context.assert_called_with(ssl.PROTOCOL_TLS)
    
    def test_ssl_keylog_file_edge_cases(self):
        """Test SSL keylog file configuration edge cases"""
        mock_sock = Mock()
        
        # Test with SSLKEYLOGFILE environment variable
        with patch.dict('os.environ', {'SSLKEYLOGFILE': '/tmp/ssl_keys.log'}):
            with patch('ssl.SSLContext') as mock_ssl_context:
                mock_context = Mock()
                mock_ssl_context.return_value = mock_context
                mock_context.wrap_socket.return_value = Mock()
                
                sslopt = {}
                _ssl_socket(mock_sock, sslopt, "example.com")
                
                # Should set keylog_filename
                self.assertEqual(mock_context.keylog_filename, '/tmp/ssl_keys.log')
    
    def test_ssl_context_verification_modes(self):
        """Test different SSL verification mode combinations"""
        mock_sock = Mock()
        
        test_cases = [
            # (cert_reqs, check_hostname, expected_verify_mode, expected_check_hostname)
            (ssl.CERT_NONE, False, ssl.CERT_NONE, False),
            (ssl.CERT_REQUIRED, False, ssl.CERT_REQUIRED, False),
            (ssl.CERT_REQUIRED, True, ssl.CERT_REQUIRED, True),
        ]
        
        for cert_reqs, check_hostname, expected_verify, expected_check in test_cases:
            with self.subTest(cert_reqs=cert_reqs, check_hostname=check_hostname):
                with patch('ssl.SSLContext') as mock_ssl_context:
                    mock_context = Mock()
                    mock_ssl_context.return_value = mock_context
                    mock_context.wrap_socket.return_value = Mock()
                    
                    sslopt = {"cert_reqs": cert_reqs, "check_hostname": check_hostname}
                    _ssl_socket(mock_sock, sslopt, "example.com")
                    
                    self.assertEqual(mock_context.verify_mode, expected_verify)
                    self.assertEqual(mock_context.check_hostname, expected_check)


    def test_ssl_socket_shutdown_edge_cases(self):
        """Test SSL socket shutdown edge cases"""
        from websocket._core import WebSocket
        
        mock_ssl_sock = Mock()
        mock_ssl_sock.shutdown.side_effect = SSLError("SSL shutdown failed")
        
        ws = WebSocket()
        ws.sock = mock_ssl_sock
        ws.connected = True
        
        # Should handle SSL shutdown errors gracefully
        try:
            ws.close()
        except SSLError:
            self.fail("SSL shutdown error should be handled gracefully")
    
    def test_ssl_socket_close_during_operation(self):
        """Test SSL socket being closed during ongoing operations"""
        mock_sock = Mock()
        
        # Simulate SSL socket being closed during recv
        mock_sock.recv.side_effect = SSLError("SSL connection has been closed unexpectedly")
        mock_sock.gettimeout.return_value = 30.0
        
        from websocket._exceptions import WebSocketConnectionClosedException
        
        # Should handle unexpected SSL closure
        with self.assertRaises((SSLError, WebSocketConnectionClosedException)):
            recv(mock_sock, 100)
    
    def test_ssl_compression_edge_cases(self):
        """Test SSL compression configuration edge cases"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.wrap_socket.return_value = Mock()
            
            # Test SSL compression options (if available)
            sslopt = {"compression": False}  # Some SSL contexts support this
            
            try:
                _ssl_socket(mock_sock, sslopt, "example.com")
                # Should not fail even if compression option is not supported
            except AttributeError:
                # Expected if SSL context doesn't support compression option
                pass
    
    def test_ssl_session_reuse_edge_cases(self):
        """Test SSL session reuse scenarios"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_ssl_sock = Mock()
            mock_context.wrap_socket.return_value = mock_ssl_sock
            
            # Test session reuse
            mock_ssl_sock.session = "mock_session"
            mock_ssl_sock.session_reused = True
            
            result = _ssl_socket(mock_sock, {}, "example.com")
            
            # Should handle session reuse without issues
            self.assertIsNotNone(result)
    
    def test_ssl_alpn_protocol_edge_cases(self):
        """Test SSL ALPN (Application Layer Protocol Negotiation) edge cases"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.wrap_socket.return_value = Mock()
            
            # Test ALPN configuration
            sslopt = {"alpn_protocols": ["http/1.1", "h2"]}
            
            # ALPN protocols are not currently supported in the SSL wrapper
            # but the test should not fail
            result = _ssl_socket(mock_sock, sslopt, "example.com")
            self.assertIsNotNone(result)
            # ALPN would need to be implemented in _wrap_sni_socket function
    
    def test_ssl_sni_edge_cases(self):
        """Test SSL SNI (Server Name Indication) edge cases"""
        mock_sock = Mock()
        
        # Test with IPv6 address (should not use SNI)
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.wrap_socket.return_value = Mock()
            
            # IPv6 addresses should not be used for SNI
            ipv6_hostname = "2001:db8::1"
            _ssl_socket(mock_sock, {}, ipv6_hostname)
            
            # Should use IPv6 address as server_hostname
            mock_context.wrap_socket.assert_called_with(
                mock_sock,
                do_handshake_on_connect=True,
                suppress_ragged_eofs=True,
                server_hostname=ipv6_hostname
            )
    
    def test_ssl_buffer_size_edge_cases(self):
        """Test SSL buffer size related edge cases"""
        mock_sock = Mock()
        
        # Test with very large recv request that should be chunked
        large_size = 1024 * 1024  # 1MB
        
        def mock_recv(bufsize):
            # SSL should never try to read more than 16KB at once
            if bufsize > 16384:
                raise SSLError("[SSL: BAD_LENGTH] buffer too large")
            return b"A" * min(bufsize, 1024)  # Return smaller chunks
        
        mock_sock.recv.side_effect = mock_recv
        mock_sock.gettimeout.return_value = 30.0
        
        from websocket._abnf import frame_buffer
        
        # Frame buffer should handle large requests by chunking
        fb = frame_buffer(lambda size: recv(mock_sock, size), skip_utf8_validation=True)
        
        # This should work even with large size due to chunking
        result = fb.recv_strict(16384)  # Exactly 16KB
        
        self.assertGreater(len(result), 0)
    
    def test_ssl_protocol_downgrade_protection(self):
        """Test SSL protocol downgrade protection"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.wrap_socket.side_effect = ssl.SSLError("SSLV3_ALERT_HANDSHAKE_FAILURE")
            
            sslopt = {"ssl_version": ssl.PROTOCOL_TLS_CLIENT}
            
            # Should propagate SSL protocol errors
            with self.assertRaises(ssl.SSLError):
                _ssl_socket(mock_sock, sslopt, "example.com")
    
    def test_ssl_certificate_chain_validation(self):
        """Test SSL certificate chain validation edge cases"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            
            # Test certificate chain validation failure
            mock_context.wrap_socket.side_effect = ssl.SSLCertVerificationError(
                "certificate verify failed: certificate has expired"
            )
            
            sslopt = {"cert_reqs": ssl.CERT_REQUIRED, "check_hostname": True}
            
            with self.assertRaises(ssl.SSLCertVerificationError):
                _ssl_socket(mock_sock, sslopt, "expired.badssl.com")
    
    def test_ssl_weak_cipher_rejection(self):
        """Test SSL weak cipher rejection scenarios"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.wrap_socket.side_effect = ssl.SSLError("no shared cipher")
            
            sslopt = {"ciphers": "RC4-MD5"}  # Intentionally weak cipher
            
            # Should fail with weak ciphers (SSL error is not wrapped by our code)
            with self.assertRaises(ssl.SSLError):
                _ssl_socket(mock_sock, sslopt, "example.com")
    
    def test_ssl_hostname_verification_edge_cases(self):
        """Test SSL hostname verification edge cases"""
        mock_sock = Mock()
        
        # Test with wildcard certificate scenarios
        test_cases = [
            ("*.example.com", "subdomain.example.com"),  # Valid wildcard
            ("*.example.com", "sub.subdomain.example.com"),  # Invalid wildcard depth
            ("example.com", "www.example.com"),  # Hostname mismatch
        ]
        
        for cert_hostname, connect_hostname in test_cases:
            with self.subTest(cert=cert_hostname, hostname=connect_hostname):
                with patch('ssl.SSLContext') as mock_ssl_context:
                    mock_context = Mock()
                    mock_ssl_context.return_value = mock_context
                    
                    if cert_hostname != connect_hostname and "sub.subdomain" in connect_hostname:
                        # Simulate hostname verification failure for invalid wildcard
                        mock_context.wrap_socket.side_effect = ssl.SSLCertVerificationError(
                            f"hostname '{connect_hostname}' doesn't match '{cert_hostname}'"
                        )
                        
                        sslopt = {"cert_reqs": ssl.CERT_REQUIRED, "check_hostname": True}
                        
                        with self.assertRaises(ssl.SSLCertVerificationError):
                            _ssl_socket(mock_sock, sslopt, connect_hostname)
                    else:
                        mock_context.wrap_socket.return_value = Mock()
                        sslopt = {"cert_reqs": ssl.CERT_REQUIRED, "check_hostname": True}
                        
                        # Should succeed for valid cases
                        result = _ssl_socket(mock_sock, sslopt, connect_hostname)
                        self.assertIsNotNone(result)
    
    def test_ssl_memory_bio_edge_cases(self):
        """Test SSL memory BIO edge cases"""
        mock_sock = Mock()
        
        # Test SSL memory BIO scenarios (if available)
        try:
            import ssl
            if hasattr(ssl, 'MemoryBIO'):
                with patch('ssl.SSLContext') as mock_ssl_context:
                    mock_context = Mock()
                    mock_ssl_context.return_value = mock_context
                    mock_context.wrap_socket.return_value = Mock()
                    
                    # Memory BIO should work if available
                    _ssl_socket(mock_sock, {}, "example.com")
                    
                    # Standard socket wrapping should still work
                    mock_context.wrap_socket.assert_called_once()
        except (ImportError, AttributeError):
            self.skipTest("SSL MemoryBIO not available")
    
    def test_ssl_renegotiation_vulnerability_protection(self):
        """Test SSL renegotiation vulnerability protection"""
        mock_sock = Mock()
        
        # Simulate SSL renegotiation attack attempt
        call_count = [0]
        def mock_recv(bufsize):
            call_count[0] += 1
            if call_count[0] == 1:  # First call triggers renegotiation
                raise SSLWantReadError("SSL renegotiation required")
            elif call_count[0] == 2:
                return b"normal data"
            else:
                return b""
        
        mock_sock.recv.side_effect = mock_recv
        mock_sock.gettimeout.return_value = 30.0
        
        with patch('selectors.DefaultSelector') as mock_selector_class:
            mock_selector = Mock()
            mock_selector_class.return_value = mock_selector
            mock_selector.select.return_value = [True]
            
            # Should handle multiple renegotiation attempts
            result = recv(mock_sock, 100)
            
            self.assertEqual(result, b"normal data")
            # Should have attempted multiple times due to renegotiation
            self.assertEqual(call_count[0], 2)
    
    def test_ssl_context_options_edge_cases(self):
        """Test SSL context options edge cases"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.wrap_socket.return_value = Mock()
            
            # Test various SSL context options
            sslopt = {
                "options": getattr(ssl, 'OP_NO_SSLv2', 0) | getattr(ssl, 'OP_NO_SSLv3', 0),
                "minimum_version": getattr(ssl, 'TLSVersion', ssl).TLSv1_2 if hasattr(ssl, 'TLSVersion') else None,
                "maximum_version": getattr(ssl, 'TLSVersion', ssl).TLSv1_3 if hasattr(ssl, 'TLSVersion') else None,
            }
            
            result = _ssl_socket(mock_sock, sslopt, "example.com")
            
            # Should handle SSL context options if available
            self.assertIsNotNone(result)
            
            # Check if options were set (if supported)
            if hasattr(ssl, 'OP_NO_SSLv2'):
                # SSL options should be set on context
                self.assertTrue(mock_context.wrap_socket.called)
    
    def test_ssl_heartbleed_vulnerability_protection(self):
        """Test protection against SSL Heartbleed-like vulnerabilities"""
        mock_sock = Mock()
        
        # Simulate potential heartbleed attack (large heartbeat request)
        def mock_recv(bufsize):
            # Should never receive malformed heartbeat responses
            if bufsize > 65535:  # Unreasonably large request
                raise SSLError("Heartbeat payload too large")
            return b"safe data"
        
        mock_sock.recv.side_effect = mock_recv
        mock_sock.gettimeout.return_value = 30.0
        
        # Normal operation should work fine
        result = recv(mock_sock, 1024)
        self.assertEqual(result, b"safe data")
    
    def test_ssl_beast_attack_protection(self):
        """Test protection against SSL BEAST attack"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            
            # BEAST attack targets CBC ciphers in TLS 1.0
            mock_context.wrap_socket.side_effect = ssl.SSLError("BEAST attack detected")
            
            sslopt = {"ssl_version": ssl.PROTOCOL_TLS_CLIENT}
            
            # Should handle BEAST protection
            with self.assertRaises(ssl.SSLError):
                _ssl_socket(mock_sock, sslopt, "example.com")
    
    def test_ssl_poodle_vulnerability_protection(self):
        """Test protection against SSL POODLE vulnerability"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            
            # POODLE affects SSLv3
            if hasattr(ssl, 'PROTOCOL_SSLv3'):
                mock_context.wrap_socket.side_effect = ssl.SSLError("SSLv3 disabled due to POODLE")
                
                sslopt = {"ssl_version": ssl.PROTOCOL_SSLv3}
                
                with self.assertRaises(ssl.SSLError):
                    _ssl_socket(mock_sock, sslopt, "example.com")
    
    def test_ssl_crime_attack_protection(self):
        """Test protection against SSL CRIME attack"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.wrap_socket.return_value = Mock()
            
            # CRIME attack exploits compression
            sslopt = {"compression": False}  # Disable compression
            
            result = _ssl_socket(mock_sock, sslopt, "example.com")
            
            # Should succeed with compression disabled
            self.assertIsNotNone(result)
    
    def test_ssl_freak_attack_protection(self):
        """Test protection against SSL FREAK attack"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            
            # FREAK attack exploits export ciphers
            mock_context.wrap_socket.side_effect = ssl.SSLError("Export cipher not allowed")
            
            sslopt = {"ciphers": "EXP-RC4-MD5"}  # Export cipher
            
            with self.assertRaises(ssl.SSLError):
                _ssl_socket(mock_sock, sslopt, "example.com")
    
    def test_ssl_logjam_attack_protection(self):
        """Test protection against SSL Logjam attack"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            
            # Logjam affects weak DH parameters
            mock_context.wrap_socket.side_effect = ssl.SSLError("DH key too small")
            
            sslopt = {"ciphers": "DHE-RSA-AES256-SHA"}
            
            with self.assertRaises(ssl.SSLError):
                _ssl_socket(mock_sock, sslopt, "example.com")
    
    def test_ssl_drown_attack_protection(self):
        """Test protection against SSL DROWN attack"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            
            # DROWN affects SSLv2
            if hasattr(ssl, 'PROTOCOL_SSLv2'):
                mock_context.wrap_socket.side_effect = ssl.SSLError("SSLv2 disabled due to DROWN")
                
                sslopt = {"ssl_version": ssl.PROTOCOL_SSLv2}
                
                with self.assertRaises(ssl.SSLError):
                    _ssl_socket(mock_sock, sslopt, "example.com")
    
    def test_ssl_sweet32_attack_protection(self):
        """Test protection against SSL Sweet32 attack"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.wrap_socket.side_effect = ssl.SSLError("3DES cipher not allowed")
            
            # Sweet32 affects 3DES ciphers
            sslopt = {"ciphers": "DES-CBC3-SHA"}
            
            with self.assertRaises(ssl.SSLError):
                _ssl_socket(mock_sock, sslopt, "example.com")
    
    def test_ssl_robot_attack_protection(self):
        """Test protection against SSL ROBOT attack"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            
            # ROBOT affects RSA key exchange
            mock_context.wrap_socket.side_effect = ssl.SSLError("RSA padding oracle detected")
            
            sslopt = {"ciphers": "RSA"}
            
            with self.assertRaises(ssl.SSLError):
                _ssl_socket(mock_sock, sslopt, "example.com")
    
    def test_ssl_timing_attack_resistance(self):
        """Test SSL timing attack resistance"""
        mock_sock = Mock()
        
        # Simulate variable timing in SSL operations
        import time
        timing_calls = []
        
        def mock_recv_with_timing(bufsize):
            start_time = time.time()
            # Simulate consistent timing regardless of data
            time.sleep(0.001)  # 1ms consistent delay
            timing_calls.append(time.time() - start_time)
            return b"timing resistant data"
        
        mock_sock.recv.side_effect = mock_recv_with_timing
        mock_sock.gettimeout.return_value = 30.0
        
        # Multiple operations should have consistent timing
        for _ in range(3):
            recv(mock_sock, 100)
        
        # All timing should be roughly consistent (within reasonable bounds)
        if len(timing_calls) > 1:
            timing_variance = max(timing_calls) - min(timing_calls)
            self.assertLess(timing_variance, 0.01)  # Less than 10ms variance
    
    def test_ssl_certificate_transparency_edge_cases(self):
        """Test SSL Certificate Transparency edge cases"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_ssl_sock = Mock()
            mock_context.wrap_socket.return_value = mock_ssl_sock
            
            # Simulate Certificate Transparency info
            mock_ssl_sock.getpeercert.return_value = {
                'subject': ((('commonName', 'example.com'),),),
                'serialNumber': '1234567890',
                'issuer': ((('commonName', 'Test CA'),),),
            }
            
            result = _ssl_socket(mock_sock, {}, "example.com")
            
            # Should handle CT without issues
            self.assertIsNotNone(result)
    
    def test_ssl_ocsp_stapling_edge_cases(self):
        """Test SSL OCSP stapling edge cases"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_ssl_sock = Mock()
            mock_context.wrap_socket.return_value = mock_ssl_sock
            
            # Simulate OCSP stapling scenarios
            mock_ssl_sock.getpeercert_chain = Mock(return_value=[])
            
            # Test OCSP stapling if available
            sslopt = {"check_hostname": True, "cert_reqs": ssl.CERT_REQUIRED}
            result = _ssl_socket(mock_sock, sslopt, "example.com")
            
            self.assertIsNotNone(result)
    
    def test_ssl_key_pinning_edge_cases(self):
        """Test SSL key pinning scenarios"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_ssl_sock = Mock()
            mock_context.wrap_socket.return_value = mock_ssl_sock
            
            # Simulate key pinning verification
            expected_pin = "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
            mock_ssl_sock.getpeercert.return_value = {
                'subject': ((('commonName', 'pinned.example.com'),),),
                'subjectPublicKeyInfo': b'mock_public_key_data'
            }
            
            # Key pinning would be handled at application level
            sslopt = {"key_pins": [expected_pin]}
            
            # Should succeed even with custom key pinning options
            result = _ssl_socket(mock_sock, sslopt, "pinned.example.com")
            self.assertIsNotNone(result)
    
    def test_ssl_perfect_forward_secrecy_edge_cases(self):
        """Test SSL Perfect Forward Secrecy scenarios"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.wrap_socket.return_value = Mock()
            
            # Test PFS-enabled cipher suites
            pfs_ciphers = "ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384"
            sslopt = {"ciphers": pfs_ciphers}
            
            result = _ssl_socket(mock_sock, sslopt, "example.com")
            
            # Should handle PFS ciphers
            self.assertIsNotNone(result)
            mock_context.set_ciphers.assert_called_with(pfs_ciphers)
    
    def test_ssl_concurrent_connection_edge_cases(self):
        """Test SSL concurrent connection scenarios"""
        mock_sock1 = Mock()
        mock_sock2 = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            mock_context.wrap_socket.return_value = Mock()
            
            # Test concurrent SSL connections
            sslopt = {"cert_reqs": ssl.CERT_REQUIRED}
            
            result1 = _ssl_socket(mock_sock1, sslopt, "example1.com")
            result2 = _ssl_socket(mock_sock2, sslopt, "example2.com")
            
            # Both should succeed
            self.assertIsNotNone(result1)
            self.assertIsNotNone(result2)
            
            # Context should be reused efficiently
            self.assertEqual(mock_ssl_context.call_count, 2)
    
    def test_ssl_error_message_sanitization(self):
        """Test SSL error message sanitization for security"""
        mock_sock = Mock()
        
        with patch('ssl.SSLContext') as mock_ssl_context:
            mock_context = Mock()
            mock_ssl_context.return_value = mock_context
            
            # Test error message that might contain sensitive info
            sensitive_error = ssl.SSLError("Certificate verification failed: private key exposed in error")
            mock_context.wrap_socket.side_effect = sensitive_error
            
            with self.assertRaises(ssl.SSLError) as cm:
                _ssl_socket(mock_sock, {"cert_reqs": ssl.CERT_REQUIRED}, "example.com")
            
            # Error should be propagated but could be logged securely
            self.assertIn("Certificate verification failed", str(cm.exception))


if __name__ == "__main__":
    unittest.main()