"""
Official Manufacturer Domain Whitelist and Verification Guard.

Enforces the challenge rule:
Only official manufacturer product pages and spec sheets may be ingested.
Marketplaces, distributors, and third-party aggregator sites are rejected.
"""

from urllib.parse import urlparse
from typing import Tuple, Set

# Whitelist of verified, official manufacturer domain suffixes and hosts
OFFICIAL_MANUFACTURER_DOMAINS: Set[str] = {
    # Appliance Manufacturers
    "frigidaire.com",
    "electrolux.com",
    "electroluxappliances.com",
    "whirlpool.com",
    "whirlpoolcorp.com",
    "bosch-home.com",
    "bosch-home.com/us",
    "boschtools.com",
    "geappliances.com",
    "kitchenaid.com",
    "maytag.com",
    "lg.com",
    "samsung.com",
    "haier.com",
    
    # Power Tools & Industrial Abrasives
    "milwaukeetool.com",
    "diablotools.com",
    "freudtools.com",
    "dewalt.com",
    "makitatools.com",
    "3m.com",
    "nortonabrasives.com",
    
    # Lighting & Electrical
    "lighting.philips.com",
    "signify.com",
    "lutron.com",
    "hubbell.com",
    "eaton.com",
    "schneider-electric.com",
    
    # Building Materials & Decking
    "trex.com",
    "timbertech.com",
    "jameshardie.com",
    "owenscorning.com",
    
    # Plumbing, Fittings, Valves & Faucets
    "nibco.com",
    "sharkbite.com",
    "rwc.com",
    "moen.com",
    "kohler.com",
    "deltafaucet.com",
    "watts.com",
    "viega.us",
    "zurn.com",
    "muellerindustries.com",
}

# Explicit blacklist of prohibited marketplace and distributor domains
FORBIDDEN_MARKETPLACE_DOMAINS: Set[str] = {
    "amazon.com",
    "homedepot.com",
    "lowes.com",
    "ebay.com",
    "walmart.com",
    "wayfair.com",
    "target.com",
    "grainger.com",
    "mcmaster.com",
    "mscdirect.com",
    "ferguson.com",
    "build.com",
    "appliancesconnection.com",
    "ajmadison.com",
    "alibaba.com",
    "aliexpress.com",
}


def is_official_manufacturer_url(url: str) -> Tuple[bool, str]:
    """
    Validate whether a URL belongs strictly to an authoritative manufacturer domain.
    
    Returns:
        (is_valid: bool, reason: str)
    """
    if not url or not isinstance(url, str):
        return False, "Empty or invalid URL provided."

    parsed = urlparse(url.strip())
    netloc = parsed.netloc.lower()
    
    # Strip port if present
    if ":" in netloc:
        netloc = netloc.split(":")[0]

    # Strip 'www.' prefix
    clean_host = netloc
    if clean_host.startswith("www."):
        clean_host = clean_host[4:]

    # Check forbidden marketplace list
    for forbidden in FORBIDDEN_MARKETPLACE_DOMAINS:
        if clean_host == forbidden or clean_host.endswith(f".{forbidden}"):
            return False, f"Prohibited source: '{clean_host}' is a third-party marketplace or distributor, not an official manufacturer."

    # Check official manufacturer whitelist
    for allowed in OFFICIAL_MANUFACTURER_DOMAINS:
        if clean_host == allowed or clean_host.endswith(f".{allowed}"):
            return True, f"Verified official manufacturer domain: '{allowed}'"

    return False, f"Untrusted domain: '{clean_host}' is not in the verified official manufacturer domain whitelist."
