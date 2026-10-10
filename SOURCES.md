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

## Adoption and executable evidence

Additional sources reviewed on 2026-10-10:

| Source | Adaptation and boundary |
|---|---|
| [Vercel skills CLI](https://github.com/vercel-labs/skills) and [version 1.7.2 metadata](https://registry.npmjs.org/skills/1.7.2) | Document optional discovery and selected installation. An isolated local-source smoke checked v1.1.0's six-skill layout and both selected agent copies. |
| [Version-pinned installer source](https://github.com/vercel-labs/skills/blob/671e8c320810d36fed80fac5f1a2c1bf7e82d812/src/installer.ts) | Its replacement behavior motivated an original project installer that refuses destination collisions. No upstream installer code is copied. |
| [OpenAI's historical gh-fix-ci skill](https://github.com/openai/skills/blob/main/skills/.curated/gh-fix-ci/SKILL.md) | A narrowly scoped script can return structured evidence and distinguish missing observations. The local receipt tool is original and has no GitHub/provider integration. |
| [HumanLayer: small focused agents](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-10-small-focused-agents.md) and [explicit control flow](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-08-own-your-control-flow.md) | Keep capture, installation and semantic review distinct, with inspectable transitions and ordinary files. |
| [Superpowers: writing skills](https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md) | Fresh-context pressure scenarios informed separating participant packets from evaluator rubrics. No comparative outcome claim is made. |

The `openai/skills` repository now declares itself deprecated and points to
[openai/plugins](https://github.com/openai/plugins). Its script pattern is cited as
historical design material, not as current installation guidance. Package flags
and side effects above were checked against the pinned Vercel version; later
versions may differ. Popularity and installation telemetry do not establish active
use or improved agent outcomes.

## Rechecking evidence, resuming and delivery

Reviewed on 2026-10-10. New portable workflows distinguish what was saved, what is
true in the receiving checkout, and what exists at the delivery destination.

| Source | Adaptation here | Evidence boundary |
|---|---|---|
| Grit session-handoff runbook and its synthetic scenario | [resuming-work](skills/resuming-work/SKILL.md) and the expanded handoff template | Internal operational guidance: read the final saved checkpoint back, reopen evidence and establish current ownership. Not a newly measured incident. |
| Grit delivery acknowledgement code/tests and uncertain-launch handling | [checking-delivery](skills/checking-delivery/SKILL.md), delivery fields and scenarios | Static implementation/test inspection separates attempts and correlated acknowledgements. An acknowledgement does not prove destination usability or human reading. |
| [in-toto Link model](https://in-toto.readthedocs.io/en/latest/model.html#link) | Keep command, selected artifact identities and execution output distinct; add a digest for the closed local log. | This is an original local record format, not an in-toto implementation or signed statement. |
| [SLSA 1.2 artifact verification](https://slsa.dev/spec/v1.2/verifying-artifacts) | Compare observed bytes with recorded identities before reusing evidence. | SLSA also has trust and policy requirements. Editable local hash comparison is not SLSA verification or authenticity. |
| [GitHub CLI release asset verification](https://cli.github.com/manual/gh_release_verify-asset) and [attestation verification](https://cli.github.com/manual/gh_attestation_verify) | Reopen the actual destination artifact and check the intended identity, then apply consumer-specific checks. | The local synthetic delivery demo adds no signing, GitHub or provider dependency. |

The receipt rechecker is new original code. Internal Grit code and external
specifications informed its separation of observations; they do not establish
that this repository inherits another system's guarantees. Private source
locations and raw operational records are not published here. No upstream code
or prose is vendored. The cited projects retain their licenses, including
in-toto's Apache-2.0, GitHub CLI's MIT, and the SLSA specification's
[Community Specification License](https://github.com/slsa-framework/governance/blob/main/1._Community_Specification_License-v1.md).

## Connected workflow and native packaging

Reviewed on 2026-10-10. We studied
[Superpowers v7.0.0 at bb92a77](https://github.com/obra/superpowers/tree/bb92a77741419a4ab5f06e711a283343f1ada0c3),
especially its entry, planning, execution and review organization. That informed
our decision to connect previously separate skills through one task entry point.
The five new skills and three record templates here are original writing. They
keep existing user authority, support a small-task path and inline execution, and
make review findings return to fixes and affected checks. We do not claim feature
parity, compatibility with its internal helpers or equivalent agent outcomes.

| Source | Application here |
|---|---|
| [Superpowers entry skill](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/using-superpowers/SKILL.md) and [execution skill](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/executing-plans/SKILL.md) | A discoverable starting point and explicit transitions between tasks; our entry also works alone without sibling files. |
| [OpenAI plugin building](https://developers.openai.com/plugins/build/plugins) | Portable manifest and native Codex catalog; skills-only distribution with no lifecycle hooks or services. |
| [Claude Code plugin reference](https://code.claude.com/docs/en/plugins-reference) and [marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) | Claude manifest, repository marketplace and documented native installation. |

The project copier's profiles and conservative update mechanism are original
Python code. Its editable provenance detects ordinary local drift; it is not
package signing. Native package structure, native CLI validation and an agent's
actual behavior are separate checks. See [plugin validation limits](docs/PLUGINS.md)
and the [workflow](docs/WORKFLOW.md). No upstream code or skill text is vendored.
Superpowers retains its MIT license; this original material uses Apache-2.0.

## Executable native exercise

The [native session procedure](docs/NATIVE-TESTS.md) separates installation,
observed loading and independently measured task acceptance. Author-run native
sessions motivated a portable CSV exercise with an external verifier. The fixture,
verifier and tests are original code, not a wrapper around another project's runner.

[Superpowers' pinned native test guide](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/tests/claude-code/README.md)
and [explicit-skill runner](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/tests/explicit-skill-requests/run-test.sh)
were studied on 2026-10-10 for the distinction between discovery and integration.
Here, the portable tool never launches a model or changes native configuration;
the operator uses their normal host/account and records the native evidence
separately. A successful artifact check does not prove skill invocation or a
reduction in agent errors. Source licenses remain with their respective projects.

## Illustrations and checks

- [The false-green demo](examples/false_green.py) is a synthetic, runnable example.
  Its animation is generated from captured demo output, not invented terminal text.
- [Evaluation cases](evals/README.md) are prompts and review rubrics, not a benchmark
  dataset or a claim of measured accuracy.
- [The wrong-delivery demo](examples/wrong_delivery.py) uses real temporary local
  copies and parsing with a positive control. It demonstrates mechanisms, not a
  production delivery or improvement rate.
- [Repository checks](tools/check_repository.py) validate local structure. Their
  result does not certify agent behavior, source truth or remote URL availability.
