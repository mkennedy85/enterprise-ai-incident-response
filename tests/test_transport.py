import json
from pathlib import Path
import ssl
import tempfile
import unittest
from unittest.mock import patch
from incident_agent.transport import create_tls_context
from incident_agent import client

class TransportTests(unittest.TestCase):
    def context_for(self, policy):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'tls.json';p.write_text(json.dumps(policy))
            return create_tls_context(p)
    def test_safe_default(self):
        c=create_tls_context()
        self.assertEqual(c.minimum_version, ssl.TLSVersion.TLSv1_2)
        self.assertEqual(c.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(c.check_hostname)
    def test_upgrade_without_client_change(self):
        c=self.context_for({'minimum_version':'TLSv1.3','tls12_cipher_policy':'modern-aead'})
        self.assertEqual(c.minimum_version, ssl.TLSVersion.TLSv1_3)
        self.assertTrue(c.check_hostname)
        self.assertEqual(c.verify_mode, ssl.CERT_REQUIRED)
    def test_unsafe_or_unknown_policy_rejected(self):
        for p in ({'minimum_version':'TLSv1'},{'minimum_version':'garbage'}, {}, [], {'minimum_version':[],'tls12_cipher_policy':'modern-aead'}, {'minimum_version':'TLSv1.2','verify':False}):
            with self.subTest(p=p), self.assertRaises(ValueError): self.context_for(p)
    def test_bad_policy_prevents_request(self):
        with patch.object(client,'require_key',return_value='unit-test-placeholder'), patch.object(client,'create_tls_context',side_effect=ValueError), patch.object(client,'urlopen') as send:
            with self.assertRaises(client.ModelError):client.complete({},1)
            send.assert_not_called()

    def test_cipher_change_is_configuration_only(self):
        c=self.context_for({'minimum_version':'TLSv1.2','tls12_cipher_policy':'aes256-gcm'})
        names=[x['name'] for x in c.get_ciphers() if x['protocol']!='TLSv1.3']
        self.assertTrue(names)
        self.assertTrue(all('AES256-GCM' in n and 'ECDHE' in n for n in names))

    def test_client_passes_verified_context(self):
        from unittest.mock import MagicMock
        response=MagicMock()
        response.__enter__.return_value.read.return_value=b'{"status":"completed","output":[{"type":"message","content":[{"type":"output_text","text":"{}"}]}]}'
        with patch.object(client,'require_key',return_value='unit-test-placeholder'), patch.object(client,'urlopen',return_value=response) as send:
            client.complete({},1)
        c=send.call_args.kwargs['context']
        self.assertTrue(c.check_hostname)
        self.assertEqual(c.verify_mode,ssl.CERT_REQUIRED)
