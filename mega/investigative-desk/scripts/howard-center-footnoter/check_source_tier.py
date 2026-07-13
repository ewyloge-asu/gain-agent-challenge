#!/usr/bin/env python3
"""
check_source_tier.py — Classify a URL by source tier per the Howard Center's
                       primary-source priority rule.

Usage:
    python check_source_tier.py <URL> [<URL> ...]
    cat urls.txt | python check_source_tier.py -

Emits a JSON list, one record per URL:
    {
      "url": "https://...",
      "tier": "primary" | "authoritative_secondary" | "unacceptable" | "unknown",
      "rationale": "Matched *.gov pattern",
      "domain": "lda.senate.gov"
    }

When the tier is "unknown", the URL didn't match any of the curated patterns
in references/primary_source_priority.md. In that case the agent must apply
judgment: read the page, identify the publisher, and classify by hand.

This script never makes a network request. It only looks at the URL string.
"""

import argparse
import json
import re
import sys
from urllib.parse import urlparse


# --- Pattern tables (synced with references/primary_source_priority.md) ----

# Each entry: (regex pattern on full hostname, tier, rationale)
PATTERNS: list[tuple[re.Pattern, str, str]] = [
    # ---- Tier 1: primary sources -----------------------------------------
    (re.compile(r"^(?:[\w-]+\.)*sec\.gov$"), "primary", "SEC / EDGAR — issuer's official filings"),
    (re.compile(r"^(?:[\w-]+\.)*congress\.gov$"), "primary", "Congress.gov — official bill text and votes"),
    (re.compile(r"^(?:[\w-]+\.)*senate\.gov$"), "primary", "U.S. Senate official site"),
    (re.compile(r"^(?:[\w-]+\.)*house\.gov$"), "primary", "U.S. House official site"),
    (re.compile(r"^(?:[\w-]+\.)*supremecourt\.gov$"), "primary", "Supreme Court of the United States"),
    (re.compile(r"^(?:[\w-]+\.)*uscourts\.gov$"), "primary", "Federal courts / PACER"),
    (re.compile(r"^courtlistener\.com$|^(?:[\w-]+\.)*courtlistener\.com$"), "primary", "CourtListener — federal court dockets"),
    (re.compile(r"^federalregister\.gov$|^(?:[\w-]+\.)*federalregister\.gov$"), "primary", "Federal Register — rulemaking notices"),
    (re.compile(r"^gao\.gov$|^(?:[\w-]+\.)*gao\.gov$"), "primary", "Government Accountability Office"),
    (re.compile(r"^bls\.gov$|^(?:[\w-]+\.)*bls\.gov$"), "primary", "Bureau of Labor Statistics"),
    (re.compile(r"^census\.gov$|^(?:[\w-]+\.)*census\.gov$"), "primary", "U.S. Census Bureau"),
    (re.compile(r"^cdc\.gov$|^(?:[\w-]+\.)*cdc\.gov$"), "primary", "Centers for Disease Control"),
    (re.compile(r"^nih\.gov$|^(?:[\w-]+\.)*nih\.gov$"), "primary", "National Institutes of Health"),
    (re.compile(r"^lda\.senate\.gov$"), "primary", "Senate LDA — lobbying disclosures"),
    (re.compile(r"^(?:[\w-]+\.)*\.gov$|^[\w-]+\.gov$"), "primary", "U.S. government .gov domain"),
    (re.compile(r"^(?:[\w-]+\.)*\.mil$|^[\w-]+\.mil$"), "primary", "U.S. military .mil domain"),
    (re.compile(r"^(?:[\w-]+\.)*\.gc\.ca$"), "primary", "Government of Canada"),
    (re.compile(r"^(?:[\w-]+\.)*\.gov\.uk$"), "primary", "UK government"),
    (re.compile(r"^(?:[\w-]+\.)*europa\.eu$"), "primary", "European Union official"),
    (re.compile(r"^un\.org$|^(?:[\w-]+\.)*un\.org$"), "primary", "United Nations"),
    (re.compile(r"^who\.int$|^(?:[\w-]+\.)*who\.int$"), "primary", "World Health Organization"),
    (re.compile(r"^imf\.org$|^(?:[\w-]+\.)*imf\.org$"), "primary", "International Monetary Fund"),
    (re.compile(r"^worldbank\.org$|^(?:[\w-]+\.)*worldbank\.org$"), "primary", "World Bank"),
    (re.compile(r"^oecd\.org$|^(?:[\w-]+\.)*oecd\.org$"), "primary", "OECD"),
    (re.compile(r"^iaea\.org$|^(?:[\w-]+\.)*iaea\.org$"), "primary", "International Atomic Energy Agency"),

    # ---- Tier 2: authoritative secondary ---------------------------------
    (re.compile(r"^reuters\.com$|^(?:[\w-]+\.)*reuters\.com$"), "authoritative_secondary", "Reuters"),
    (re.compile(r"^apnews\.com$|^(?:[\w-]+\.)*apnews\.com$"), "authoritative_secondary", "Associated Press"),
    (re.compile(r"^nytimes\.com$|^(?:[\w-]+\.)*nytimes\.com$"), "authoritative_secondary", "The New York Times"),
    (re.compile(r"^washingtonpost\.com$|^(?:[\w-]+\.)*washingtonpost\.com$"), "authoritative_secondary", "The Washington Post"),
    (re.compile(r"^wsj\.com$|^(?:[\w-]+\.)*wsj\.com$"), "authoritative_secondary", "The Wall Street Journal"),
    (re.compile(r"^bloomberg\.com$|^(?:[\w-]+\.)*bloomberg\.com$"), "authoritative_secondary", "Bloomberg"),
    (re.compile(r"^ft\.com$|^(?:[\w-]+\.)*ft\.com$"), "authoritative_secondary", "Financial Times"),
    (re.compile(r"^propublica\.org$|^(?:[\w-]+\.)*propublica\.org$"), "authoritative_secondary", "ProPublica"),
    (re.compile(r"^npr\.org$|^(?:[\w-]+\.)*npr\.org$"), "authoritative_secondary", "NPR"),
    (re.compile(r"^pbs\.org$|^(?:[\w-]+\.)*pbs\.org$"), "authoritative_secondary", "PBS / NewsHour / Frontline"),
    (re.compile(r"^bbc\.(?:com|co\.uk)$|^(?:[\w-]+\.)*bbc\.(?:com|co\.uk)$"), "authoritative_secondary", "BBC"),
    (re.compile(r"^cnn\.com$|^(?:[\w-]+\.)*cnn\.com$"), "authoritative_secondary", "CNN"),
    (re.compile(r"^politico\.com$|^(?:[\w-]+\.)*politico\.com$"), "authoritative_secondary", "Politico"),
    (re.compile(r"^axios\.com$|^(?:[\w-]+\.)*axios\.com$"), "authoritative_secondary", "Axios"),
    (re.compile(r"^theguardian\.com$|^(?:[\w-]+\.)*theguardian\.com$"), "authoritative_secondary", "The Guardian"),
    (re.compile(r"^brookings\.edu$|^(?:[\w-]+\.)*brookings\.edu$"), "authoritative_secondary", "Brookings Institution"),
    (re.compile(r"^pewresearch\.org$|^(?:[\w-]+\.)*pewresearch\.org$"), "authoritative_secondary", "Pew Research Center"),
    (re.compile(r"^rand\.org$|^(?:[\w-]+\.)*rand\.org$"), "authoritative_secondary", "RAND Corporation"),
    (re.compile(r"^urban\.org$|^(?:[\w-]+\.)*urban\.org$"), "authoritative_secondary", "Urban Institute"),
    (re.compile(r"^cbpp\.org$|^(?:[\w-]+\.)*cbpp\.org$"), "authoritative_secondary", "Center on Budget and Policy Priorities"),
    (re.compile(r"^kff\.org$|^(?:[\w-]+\.)*kff\.org$"), "authoritative_secondary", "KFF (formerly Kaiser Family Foundation)"),
    (re.compile(r"^nature\.com$|^(?:[\w-]+\.)*nature\.com$"), "authoritative_secondary", "Nature (journal)"),
    (re.compile(r"^science\.org$|^(?:[\w-]+\.)*science\.org$"), "authoritative_secondary", "Science (journal)"),
    (re.compile(r"^nejm\.org$|^(?:[\w-]+\.)*nejm\.org$"), "authoritative_secondary", "New England Journal of Medicine"),
    (re.compile(r"^thelancet\.com$|^(?:[\w-]+\.)*thelancet\.com$"), "authoritative_secondary", "The Lancet"),
    (re.compile(r"^jamanetwork\.com$|^(?:[\w-]+\.)*jamanetwork\.com$"), "authoritative_secondary", "JAMA"),
    (re.compile(r"^bostonglobe\.com$|^(?:[\w-]+\.)*bostonglobe\.com$"), "authoritative_secondary", "The Boston Globe"),
    (re.compile(r"^latimes\.com$|^(?:[\w-]+\.)*latimes\.com$"), "authoritative_secondary", "Los Angeles Times"),
    (re.compile(r"^chicagotribune\.com$|^(?:[\w-]+\.)*chicagotribune\.com$"), "authoritative_secondary", "Chicago Tribune"),

    # ---- Tier 3: unacceptable as a footnote endpoint ---------------------
    (re.compile(r"^(?:[\w-]+\.)*wikipedia\.org$"), "unacceptable", "Wikipedia — use as discovery tool, never as endpoint"),
    (re.compile(r"^(?:[\w-]+\.)*wiktionary\.org$"), "unacceptable", "Wiktionary"),
    (re.compile(r"^(?:[\w-]+\.)*fandom\.com$"), "unacceptable", "Fandom wikis"),
    (re.compile(r"^medium\.com$|^(?:[\w-]+\.)*medium\.com$"), "unacceptable", "Medium — not a primary source unless author IS the source"),
    (re.compile(r"^substack\.com$|^(?:[\w-]+\.)*substack\.com$"), "unacceptable", "Substack — not a primary source unless author IS the source"),
    (re.compile(r"^prnewswire\.com$|^(?:[\w-]+\.)*prnewswire\.com$"), "unacceptable", "PR Newswire — go to the issuer's own site"),
    (re.compile(r"^businesswire\.com$|^(?:[\w-]+\.)*businesswire\.com$"), "unacceptable", "Business Wire — go to the issuer's own site"),
    (re.compile(r"^globenewswire\.com$|^(?:[\w-]+\.)*globenewswire\.com$"), "unacceptable", "GlobeNewswire — go to the issuer's own site"),
    (re.compile(r"^news\.google\.com$"), "unacceptable", "Google News aggregator — strips attribution"),
    (re.compile(r"^news\.yahoo\.com$"), "unacceptable", "Yahoo News aggregator"),
    (re.compile(r"^quora\.com$|^(?:[\w-]+\.)*quora\.com$"), "unacceptable", "Quora — user-generated, not editorial"),
    (re.compile(r"^answers\.com$"), "unacceptable", "Answers.com — content farm"),
    (re.compile(r"^ehow\.com$|^(?:[\w-]+\.)*ehow\.com$"), "unacceptable", "eHow — content farm"),
]


