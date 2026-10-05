# Done is a claim

![Done is a claim: 18 rules for coding agents, each one paid for by a real failure. An AGENTS.md file open beside the title, showing rules 3 to 6.](assets/card.png)

**18 rules and 3 skills for coding agents, each one paid for by a real failure.**

Your agent says "done". Usually it is. Sometimes the tests never ran, the exit code belonged to `tail`, or the fix reached one call site out of four. These rules make an agent show its evidence before it says the word.

We wrote them while running Claude Code and Codex agents on our own repository. Between 14 and 29 September 2026 a server re-ran the acceptance command of **3,489** agent tasks: **2,282** passed on that first independent re-run, and **736** tasks had passed their own test while turning the full suite red on main. Every rule below comes with the incident behind it in [INCIDENTS.md](INCIDENTS.md).

## Use it

Copy [AGENTS.md](AGENTS.md) into the root of your repository. Codex and other agents that read `AGENTS.md` pick it up as it is.

For Claude Code, also copy [CLAUDE.md](CLAUDE.md). It holds one line, `@AGENTS.md`, which imports the rules.

Already have an `AGENTS.md` or `CLAUDE.md`? Paste the rules under your own.

## The rules

**Before you start**
1. Write the acceptance command before the work, and never edit it to pass.
2. Check that every path you were given exists.

**Before you say "done"**
3. Re-run the acceptance yourself, on the current revision, and quote its output.
4. Run the whole suite, not only your test.
5. Record the command's own exit code, not the pipe's.
6. "No tests ran" is a failure.
7. Unknown is not pass.
8. Green means every check.

**When you report**
9. Read the artefact, not the summary.
10. A file that exists is not a file that works.
11. Look at it yourself.
12. Verify every citation.
13. State the base, and re-check it before you publish.

**When you write tests and fixes**
14. A test that repeats a constant proves nothing.
15. Fix the class, not the instance.
16. Run a detector on a known-good case first.
17. Register cleanup before the work it cleans up.

**Never**
18. Never run a destructive command to answer a question.

## Skills

Three skills for the moments the rules are hardest to follow:

| Skill | Use it when |
|---|---|
| [reading-measurements](skills/reading-measurements/SKILL.md) | before reporting any figure: an exit code, a test count, a green, a list size |
| [whose-red](skills/whose-red/SKILL.md) | tests fail and someone has to decide: the change, or main? |
| [public-claims](skills/public-claims/SKILL.md) | writing a README, release notes or a launch post with numbers in it |

For Claude Code, copy a skill's folder into `.claude/skills/` in your repository, or into `~/.claude/skills/` for every project:

```bash
git clone https://github.com/Grit-77/done-is-a-claim
cp -r done-is-a-claim/skills/* ~/.claude/skills/
```

Each skill is one Markdown file, so any other agent can be pointed at it directly.

## Rules are not a gate

A rule in a prompt is advice: the agent can still skip it. We built that gate as a separate tool, RADAR, which refuses to close a task until its acceptance has passed again on the current revision. These rules are the part that fits in one file.

## Contributing

Have a rule that cost you a real failure? Open an issue with the incident: what the agent claimed, what was true, and the number or output that showed the difference. Rules without an incident are not added.

## Licence

Apache-2.0. Made by [Grit](https://grit.grit-77.workers.dev), Ankara. Also from us: [cinematic-site](https://github.com/Grit-77/cinematic-site), a Claude Code skill for websites that ship checked.
