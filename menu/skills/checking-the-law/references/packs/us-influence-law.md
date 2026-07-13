# EXAMPLE domain law pack: US lobbying & influence

*This is an **optional, swappable example** of a domain law pack — the pre-built topic→citation
map described in the checking-the-law skill. The skill itself is domain-independent and does NOT
require this file: for any other beat, either build your own pack in this format (topic → governing
provision → key defined terms → scope limits/exceptions → where official guidance lives) or work
citation-by-citation via references/finding-the-law.md. This pack covers the US lobbying/influence
beat and is retained because this bundle's worked findings cite it.*


A starting index of the laws a lead in this corpus most often raises, and their well-known scope
limits. **This is a map, not the answer.** Always fetch and read the current primary text before
concluding — provisions have subsections, exceptions, and amendments, and they change. Citations
here are orientation; verify each against the U.S. Code (law.cornell.edu / govinfo.gov), the House
and Senate ethics manuals, or the DOJ FARA site, and record your as-of date.

## Contents
- Revolving door / post-employment (18 U.S.C. § 207)
- Lobbying registration & disclosure (LDA / HLOGA)
- Foreign agents (FARA)
- Gifts, travel, and "honor" contributions
- Bribery, gratuities, honest-services
- Financial disclosure (EIGA / STOCK Act)
- How to pick the right one

## Revolving door / post-employment — 18 U.S.C. § 207
The most common revolving-door question. Critically, the ban restricts **making lobbying
*contacts*** with one's former branch/office for a period — it does **not** forbid *being* a
lobbyist, registering, or doing behind-the-scenes strategy. "Ex-staffer registered to lobby" is
not itself a violation; a prohibited *contact* would be. Scope differs sharply by role:

- **Former Members of Congress** — §207(e)(1): **Senators: 2-year** ban on lobbying contacts with
  the *entire legislative branch*. **House Members: 1-year** ban (similar breadth).
- **Senate senior staff** — §207(e)(2): **1-year** ban on contacts with the *entire Senate* plus
  certain leadership offices (broad).
- **House senior staff** — §207(e)(3): **1-year** ban, narrower — contacts with the *former
  employing office* (and, for committee staff, the committee).
- **Committee employees** — §207(e)(4)/(5): **1-year** ban limited to **that committee and its
  members/staff** — NOT the whole chamber. *(This is the classic "looks illegal but isn't" trap:
  a former committee counsel lobbying an unrelated part of Congress is outside the ban.)*
- Executive-branch analogues: §207(a) (permanent/2-yr, particular matters), §207(c) (1-yr senior).

Always check: the person's exact role, the "senior"/salary threshold, the departure date vs. the
contact date, and whether the *contact* (not just registration) fell within scope.

## Lobbying registration & disclosure — LDA (2 U.S.C. § 1601 et seq.), amended by HLOGA (2007)
Requires registration when someone crosses time (≥20% on lobbying for a client) and dollar
thresholds, then quarterly LD-2 activity reports and semiannual LD-203 contribution reports.
Questions here are usually *disclosure* failures (unregistered lobbying, late/missing filings),
not the fact of lobbying. Enforcement is civil/administrative and rare.

## Foreign agents — FARA (22 U.S.C. § 611 et seq.)
Agents acting in the U.S. for a *foreign principal* (government, party, or foreign company, in
political/PR contexts) must register with DOJ — a separate, stricter regime than the LDA. The LDA
has an exemption (LDA §4(b)(4)) that lets some foreign-commercial lobbying report under LDA instead
of FARA. If a filing shows `foreign_entities`, the question is which regime applies. Do not assert
a FARA violation from LDA data alone; flag for a lawyer.

## Gifts, travel, and "honor" contributions
Governed largely by **chamber rules** (House/Senate ethics manuals) and HLOGA, not a single
statute. HLOGA sharply restricted gifts and privately-funded travel from lobbyists. **Charitable
donations "in honor of" a member** (the LD-203 honorary items) are generally **legal and
disclosed**: a member may designate a charity, the money goes to the charity (not the member),
and it's reported. The story there is the *channel and concentration*, not a gift-rule violation —
unless facts show personal benefit or a linked official act. Confirm against the current gift rules.

## Bribery, gratuities, honest-services — 18 U.S.C. §§ 201, 1341/1346
Very high bar. Bribery (§201) needs a corrupt *quid pro quo* tied to an **official act**; illegal
gratuity is lesser but still needs a link to an official act. Honest-services fraud (§1346) was
narrowed by *McDonnell v. United States* (2016) to require a formal "official act." Disclosed
money next to a vote does **not** meet this — never imply bribery from the corpus. This is
lawyers-and-prosecutors territory; at most, flag a question.

## Financial disclosure — Ethics in Government Act; STOCK Act (2012)
Members/senior staff file financial disclosures; the STOCK Act adds securities-trading disclosure
and bans certain uses of nonpublic information. Rarely reachable from this corpus (no trading data)
but relevant if a lead touches a member's finances via outside data.

## How to pick the right one
- Ex-government person now lobbying → **§ 207** (get the exact role and the contact date).
- Foreign client/entity → **FARA** vs. LDA exemption.
- Unregistered or missing filings → **LDA/HLOGA** disclosure duties.
- Gift / trip / "honor money" → **chamber gift rules / HLOGA** (usually legal if disclosed).
- Money ↔ a specific official act → **§ 201 / § 1346** (almost always just a question for a lawyer).

When in doubt about which applies, read the definitions section of the candidate statute first —
the definitions (who is a "covered official," what is a "lobbying contact," what is a "foreign
principal") decide most of these questions.