def classify(url: str) -> dict:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    host = host.lower()
    if not host:
        return {
            "url": url,
            "tier": "unknown",
            "rationale": "Could not parse hostname from URL",
            "domain": "",
        }
    for pattern, tier, rationale in PATTERNS:
        if pattern.match(host):
            return {
                "url": url,
                "tier": tier,
                "rationale": rationale,
                "domain": host,
            }
    # Heuristic fallback: any .edu and not a known agg → likely Tier 2.
    if host.endswith(".edu"):
        return {
            "url": url,
            "tier": "authoritative_secondary",
            "rationale": ".edu domain — likely a university publication; verify the page is editorial, not a student blog",
            "domain": host,
        }
    # Any generic .org → unknown without further inspection.
    return {
        "url": url,
        "tier": "unknown",
        "rationale": ("No pattern match. Read the page to identify the publisher "
                      "and classify by hand using references/primary_source_priority.md."),
        "domain": host,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("urls", nargs="+",
                    help="URLs to classify, or '-' to read one per line from stdin")
    args = ap.parse_args()
    urls: list[str] = []
    for u in args.urls:
        if u == "-":
            urls.extend(line.strip() for line in sys.stdin if line.strip())
        else:
            urls.append(u)
    results = [classify(u) for u in urls]
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
