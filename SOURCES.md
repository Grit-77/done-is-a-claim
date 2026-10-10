# Sources and design decisions

This project distinguishes an observed incident, an operational lesson, and an
example invented to test reasoning. They are not interchangeable.

## Original incidents

The original 18 rules come from the author's internal September 2026 records.
[INCIDENTS.md](INCIDENTS.md) contains the accounts;
[CLAIMS.md](CLAIMS.md) identifies their internal record names and limits. The raw
logs are private. The public repository does not independently reproduce those
historical totals.

## Grit operational material

Reviewed on 2026-10-10. These are original, portable adaptations of the owner's
Grit runbooks, with system-specific commands and private operational details
removed. They do not depend on the Grit runtime.

| Material reviewed | Adaptation here | Evidence status |
|---|---|---|
| Worker collection and return records | [collecting-worker-results](skills/collecting-worker-results/SKILL.md) | Operational guidance: process status, commit footprint, checked tree and delivery are separate observations. |
| Dispatch acceptance design and brief defects | [acceptance-design](skills/acceptance-design/SKILL.md) | Operational guidance: check the affected boundary and make the required inputs available. |
| Batch collection and a static verification review | [evidence-freshness](skills/evidence-freshness/SKILL.md) | Operational guidance and static-review finding: evidence must refer to unchanged inputs; not a newly reproduced production incident. |
| Measurement and worker diagnosis guidance | Revisions to [whose-red](skills/whose-red/SKILL.md) and [reading-measurements](skills/reading-measurements/SKILL.md) | Control-design guidance, corrected where the old wording overstated what a comparison proves. |

The source materials are internal. They are provenance for the adaptation, not
publicly reproducible measurements. The examples and [evaluation scenarios](evals/README.md)
are explicitly synthetic and can be inspected without access to those materials.

## Related public projects

Studied on 2026-10-10. These projects informed packaging and navigation; their
popularity is not evidence that this repository improves agent outcomes. No
source code or skill text from them is vendored here.

| Project | What we learned | What we chose here |
|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | Explain the workflow, installation and verification expectations. | Show a concrete failure first, then a small entry point and optional skills. |
| [anthropics/skills](https://github.com/anthropics/skills) | Make skills discoverable and distinguish examples from production guarantees. | A problem-oriented catalog, specific triggers and explicit limitations. |
| [agentsmd/agents.md](https://github.com/agentsmd/agents.md) | A conventional instruction file can keep adoption small. | Keep the portable core in `AGENTS.md`; preserve the adopting project's context. |
| [agentskills/agentskills](https://github.com/agentskills/agentskills) | Package a skill as a small directory with an identifiable entry point. | Standalone folders with `name`, `description` and `SKILL.md`. |

Fresh verification is also a central idea in
[Superpowers' verification skill](https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md).
This project's particular focus is the failure account behind a rule and the
measurement traps that can make an apparently valid result misleading.

Sources retain their own licenses. In particular, a repository containing skills
does not imply that every included skill has the same license. This repository's
original material is covered by [Apache-2.0](LICENSE).

## Illustrations and checks

- [The false-green demo](examples/false_green.py) is a synthetic, runnable example.
  Its animation is generated from captured demo output, not invented terminal text.
- [Evaluation cases](evals/README.md) are prompts and review rubrics, not a benchmark
  dataset or a claim of measured accuracy.
- [Repository checks](tools/check_repository.py) validate local structure. Their
  result does not certify agent behavior, source truth or remote URL availability.
