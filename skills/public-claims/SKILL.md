---
name: public-claims
description: "Write and fact-check public copy so that every figure, credential, promise and command has a receipt - a source with a locator, a command that re-derives it, or the author's own words - and remove any claim without one instead of softening it. Use when drafting or reviewing a README, release notes, a launch post or thread, slides, or a website page; and whenever a draft states a number, a ranking, a credential, a promised result or a command."
---

# Public claims

**No receipt, no claim.** In public copy every figure, credential, promise and
command has a receipt. A claim without one is removed, never softened into
"about", "up to" or a vaguer label that implies the same thing.

A receipt identifies what supports the claim and how it was checked:

- a source with a locator: `path:line`, a document and section, the issuer's
  own listing;
- a command that re-derives the value on a pinned commit;
- the author's own words, with date and the exact text, supporting an
  attributed report rather than independent reproducibility.

Distinguish current reproducible results from historical or private-source
reports. For a historical result, retain the original revision, date and
evidence; a recount today measures today's state. If the source is private,
say so in the public claim and identify its type and date without exposing
the private link or material. A row can preserve the exact authorized author
report, for example, "The author reported 42 collected cases on <date>;
the underlying run is private and was not independently reproduced."
Do not turn that report into a verified current test count. If disclosure is
not authorized or adequate evidence is unavailable, omit the claim.

This skill never posts anything. Publishing is a separate decision for a human.

## Procedure

1. **Pin the reviewed revision** and write its commit at the top of the fact
   sheet. Current recounts run on it; historical claims name their own
   revision and date.
2. **Keep one fact sheet**, `FACTS.md`, beside the drafts. A row holds the
   claim, its value, receipt and verification limits. Drafts quote the sheet
   and never introduce a new fact.
3. **Find the receipt for each claim** in every draft. No receipt: delete the
   sentence and log it in the changelog.
4. **Check each figure against its stated basis.** Recount current figures on
   the pinned revision; retain and verify the source for attributed historical
   reports. For pytest cases, run `pytest --collect-only -q tests` in a clean
   checkout of the pinned commit and record its exit status and collection
   summary, with configuration and environment. Counting `def test_` lines
   counts matching definitions, not collected cases: parametrization, methods
   and collection rules can change the total. Collection also does not prove
   that the cases passed.
5. **Check every universal.** "Every", "never", "all" and "only" each need a
   receipt for the universal. When the claim is narrower, write the narrower
   sentence. Precise beats grand.
6. **Show only real output.** Quote the actual message text the tool prints;
   never write an imagined terminal session.
7. **Tag unshipped work** `[PENDING]` in drafts and keep it off public pages.
8. **Use tokens for undecided names**: `{{NAME}}`, `{{REPO_URL}}`, so one
   replace lands the final choice. A private link never appears.
9. **Check length** with tokens filled at their final length. Verify the
   platform's current counting rules and limits for the account and post
   type, including link handling; use its composer or documented counter.
10. **Keep a changelog** at the bottom of the fact sheet: what was removed,
    recounted or tagged, why, and on which revision.

## Fact sheet row

| Claim | Value | Receipt | Checked on / limits |
|---|---|---|---|
| Collected pytest cases in `tests` | <n> | `pytest --collect-only -q tests`, exit status and saved collection summary | `<commit>`, <date>, <environment>; collection only |
| Historical author report | <exact dated statement> | <authorized source and locator> | <source date/revision>; private source or not independently reproduced, if applicable |

## Done when

Every claim in every draft has a fact-sheet row that supports its actual scope:
current results re-derive on the pinned revision, and historical or private
reports carry clear attribution and verification limits. Unreceipted claims
are gone, not hedged; every `[PENDING]` tag has been re-checked; and the changelog
names the revision reviewed.
