"""
File:
    aliases.py

Version:
    2.0.0

Phase:
    3

Status:
    IMPLEMENTING

Purpose:
    Maintain deterministic alias mappings for company names.

Responsibilities:
    - Store canonical company aliases in a private class constant
    - Provide lookup method to resolve aliases to canonical names
    - Trim whitespace before lookup

Dependencies:
    - None

This module does NOT:
    - Use fuzzy matching
    - Use regex
    - Use normalization
    - Use validation
    - Use database
    - Use API
    - Use logging
    - Use resolver logic
    - Use Playwright

PEP8:     Yes
SOLID:    Yes (Single Responsibility)
DRY:      Yes
KISS:     Yes
"""

from __future__ import annotations


class CompanyAliases:
    """
    Deterministic company alias resolver.

    Alias data is stored as a private class constant. This allows the
    data to be moved to an external file (e.g., identity/data/company_aliases.py)
    without changing the public API.

    Methods:
        resolve: Look up alias and return canonical company name.
    """

    # ------------------------------------------------------------------
    # Private Class Constants
    # ------------------------------------------------------------------

    _ALIASES: dict[str, str] = {
        # Google variants
        "google india": "google",
        "google llc": "google",
        "google inc": "google",
        "google corporation": "google",
        "alphabet": "google",
        "alphabet inc": "google",
        # TCS variants
        "tcs": "tata consultancy services",
        # IBM variants
        "ibm india": "ibm",
        "ibm corp": "ibm",
        "international business machines": "ibm",
        # Amazon variants
        "amazon web services": "amazon",
        "aws": "amazon",
        "amazon inc": "amazon",
        # Microsoft variants
        "microsoft india": "microsoft",
        "msft": "microsoft",
        # Infosys variants
        "infosys technologies": "infosys",
        # Wipro variants
        "wipro technologies": "wipro",
        # HCL variants
        "hcl technologies": "hcl",
        "hcl infosystems": "hcl",
        # Accenture variants
        "accenture india": "accenture",
        # Deloitte variants
        "deloitte india": "deloitte",
        # PwC variants
        "pwc india": "pwc",
        "pricewaterhousecoopers": "pwc",
        # EY variants
        "ey india": "ey",
        "ernst & young": "ey",
        # KPMG variants
        "kpmg india": "kpmg",
        # Oracle variants
        "oracle india": "oracle",
        # SAP variants
        "sap india": "sap",
        # Cisco variants
        "cisco india": "cisco",
        # Intel variants
        "intel india": "intel",
        # Meta variants
        "meta india": "meta",
        "facebook india": "meta",
        # Apple variants
        "apple inc": "apple",
        # Netflix variants
        "netflix india": "netflix",
        # Goldman Sachs variants
        "goldman sachs india": "goldman sachs",
        # JP Morgan variants
        "jpmorgan": "jpmorgan",
        "jp morgan": "jpmorgan",
        # Morgan Stanley variants
        "morgan stanley india": "morgan stanley",
        # Citi variants
        "citi india": "citi",
        "citibank": "citi",
    }

    def resolve(self, company: str) -> str:
        """
        Resolve alias to canonical company name.

        If the company name exists as a key in _ALIASES, return the
        canonical name. Otherwise, return the original company name.

        Args:
            company: Company name to resolve.

        Returns:
            str: Canonical company name.

        Examples:
            >>> resolver = CompanyAliases()
            >>> resolver.resolve("google india")
            "google"
            >>> resolver.resolve("tcs")
            "tata consultancy services"
            >>> resolver.resolve("unknown company")
            "unknown company"
        """
        if not company:
            return ""

        cleaned: str = company.strip()

        if not cleaned:
            return ""

        return self._ALIASES.get(cleaned, cleaned)


# =============================================================================
# END OF FILE
# =============================================================================