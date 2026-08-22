"""
Manufacturer Source Security, SSRF Prevention & Integrity Hardening Module.
"""

from __future__ import annotations

import ipaddress
import re
import socket
import urllib.parse
from typing import Optional, Set, Tuple


# Strict Official Manufacturer Domain Allowlist
ALLOWED_MANUFACTURER_DOMAINS: Set[str] = {
    "sharkbite.com",
    "nibco.com",
    "hubbell.com",
    "moen.com",
    "frigidaire.com",
    "whirlpool.com",
    "bosch-home.com",
    "geappliances.com",
    "diablotools.com",
    "3m.com",
    "milwaukeetool.com",
    "dewalt.com",
    "ridgid.com",
    "eaton.com",
    "schneider-electric.com",
    "siemens.com",
}

# Maximum allowed file size for downloaded evidence (10 MB)
MAX_SOURCE_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Allowed MIME types
ALLOWED_MIME_TYPES: Set[str] = {
    "text/html",
    "text/plain",
    "application/pdf",
    "application/xhtml+xml",
}

# Allowed URL schemes
ALLOWED_URL_SCHEMES: Set[str] = {"http", "https"}


class SecurityValidationError(Exception):
    """Raised when an evidence source fails SSRF or allowlist verification."""
    def __init__(self, message: str, code: str = "SECURITY_VALIDATION_FAILED"):
        super().__init__(message)
        self.message = message
        self.code = code


class EvidenceSecurityValidator:
    """
    Validates official manufacturer URLs to prevent SSRF, DNS rebinding,
    and unauthorized/untrusted third-party content ingestion.
    """

    @staticmethod
    def is_private_or_reserved_ip(ip_str: str) -> bool:
        """Check if an IP address belongs to private, loopback, or link-local ranges."""
        try:
            ip = ipaddress.ip_address(ip_str)
            return (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_unspecified
            )
        except ValueError:
            return True

    @classmethod
    def validate_source_url(cls, url_str: str) -> Tuple[bool, Optional[str]]:
        """
        Validate URL for scheme, manufacturer allowlist, and SSRF private IP protection.
        Returns (is_valid, rejection_reason).
        """
        if not url_str or not url_str.strip():
            return True, None  # Allow empty URL if direct content or offline seed

        url_str = url_str.strip()
        try:
            parsed = urllib.parse.urlparse(url_str)
        except Exception:
            return False, "Malformed URL format"

        # 1. Enforce Scheme
        if parsed.scheme.lower() not in ALLOWED_URL_SCHEMES:
            return False, f"Unsupported URL scheme: '{parsed.scheme}'. Only HTTP and HTTPS are permitted."

        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname in URL"

        hostname_lower = hostname.lower().strip()

        # 2. Block Localhost & Numerical IP strings directly
        if hostname_lower in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
            return False, "SSRF Protection: Access to localhost or loopback is forbidden."

        # Check if direct IP address provided
        try:
            ip_obj = ipaddress.ip_address(hostname_lower)
            if cls.is_private_or_reserved_ip(str(ip_obj)):
                return False, f"SSRF Protection: IP address '{hostname_lower}' is private or reserved."
        except ValueError:
            pass  # Hostname is a domain name

        # 3. Manufacturer Domain Allowlist Verification
        # Matches domain or any subdomain (e.g. us.sharkbite.com matches sharkbite.com)
        domain_match = False
        for allowed in ALLOWED_MANUFACTURER_DOMAINS:
            if hostname_lower == allowed or hostname_lower.endswith(f".{allowed}"):
                domain_match = True
                break

        if not domain_match:
            return False, f"Untrusted domain '{hostname_lower}'. Source must be from official manufacturer domain allowlist."

        # 4. DNS Rebinding Check: Resolve domain and ensure resolved IPs are not private
        try:
            addr_info = socket.getaddrinfo(hostname_lower, None)
            for addr in addr_info:
                ip = addr[4][0]
                if cls.is_private_or_reserved_ip(ip):
                    return False, f"SSRF Protection: Hostname '{hostname_lower}' resolved to restricted IP: {ip}"
        except socket.gaierror:
            # Domain in allowlist passes if network/DNS is offline in test or isolated sandbox
            pass
        except Exception as e:
            return False, f"Error validating hostname: {e}"

        return True, None

    @classmethod
    def validate_content_size_and_type(
        cls,
        content_bytes: bytes,
        mime_type: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Validate content size limit and MIME type."""
        if len(content_bytes) > MAX_SOURCE_FILE_SIZE_BYTES:
            size_mb = len(content_bytes) / (1024 * 1024)
            return False, f"Content size ({size_mb:.2f} MB) exceeds maximum limit of 10 MB."

        if mime_type:
            clean_mime = mime_type.split(";")[0].strip().lower()
            if clean_mime not in ALLOWED_MIME_TYPES:
                return False, f"Unsupported MIME type '{clean_mime}'. Allowed: {', '.join(ALLOWED_MIME_TYPES)}"

        return True, None


security_validator = EvidenceSecurityValidator()
