"""Shared helpers for the lobbying-influence-investigator skill.

Stdlib-only by design so the skill is reproducible without extra installs.
Centralizes: path resolution, the SQLite schema, deterministic name
normalization, and provenance-id construction (every normalized row records
exactly where it came from so any downstream claim can be audited).
"""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
# DATA_DIR: the decompressed `data/` corpus described in data_manual.md.
# WORKDIR : where generated artifacts (the SQLite db, external snapshots,
#           the investigation state file) live. Both are overridable so the
#           skill runs on any machine / layout.

def data_dir() -> Path:
    return Path(os.environ.get("GAIN_DATA_DIR", "data")).expanduser().resolve()


def workdir() -> Path:
    wd = Path(os.environ.get("GAIN_WORKDIR", "build")).expanduser().resolve()
    wd.mkdir(parents=True, exist_ok=True)
    return wd


def db_path() -> Path:
    return Path(os.environ.get("GAIN_DB", str(workdir() / "influence.db"))).resolve()


def load_credentials() -> list[str]:
    """Load API keys from a gitignored credentials file into the environment so
    the connector can find them. Never overwrites an already-set env var.

    Search order (first existing file wins):
      1. $GAIN_CREDENTIALS (explicit path)
      2. ./credentials.env (current dir)
      3. <submission root>/credentials.env  (two levels up from scripts/)
      4. $GAIN_WORKDIR/credentials.env

    File format is simple KEY=VALUE lines; blank lines and #comments ignored.
    Returns the list of keys that were loaded (for diagnostics)."""
    candidates = []
    if os.environ.get("GAIN_CREDENTIALS"):
        candidates.append(Path(os.environ["GAIN_CREDENTIALS"]))
    candidates.append(Path.cwd() / "credentials.env")
    candidates.append(Path(__file__).resolve().parent.parent.parent / "credentials.env")
    candidates.append(workdir() / "credentials.env")
    loaded = []
    for p in candidates:
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v
                loaded.append(k)
        break
    return loaded


def connect(db: str | os.PathLike | None = None) -> sqlite3.Connection:
    p = Path(db) if db else db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(p))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=OFF")
    return con


