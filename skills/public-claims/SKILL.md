---
name: public-claims
description: "Write and fact-check public copy so that every figure, credential, promise and command has a receipt - a source with a locator, a command that re-derives it, or the author's own words - and remove any claim without one instead of softening it. Use when drafting or reviewing a README, release notes, a launch post or thread, slides, or a website page; and whenever a draft states a number, a ranking, a credential, a promised result or a command."
---

# Public claims

**No receipt, no claim.** In public copy every figure, credential, promise and
command has a receipt. A claim without one is removed, never softened into
"about", "up to" or a vaguer label that implies the same thing.

A receipt lets someone else re-derive the claim on the reviewed revision:

- a source with a locator: `path:line`, a document and section, the issuer's
  own listing;
- a command that re-derives the value on a pinned commit;
- the author's own words, with date and the exact text.

This skill never posts anything. Publishing is a separate decision for a human.

## Procedure

1. **Pin one revision** and write its commit at the top of the fact sheet.
   Every recount runs on it.
2. **Keep one fact sheet**, `FACTS.md`, beside the drafts. A row holds the
   claim, its value and its receipt. Drafts quote the sheet and never
   introduce a new fact.
3. **Find the receipt for each claim** in every draft. No receipt: delete the
   sentence and log it in the changelog.
4. **Recount every figure** from its receipt on the pinned revision; never copy
   a number from an older draft. A test count, for example:
   `git grep -E "^\s*(async\s+)?def test_" <commit> -- tests | wc -l`.
5. **Check every universal.** "Every", "never", "all" and "only" each need a
   receipt for the universal. When the claim is narrower, write the narrower
   sentence. Precise beats grand.
6. **Show only real output.** Quote the actual message text the tool prints;
   never write an imagined terminal session.
7. **Tag unshipped work** `[PENDING]` in drafts and keep it off public pages.
8. **Use tokens for undecided names**: `{{NAME}}`, `{{REPO_URL}}`, so one
   replace lands the final choice. A private link never appears.
9. **Count length** with tokens filled at their final length. On X a post is
   at most 280 characters and every link counts as 23.
10. **Keep a changelog** at the bottom of the fact sheet: what was removed,
    recounted or tagged, why, and on which revision.

## Fact sheet row

| Claim | Value | Receipt | Checked on |
|---|---|---|---|
| Test count | <n> | `git grep ... <commit> \| wc -l` | `<commit>`, 2026-10-05 |

## Done when

Every claim in every draft has a fact-sheet row whose receipt re-derives on the
pinned revision; unreceipted claims are gone, not hedged; every `[PENDING]` tag
has been re-checked; and the changelog names the revision reviewed.
