# README media

[receipt.svg](../assets/receipt.svg) is original vector artwork. The README's
[animated cover](../assets/receipt-stamp.gif) gives its red stamp a short drop and
compression, then stays on the final impression without looping. Readers requesting reduced motion
receive the SVG through `picture`; a static-cover link is also present. A
[PNG of the impression](../assets/receipt-stamp.png) is available for previews.

The stamp animation is decorative, not evidence of an executed check. It was
rendered from the approved SVG design. Its title and description are embedded in
the SVG; the README also supplies alternative text.

The separate [demo GIF](../assets/false-green.gif) and [static PNG](../assets/false-green.png) are
rendered from the actual output of the included synthetic demo. The animation
plays once. These optional demo assets are not embedded in the README; the PNG
presents the final state without motion. Neither is a recording of a production incident.

[demo-evidence.json](../assets/demo-evidence.json) contains the captured synthetic
outputs, exit codes and source hashes. It omits local interpreter paths.

## Regenerate

The cover animation requires Pillow plus Node.js and Sharp, all optional:

```bash
python tools/render_stamp.py --sharp-module /path/to/node_modules/sharp
```

It performs no network requests. `--node` can select an existing Node executable.
The static SVG is the source of truth; if its stamp group changes, review the
animation's transform coordinates before regeneration.

The core toolkit and checks use Python's standard library. Only this optional
demo renderer needs Pillow and two local TrueType font files. In an environment
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