# --------------------------------------------------------------------------
# Deterministic normalization
# --------------------------------------------------------------------------
_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[.,/#!$%^&*;:{}=_`~()\"']")
_ORG_SUFFIX = re.compile(
    r"\b(INCORPORATED|INC|CORPORATION|CORP|COMPANY|CO|LLC|L L C|LLP|LP|LTD|"
    r"PLLC|PC|PA|LIMITED|HOLDINGS|GROUP|THE)\b"
)
_TITLE = re.compile(
    r"^(SEN|SENATOR|REP|REPRESENTATIVE|CONG|CONGRESSMAN|CONGRESSWOMAN|"
    r"HON|HONORABLE|DR|MR|MRS|MS)\.?\s+"
)


def squash(s: str | None) -> str:
    """Lowercase-insensitive whitespace squash + uppercasing."""
    if not s:
        return ""
    return _WS.sub(" ", str(s)).strip().upper()


def norm_org(s: str | None) -> str:
    """Canonical-ish org key: uppercase, strip punctuation + common corporate
    suffixes so 'Comcast Corporation' and 'COMCAST CORP.' collapse together.
    Deterministic and dependency-free."""
    s = squash(s)
    if not s:
        return ""
    s = _PUNCT.sub(" ", s)
    s = _ORG_SUFFIX.sub(" ", s)
    return _WS.sub(" ", s).strip()


def strip_title(s: str | None) -> str:
    s = squash(s)
    while True:
        new = _TITLE.sub("", s)
        if new == s:
            return new
        s = new


def norm_person(s: str | None) -> str:
    """Canonical person key: drop honorific titles + punctuation.
    'Sen. Mark Warner' and 'Mark Warner' -> 'MARK WARNER'."""
    s = strip_title(s)
    s = _PUNCT.sub(" ", s)
    return _WS.sub(" ", s).strip()


_PAREN = re.compile(r"\([^)]*\)")


def lastname_key(s: str | None) -> str:
    """Best-effort person key 'LAST|FIRST'. Handles 'First Last', 'Last, First',
    honorific titles, and trailing party/state parentheticals like '(R-KY)'.
    Deterministic; used to link honoree_name -> member across spelling variants."""
    raw = squash(s)
    if not raw:
        return ""
    raw = _PAREN.sub(" ", raw)  # drop '(R)', '(R-KY)', etc.
    if "," in raw:
        # 'Last, First ...' form -> reorder
        last_part, _, rest = raw.partition(",")
        last_toks = norm_person(last_part).split()
        first_toks = norm_person(rest).split()
        last = last_toks[-1] if last_toks else ""
        first = first_toks[0] if first_toks else ""
        if last:
            return f"{last}|{first}" if first else last
    p = norm_person(raw)
    parts = p.split()
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return f"{parts[-1]}|{parts[0]}"


_CAMPAIGN_RX = [
    # "Guthrie for Congress", "Pete Ricketts for Senate", "Ken Calvert for
    # Congress Committee" — anchored so "…for Congressional Studies" never matches.
    re.compile(r"^(?:THE\s+)?(?:RE-?ELECT\s+)?(?P<cand>.+?)\s+FOR\s+"
               r"(?:U\.?\s*S\.?\s+)?(?:CONGRESS|SENATE)"
               r"(?:\s+(?:COMMITTEE|INC\.?))?$"),
    re.compile(r"^FRIENDS\s+OF\s+(?P<cand>.+)$"),
    re.compile(r"^(?:THE\s+)?COMMITTEE\s+TO\s+RE-?ELECT\s+(?P<cand>.+)$"),
]
_ORG_TOKENS = ("PAC", "COMMITTEE", "ASSOCIATION", "INSTITUTE", "FOUNDATION",
               "CAUCUS", "PARTY", "FUND")


def campaign_candidate_name(s: str | None) -> str | None:
    """Extract the candidate's personal name from a campaign-committee-style
    honoree ("Guthrie for Congress" -> "GUTHRIE"). Conservative: the extracted
    part must look like a short personal name, and callers should still require
    a unique member match before attributing money. Returns None if the string
    doesn't look like a campaign committee."""
    raw = squash(s)
    if not raw:
        return None
    raw = raw.rstrip(".").strip()
    for rx in _CAMPAIGN_RX:
        m = rx.match(raw)
        if not m:
            continue
        cand = m.group("cand").strip()
        toks = cand.split()
        if 0 < len(toks) <= 4 and not any(t in _ORG_TOKENS for t in toks):
            return cand
    return None


def to_float(v) -> float | None:
    if v in (None, "", "null"):
        return None
    try:
        return float(str(v).replace(",", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------------
# Policy-domain taxonomy (the "say <-> do" bridge)
# --------------------------------------------------------------------------
# One coarse, documented vocabulary that three different datasets can be mapped
# into so they become comparable:
#   - press-release free text  -> domains_in_text()      (keyword match)
#   - Congress.gov policy_area -> domain_for_policy_area() (controlled vocab)
#   - LDA ALI issue codes      -> domain_for_issue()       (3-letter codes)
# This is heuristic by design (like the industry tagger) and is labeled as such
# wherever it surfaces. The keyword lists favor longer, specific stems to keep
# false positives low; multi-domain releases are counted once per domain.

POLICY_DOMAINS = [
    "Health", "Taxes & Budget", "Energy & Environment",
    "Defense & Veterans", "Trade & Tariffs", "Finance & Banking",
    "Immigration", "Tech & Telecom", "Agriculture & Food",
    "Labor & Education", "Transportation & Infrastructure",
    "Justice & Civil Rights", "Foreign Affairs", "Government & Elections",
]

# Keyword stems per domain. Matched case-insensitively on word boundaries.
_DOMAIN_KEYWORDS = {
    "Health": [r"health", r"medicare", r"medicaid", r"hospital", r"prescription",
               r"pharmaceutical", r"\bpharma\b", r"opioid", r"fentanyl", r"medical",
               r"physician", r"\bnurse", r"drug pric", r"mental health", r"affordable care"],
    "Taxes & Budget": [r"\btax(?:es|ation|payer|able)?\b", r"budget", r"appropriation",
                       r"deficit", r"debt ceiling", r"\birs\b", r"fiscal", r"federal spending"],
    "Energy & Environment": [r"\benergy\b", r"\boil\b", r"pipeline", r"climate", r"emission",
                             r"renewable", r"\bsolar\b", r"nuclear", r"environment", r"\bepa\b",
                             r"drilling", r"power grid", r"natural gas", r"gasoline"],
    "Defense & Veterans": [r"defense", r"military", r"pentagon", r"\btroops\b",
                           r"national security", r"missile", r"armed forces", r"\bnavy\b",
                           r"\barmy\b", r"air force", r"veterans?", r"homeland security"],
    "Trade & Tariffs": [r"tariff", r"\btrade\b", r"\bimports?\b", r"\bexports?\b",
                        r"supply chain", r"\bwto\b"],
    "Finance & Banking": [r"\bbank", r"wall street", r"financial", r"securities and exchange",
                          r"\bcredit\b", r"mortgage", r"insurance", r"crypto", r"stablecoin",
                          r"interest rate"],
    "Immigration": [r"immigration", r"immigrant", r"\bborder\b", r"migrant", r"asylum",
                    r"deportation", r"\bdaca\b"],
    "Tech & Telecom": [r"broadband", r"internet", r"telecom", r"artificial intelligence",
                       r"\bai\b", r"semiconductor", r"social media", r"spectrum", r"\bcyber",
                       r"data privacy"],
    "Agriculture & Food": [r"\bfarm", r"agricultur", r"\bcrop", r"\branch", r"\bdairy",
                           r"\busda\b", r"food security"],
    "Labor & Education": [r"\bjobs\b", r"\bworkers?\b", r"\bunion\b", r"\blabor\b", r"\bwage",
                          r"\bschool", r"students?\b", r"education", r"teachers?\b",
                          r"\bcollege", r"tuition"],
    "Transportation & Infrastructure": [r"infrastructure", r"highway", r"\btransit\b",
                                        r"\brail", r"airport", r"aviation", r"\bbridge", r"\broads?\b"],
    "Justice & Civil Rights": [r"\bcrime", r"\bpolice\b", r"\bjustice\b", r"\bcourt",
                               r"\bguns?\b", r"second amendment", r"voting rights",
                               r"civil rights", r"abortion", r"supreme court"],
    "Foreign Affairs": [r"foreign", r"israel", r"ukraine", r"\bchina\b", r"russia", r"\biran\b",
                        r"\bnato\b", r"diplomacy", r"sanctions", r"taiwan"],
    "Government & Elections": [r"election", r"\bethics\b", r"shutdown", r"federal workforce",
                              r"oversight", r"\bdoge\b"],
}
_DOMAIN_RE = {d: re.compile("|".join(kws), re.I) for d, kws in _DOMAIN_KEYWORDS.items()}

# Congress.gov policy_area (controlled vocabulary) -> domain.
POLICY_AREA_TO_DOMAIN = {
    "Health": "Health",
    "Taxation": "Taxes & Budget",
    "Economics and Public Finance": "Taxes & Budget",
    "Energy": "Energy & Environment",
    "Environmental Protection": "Energy & Environment",
    "Public Lands and Natural Resources": "Energy & Environment",
    "Water Resources Development": "Energy & Environment",
    "Armed Forces and National Security": "Defense & Veterans",
    "Foreign Trade and International Finance": "Trade & Tariffs",
    "International Affairs": "Foreign Affairs",
    "Finance and Financial Sector": "Finance & Banking",
    "Immigration": "Immigration",
    "Science, Technology, Communications": "Tech & Telecom",
    "Crime and Law Enforcement": "Justice & Civil Rights",
    "Law": "Justice & Civil Rights",
    "Civil Rights and Liberties, Minority Issues": "Justice & Civil Rights",
    "Government Operations and Politics": "Government & Elections",
    "Congress": "Government & Elections",
    "Education": "Labor & Education",
    "Labor and Employment": "Labor & Education",
    "Social Welfare": "Labor & Education",
    "Transportation and Public Works": "Transportation & Infrastructure",
    "Housing and Community Development": "Transportation & Infrastructure",
    "Agriculture and Food": "Agriculture & Food",
}

# LDA ALI issue codes (3-letter) -> domain.
ALI_TO_DOMAIN = {
    "HCR": "Health", "MMM": "Health", "MED": "Health", "PHA": "Health",
    "TAX": "Taxes & Budget", "BUD": "Taxes & Budget", "ECN": "Taxes & Budget",
    "ENG": "Energy & Environment", "ENV": "Energy & Environment",
    "CAW": "Energy & Environment", "NAT": "Energy & Environment",
    "DEF": "Defense & Veterans", "HOM": "Defense & Veterans", "VET": "Defense & Veterans",
    "TRD": "Trade & Tariffs",
    "FIN": "Finance & Banking", "BAN": "Finance & Banking", "INS": "Finance & Banking",
    "IMM": "Immigration",
    "TEC": "Tech & Telecom", "CPT": "Tech & Telecom", "SCI": "Tech & Telecom", "COM": "Tech & Telecom",
    "AGR": "Agriculture & Food", "FOO": "Agriculture & Food",
    "LBR": "Labor & Education", "EDU": "Labor & Education",
    "TRA": "Transportation & Infrastructure", "AVI": "Transportation & Infrastructure",
    "MAR": "Transportation & Infrastructure", "HOU": "Transportation & Infrastructure",
    "LAW": "Justice & Civil Rights", "CIV": "Justice & Civil Rights",
    "FOR": "Foreign Affairs",
    "GOV": "Government & Elections", "CAM": "Government & Elections",
}


def press_topic_text(title: str | None, text: str | None, lede_chars: int = 500) -> str:
    """The slice of a press release used for topic tagging: the title plus the
    lede (first ~500 chars). Press releases state their subject up top; the long
    tail and the office/committee footer add boilerplate noise (e.g. a member who
    chairs 'Energy & Commerce' would match 'energy' on every release), so they
    are excluded."""
    return f"{title or ''} {(text or '')[:lede_chars]}"


def domains_in_text(text: str | None) -> list[str]:
    """Return the policy domains a press release touches (multi-label, coarse)."""
    if not text:
        return []
    return [d for d, rx in _DOMAIN_RE.items() if rx.search(text)]


def domain_for_policy_area(pa: str | None) -> str | None:
    """Map a Congress.gov policy_area string to a domain (None if unmapped)."""
    if not pa:
        return None
    return POLICY_AREA_TO_DOMAIN.get(pa.strip())


def domain_for_issue(code: str | None) -> str | None:
    """Map an LDA ALI issue code (e.g. 'HCR') to a domain (None if unmapped)."""
    if not code:
        return None
    return ALI_TO_DOMAIN.get(code.strip().upper())


# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS senate_filings (
  filing_uuid TEXT PRIMARY KEY,
  filing_type TEXT, filing_year INTEGER, filing_period TEXT,
  income REAL, expenses REAL,
  registrant_id INTEGER, registrant_name TEXT, registrant_name_norm TEXT,
  registrant_house_id INTEGER,
  client_id INTEGER, client_name TEXT, client_name_norm TEXT,
  client_state TEXT, client_country TEXT,
  dt_posted TEXT, prov TEXT
);
CREATE TABLE IF NOT EXISTS senate_activities (
  filing_uuid TEXT, act_idx INTEGER, issue_code TEXT, description TEXT,
  gov_entities TEXT, prov TEXT
);
CREATE TABLE IF NOT EXISTS senate_activity_lobbyists (
  filing_uuid TEXT, act_idx INTEGER, lobbyist_name TEXT,
  lobbyist_name_norm TEXT, covered_position TEXT, prov TEXT
);
CREATE TABLE IF NOT EXISTS senate_contributions (
  filing_uuid TEXT PRIMARY KEY,
  filing_type TEXT, filing_year INTEGER, filing_period TEXT, filer_type TEXT,
  registrant_id INTEGER, registrant_name TEXT,
  lobbyist_name TEXT, no_contributions INTEGER, prov TEXT
);
CREATE TABLE IF NOT EXISTS contribution_items (
  filing_uuid TEXT, item_idx INTEGER, contribution_type TEXT,
  contributor_name TEXT, payee_name TEXT,
  honoree_name TEXT, honoree_name_norm TEXT, honoree_key TEXT,
  amount REAL, item_date TEXT, prov TEXT
);
CREATE TABLE IF NOT EXISTS house_filings (
  house_id TEXT PRIMARY KEY,
  report_year INTEGER, report_type TEXT,
  organization_name TEXT, organization_name_norm TEXT,
  client_name TEXT, client_name_norm TEXT,
  senate_id_raw TEXT, senate_registrant_id INTEGER, senate_client_id INTEGER,
  income REAL, expenses REAL, prov TEXT
);
CREATE TABLE IF NOT EXISTS house_alis (
  house_id TEXT, ali_idx INTEGER, issue_code TEXT, description TEXT,
  federal_agencies TEXT, prov TEXT
);
CREATE TABLE IF NOT EXISTS press_releases (
  url TEXT PRIMARY KEY, date TEXT, title TEXT,
  member_bioguide TEXT, member_name TEXT, member_party TEXT,
  member_state TEXT, member_chamber TEXT, text TEXT, prov TEXT
);
CREATE TABLE IF NOT EXISTS members (
  bioguide TEXT PRIMARY KEY, name TEXT, name_key TEXT,
  party TEXT, state TEXT, chamber TEXT
);
-- Resolver output: maps any honoree to a member bioguide (or NULL if unmatched)
CREATE TABLE IF NOT EXISTS honoree_resolution (
  honoree_name TEXT PRIMARY KEY, honoree_key TEXT,
  bioguide TEXT, match_method TEXT, n_items INTEGER, total_amount REAL
);
-- Resolver output: cross-chamber engagement links via the senateID bridge
CREATE TABLE IF NOT EXISTS xref_engagements (
  senate_registrant_id INTEGER, senate_client_id INTEGER,
  house_id TEXT, senate_filing_uuid TEXT,
  registrant_name TEXT, client_name TEXT, match_method TEXT
);
CREATE INDEX IF NOT EXISTS ix_sf_client ON senate_filings(client_name_norm);
CREATE INDEX IF NOT EXISTS ix_sf_reg ON senate_filings(registrant_id);
-- engagement-period lookup (mismatch cmd): without this SQLite may pick the
-- low-selectivity year index and the cross-chamber pass takes minutes, not seconds
CREATE INDEX IF NOT EXISTS ix_sf_engagement
  ON senate_filings(registrant_id, client_id, filing_year, filing_period);
CREATE INDEX IF NOT EXISTS ix_sf_year ON senate_filings(filing_year);
CREATE INDEX IF NOT EXISTS ix_sa_uuid ON senate_activities(filing_uuid);
CREATE INDEX IF NOT EXISTS ix_sa_code ON senate_activities(issue_code);
CREATE INDEX IF NOT EXISTS ix_sal_uuid ON senate_activity_lobbyists(filing_uuid);
CREATE INDEX IF NOT EXISTS ix_ci_uuid ON contribution_items(filing_uuid);
CREATE INDEX IF NOT EXISTS ix_ci_hon ON contribution_items(honoree_key);
CREATE INDEX IF NOT EXISTS ix_hf_sreg ON house_filings(senate_registrant_id);
CREATE INDEX IF NOT EXISTS ix_hf_client ON house_filings(client_name_norm);
CREATE INDEX IF NOT EXISTS ix_pr_bio ON press_releases(member_bioguide);
CREATE INDEX IF NOT EXISTS ix_pr_date ON press_releases(date);
"""


def init_schema(con: sqlite3.Connection) -> None:
    con.executescript(SCHEMA)
    con.commit()
