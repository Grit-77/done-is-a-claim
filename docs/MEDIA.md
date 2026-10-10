# README media

[receipt.svg](../assets/receipt.svg) is original vector artwork. Its title and
description are embedded; the README also supplies alternative text.

The [GIF](../assets/false-green.gif) and [static PNG](../assets/false-green.png) are
rendered from the actual output of the included synthetic demo. The animation
plays once and is inside a collapsible section. The PNG presents the final state
without motion. Neither is a recording of a production incident.

[demo-evidence.json](../assets/demo-evidence.json) contains the captured synthetic
outputs, exit codes and source hashes. It omits local interpreter paths.

## Regenerate

The core toolkit and checks use Python's standard library. Only this optional
artwork renderer needs Pillow and two local TrueType font files. In an environment
with Pillow installed:

```bash
python tools/render_demo.py --font /path/to/bold.ttf --mono /path/to/monospace.ttf
```

Use fonts you are licensed to render. Font files are not bundled or redistributed.
Text layout may vary by font, so visually inspect the resulting GIF and PNG. Run
the demo again if its source changes; do not keep a stale recording as evidence of
the new source's behavior.

This renderer executes only the repository's synthetic demo. It does not connect
to an agent, send data to a provider or record your terminal.
