# Claims

Every figure in this repository, with where it comes from. The incidents come from Grit's internal records, written
on the day each one happened; the lesson name is the record's id. A figure that cannot be traced here is removed,
not softened.

| Figure | Where it appears | Receipt |
|---|---|---|
| 3,489 tasks re-run, 2,282 passed the first independent re-run, 14-29 Sep 2026 | README, INCIDENTS | Server re-run log of each task's own acceptance (first result per task), measured 2026-09-29 ~15:40Z; record `project-radar-verification-numbers-2026-09-29` |
| 736 tasks passed their own test and turned the full suite red | README, INCIDENTS | Culprit log from the same server, same date and record |
| 66 tasks opened, 48 without scope, 21 workers, zero lines of code | INCIDENTS §1-2 | Record `feedback-a-task-with-no-scope-authorises-nothing`, 2026-09-22 |
| 12 passed; 5 failed against 741 passed, 0 failed | INCIDENTS §3-4, §9 | Record `feedback-read-the-artefact-not-the-summary`, 2026-09-22 |
| Three `cmd \| tail` reports recorded as exit 0; three lint errors | INCIDENTS §5 | Record `feedback-capture-the-commands-own-exit-code`, 2026-09-22 |
| pytest exit 4 (missing path) and 5 (nothing collected) | INCIDENTS §6 | Record `feedback-no-tests-ran-exits-zero` (corrected entry, 2026-09-22 11:05); measured with the project's interpreter |
| `80 -> 65 (1 reconciled)`; `commits: 1` on two of four results | INCIDENTS §9 | Record `feedback-read-the-artefact-not-the-summary`, 2026-09-22 |
| 11 frames of 0 bytes, 46 cut off | INCIDENTS §10 | Record `feedback-verify-rendered-frames-decode`, 2026-09-28 |
| Sixty rendered frames, never looked at in a terminal | INCIDENTS §11 | Record `feedback-look-at-it-yourself`, 2026-09-18 |
| `c9476137` does not exist; 12 tasks closed unverified | INCIDENTS §12 | Record `feedback-verify-subagent-citations`, 2026-09-23 |
| 17 handover lines; main 14 commits ahead in 40 minutes | INCIDENTS §13 | Record `feedback-your-base-expires-while-you-write`, 2026-09-22 |
| SQLite floor 3.51.3; 3.51.2 and 3.45.1 in the test; Ubuntu 24.04 hosts on 3.45.1 | INCIDENTS §14 | Record `feedback-a-test-that-asserts-a-constant-proves-self-agreement`, 2026-09-22 |
| One of four refusal branches; two tests | INCIDENTS §15 | Record `feedback-a-fix-can-reach-one-call-site`, 2026-09-22 |
| 208 of 208; 8 of 8 | INCIDENTS §16 | Record `feedback-a-detector-with-no-true-negatives`, 2026-09-22 |
| Four uncommitted edits destroyed | INCIDENTS §18 | Record `feedback-never-reset-hard-a-dirty-tree`, 2026-09-19 |

## Not claims

Rule numbers (1-18), dates, version numbers in examples, and the counts of files in this repository.

## Not claimed

- A rate of wrong agent work. Part of the 1,207 tasks that did not pass the first re-run failed for environment
  reasons (missing tools, host errors), so they are not all defects.
- How often the gate rejects good work. It was never measured.
