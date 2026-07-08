# Normalized store schema

`ingest.py` writes a SQLite database (default `build/influence.db`). Every row
carries a `prov` provenance id (see below). Tables:

## Source tables
- `senate_filings` — one LDA filing. Key cols: `filing_uuid` (PK), `filing_type`,
  `filing_year`, `filing_period`, `income`, `expenses`, `registrant_id`,
  `registrant_name(_norm)`, `registrant_house_id`, `client_id`,
  `client_name(_norm)`, `client_state`, `client_country`, `dt_posted`, `prov`.
- `senate_activities` — `filing_uuid`, `act_idx`, `issue_code` (ALI), `description`,
  `gov_entities` (semicolon-joined names lobbied), `prov`.
- `senate_activity_lobbyists` — `filing_uuid`, `act_idx`, `lobbyist_name(_norm)`,
  `covered_position` (revolving-door text), `prov`.
- `senate_contributions` — LD-203 report. `filing_uuid` (PK), `filer_type`
  (`lobbyist`/`organization`), `registrant_id`, `registrant_name`,
  `lobbyist_name`, `no_contributions`, `prov`.
- `contribution_items` — one contribution line. `filing_uuid`, `item_idx`,
  `contribution_type`, `contributor_name`, `payee_name`, `honoree_name(_norm)`,
  `honoree_key`, `amount`, `item_date`, `prov`.
- `house_filings` — one House LD-1/LD-2. `house_id` (PK = filename), `report_year`,
  `report_type` (`REG`/`Q1`..`Q4`), `organization_name(_norm)`,
  `client_name(_norm)`, `senate_id_raw`, `senate_registrant_id`,
  `senate_client_id`, `income`, `expenses`, `prov`.
- `house_alis` — `house_id`, `ali_idx`, `issue_code`, `description`,
  `federal_agencies`, `prov`.
- `press_releases` — `url` (PK), `date`, `title`, `member_bioguide`,
  `member_name`, `member_party`, `member_state`, `member_chamber`, `text`, `prov`.
- `members` — `bioguide` (PK), `name`, `name_key` (LAST|FIRST), `party`, `state`,
  `chamber`. Derived from the press corpus.

## Resolver output tables
- `honoree_resolution` — `honoree_name` (PK) → `bioguide`, `match_method`
  (`exact`/`lastname_unique`/`unmatched`/`ambiguous_key`), `n_items`,
  `total_amount`.
- `xref_engagements` — `senate_registrant_id`, `senate_client_id`, `house_id`,
  `senate_filing_uuid`, `registrant_name`, `client_name`, `match_method`
  (`senateID_bridge`/`name_match`).

## Provenance id format (`prov`)
- `data/.../file.jsonl#L<n>` — press release at line `n`.
- `data/.../filings_YYYY.json#<filing_uuid>` — a Senate filing/contribution.
- `data/.../<houseID>.xml` — a House filing (whole file is the record).

`review.py <prov>` round-trips any of these to the raw source record.
