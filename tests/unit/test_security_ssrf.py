"""
Unit tests for Ingestion Security, SSRF Prevention & Domain Allowlists.
"""

import pytest
from src.evidence.security import EvidenceSecurityValidator, MAX_SOURCE_FILE_SIZE_BYTES


def test_reject_localhost_and_loopback():
    """Verify localhost, 127.0.0.1, and 0.0.0.0 are blocked by SSRF defenses."""
    bad_urls = [
        "http://localhost:8000/spec.pdf",
        "http://127.0.0.1:5000/internal",
        "http://0.0.0.0:8080/admin",
        "https://127.0.0.1/data",
    ]
    for url in bad_urls:
        is_valid, reason = EvidenceSecurityValidator.validate_source_url(url)
        assert is_valid is False
        assert "SSRF" in reason or "Untrusted" in reason or "Forbidden" in reason.lower()


def test_reject_private_and_link_local_ips():
    """Verify private IP addresses (RFC 1918) and link-local AWS metadata IPs are blocked."""
    private_urls = [
        "http://10.0.0.1/secrets.json",
        "http://192.168.1.1/router",
        "http://172.16.0.5/api",
        "http://169.254.169.254/latest/meta-data/",  # Cloud instance metadata
    ]
    for url in private_urls:
        is_valid, reason = EvidenceSecurityValidator.validate_source_url(url)
        assert is_valid is False
        assert "SSRF" in reason or "private" in reason.lower() or "Untrusted" in reason


def test_reject_unsupported_schemes():
    """Verify file://, ftp://, gopher:// schemes are rejected."""
    bad_schemes = [
        "file:///etc/passwd",
        "ftp://ftp.example.com/spec.pdf",
        "gopher://gopher.example.com",
    ]
    for url in bad_schemes:
        is_valid, reason = EvidenceSecurityValidator.validate_source_url(url)
        assert is_valid is False
        assert "Unsupported URL scheme" in reason


def test_reject_untrusted_third_party_domains():
    """Verify non-allowlisted third-party marketplaces or unknown domains are rejected."""
    untrusted_urls = [
        "https://www.ebay.com/itm/sharkbite-fitting",
        "https://www.amazon.com/dp/B00004",
        "https://random-distributor-blog.net/specs",
        "https://malicious-site.xyz/fake_spec.html",
    ]
    for url in untrusted_urls:
        is_valid, reason = EvidenceSecurityValidator.validate_source_url(url)
        assert is_valid is False
        assert "Untrusted domain" in reason


def test_allow_official_manufacturer_domains():
    """Verify official manufacturer domains pass security validation."""
    valid_urls = [
        "https://www.sharkbite.com/us/en/brass-push-to-connect/couplings/brass-push-straight-coupling-u008lfa",
        "https://www.nibco.com/fittings/copper-fittings/607-12-90-copper-elbow",
        "https://www.frigidaire.com/en/p/kitchen/dishwashers/built-in-dishwashers/PDSH4816AF",
        "https://www.diablotools.com/products/DCB518ASTS06G",
    ]
    for url in valid_urls:
        is_valid, reason = EvidenceSecurityValidator.validate_source_url(url)
        assert is_valid is True
        assert reason is None


def test_content_size_and_mime_type_validation():
    """Verify content size limits and MIME types."""
    # 1. Content within 10 MB limit
    small_bytes = b"<html>Test Spec</html>"
    valid, _ = EvidenceSecurityValidator.validate_content_size_and_type(small_bytes, "text/html")
    assert valid is True

    # 2. Content exceeding 10 MB limit
    huge_bytes = b"A" * (MAX_SOURCE_FILE_SIZE_BYTES + 1024)
    valid, reason = EvidenceSecurityValidator.validate_content_size_and_type(huge_bytes, "text/html")
    assert valid is False
    assert "exceeds maximum limit" in reason

    # 3. Disallowed MIME type (e.g. executable)
    valid, reason = EvidenceSecurityValidator.validate_content_size_and_type(small_bytes, "application/x-msdownload")
    assert valid is False
    assert "Unsupported MIME type" in reason
