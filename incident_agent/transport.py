"""Central TLS policy. This is crypto-agility scaffolding, not a PQC claim."""
import json
from pathlib import Path
import ssl

POLICY = Path(__file__).resolve().parents[1] / 'config' / 'tls_policy.json'
ALLOWED_CIPHERS = {'modern-aead': 'ECDHE+AESGCM:ECDHE+CHACHA20', 'aes256-gcm': 'ECDHE+AESGCM+AES256'}
ALLOWED_MINIMUMS = {'TLSv1.2': ssl.TLSVersion.TLSv1_2, 'TLSv1.3': ssl.TLSVersion.TLSv1_3}

def create_tls_context(policy_path=POLICY):
    policy = json.loads(Path(policy_path).read_text())
    if (not isinstance(policy, dict) or set(policy) != {'minimum_version', 'tls12_cipher_policy'}
            or not isinstance(policy['minimum_version'], str)
            or not isinstance(policy['tls12_cipher_policy'], str)
            or policy['minimum_version'] not in ALLOWED_MINIMUMS
            or policy['tls12_cipher_policy'] not in ALLOWED_CIPHERS):
        raise ValueError('Invalid TLS minimum version or TLS 1.2 cipher policy')
    context = ssl.create_default_context()
    context.set_ciphers(ALLOWED_CIPHERS[policy['tls12_cipher_policy']])
    context.minimum_version = ALLOWED_MINIMUMS[policy['minimum_version']]
    # System CA trust, hostname checks and certificate validation stay mandatory.
    # Negotiated groups depend on the linked OpenSSL and peer; never infer PQC.
    return context
