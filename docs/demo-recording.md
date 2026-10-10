# Recorded false-green proof

The README animation depicts output from a real local run of the **synthetic**
[false-green example](../examples/false_green.py). It is not a production log,
a live agent session, an installation check or a measure of agent performance.

## Reproduce the observation

Source revision:
[`cc38701aa0f447c623c94a7f4299c1b55020179e`](https://github.com/Grit-77/done-is-a-claim/commit/cc38701aa0f447c623c94a7f4299c1b55020179e).
Recorded on Windows with Python 3.12.14; the source requires Python 3.10+ and
uses the standard library.

From a checkout of that revision:

```bash
python examples/false_green.py
```

The observed verifier exit was **1**, the summarizer exit was **0**, and the
example's receipt state was **FAIL**. The outer demo returned **0**: the intended
mismatch was demonstrated; the verifier did not pass.

## What the image preserves

The [looping GIF](../assets/demo/false-green-recorded.gif) and
[static image](../assets/demo/false-green-recorded.png) show these captured lines:

```text
Synthetic demo, not incident raw log.
Verifier output:
SYNTHETIC verifier: FAIL (expected 2, got 3)
Verifier exit: 1
Summarizer output:
SYNTHETIC summarizer: displayed final line
SYNTHETIC verifier: FAIL (expected 2, got 3)
Summarizer exit: 0
Receipt state: FAIL
Command exit: 1
Reason: Verifier exited 1; summarizer exit 0 does not verify the fixture.
Demo exit: 0 (expected mismatch demonstrated; not fixture success)
```

Three argv lines containing local interpreter paths are omitted. The displayed
command uses the portable `python` alias. Four frames reveal the recorded output
at reading pace; the animation's 14-second loop is **not execution timing**.
The PNG contains the final frame and provides a reduced-motion alternative.

Source SHA256:
`3f916abe198dde05e1969480f7c33ab8174296c9244f3340d74e340f557223ba`.
This identifies the recorded source bytes; it is not a signed attestation or a
guarantee of agent behavior. Raw local logs and interpreter paths are not included.

For recording your own command, see [receipts](RECEIPTS.md). A receipt with no
selected `--input` files remains incomplete for selected-input freshness checks.
