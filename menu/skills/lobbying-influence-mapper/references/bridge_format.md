# The Senate ↔ House bridge

The House and Senate publish the *same* Lobbying Disclosure Act filings in two
different systems with different schemas. Linking them is the backbone of any
cross-chamber analysis. Two mechanisms, both deterministic:

## 1. The `senateID` bridge (primary)

Every House XML filing carries a `<senateID>` element formatted as:

```
<registrantID>-<clientID>
```

e.g. `401105148-53487` → Senate registrant `401105148`, client `53487`. These
map directly onto `senate_filings.registrant_id` and `senate_filings.client_id`.
`resolve_entities.py` joins on both ids to produce `xref_engagements`
(`match_method='senateID_bridge'`).

Observed coverage (2025 House filings): ~45% link to an in-store Senate filing
via the exact id pair; the gap is mostly filings whose Senate counterpart is in a
year not yet ingested, or registrant/client ids not present in the store.

Independently, ~69.5% of *Senate* filings carry a `registrant.house_registrant_id`,
giving a registrant-level bridge in the other direction.

## 2. Normalized-name fallback

When the id pair does not resolve, fall back to matching
`house_filings.organization_name_norm == senate_filings.registrant_name_norm`
AND `client_name_norm` equal. `norm_org()` uppercases, strips punctuation, and
removes common corporate suffixes (INC/LLC/CORP/CO/LP/LLP/THE/HOLDINGS/GROUP),
so "Comcast Corporation" and "COMCAST CORP." collapse. This lifts total House→Senate
linkage to ~98%.

## Caveat
Senate client/registrant names are already uppercased and internally consistent
(0 casing-only duplicates observed); House names are mixed-case and messier, so
the *cross-dataset* normalization is where the resolver earns its keep. Name-match
links are weaker than id links — treat `match_method='name_match'` rows as
candidates to confirm, not ground truth.
