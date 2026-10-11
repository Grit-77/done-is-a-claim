# Copy and try

Short public copy for sharing this repository. These drafts are not published
posts. The links below identify the source and limits of each observation.

## English

**One sentence:** Your coding agent says done. Show the receipt: a portable
workflow for checking what ran, what was tested, and what actually arrived.

**Short post:**

> Your coding agent says “done”. What would prove it? Done is a claim connects
> acceptance, implementation, review and delivery checks. Its recorded synthetic
> demo shows a verifier exiting 1 while the summarizer exits 0. The optional
> Markdown receipt reporter shows the recorded command outcome alongside current
> evidence freshness, without rerunning the command. Try it on an existing
> project and share a concrete benefit, failure or confusing result.
>
> [Repository](https://github.com/Grit-77/done-is-a-claim) ·
> [Recorded demo and limits](https://github.com/Grit-77/done-is-a-claim/blob/main/docs/demo-recording.md) ·
> [Receipt reporter quickstart](https://github.com/Grit-77/done-is-a-claim/blob/main/docs/REPORTS.md) ·
> [Share a use report](https://github.com/Grit-77/done-is-a-claim/issues/new?template=use-report.yml)

**Request to your agent:**

> Install https://github.com/Grit-77/done-is-a-claim. Follow its INSTALL.md,
> preserve my existing work, verify the installation, then explain what changed
> and how I start using it. Use my current account and permissions.

## Türkçe

**Tek cümle:** Kod ajanınız “bitti” diyor. Kanıtını gösterin: neyin çalıştığını,
neyin sınandığını ve neyin gerçekten teslim edildiğini kontrol eden taşınabilir
bir iş akışı.

**Kısa paylaşım:**

> Kod ajanınız “bitti” diyor. Bunu ne kanıtlar? Done is a claim; kabul ölçütünü,
> uygulamayı, incelemeyi ve teslimat kontrollerini birbirine bağlar. Kaydedilmiş
> sentetik demosunda doğrulayıcı 1 ile çıkarken özetleyici 0 ile çıkar. İsteğe
> bağlı Markdown kanıt raporlayıcısı, komutu yeniden çalıştırmadan kaydedilmiş
> komut sonucunu kanıtın güncel durumuyla birlikte gösterir. Mevcut bir projede
> deneyin; somut bir faydayı, hatayı veya kafa karıştıran sonucu paylaşın.
>
> [Depo](https://github.com/Grit-77/done-is-a-claim) ·
> [Kaydedilmiş demo ve sınırları](https://github.com/Grit-77/done-is-a-claim/blob/main/docs/demo-recording.md) ·
> [Kanıt raporlayıcısı başlangıç rehberi](https://github.com/Grit-77/done-is-a-claim/blob/main/docs/REPORTS.md) ·
> [Kullanım deneyimi paylaş](https://github.com/Grit-77/done-is-a-claim/issues/new?template=use-report.yml)

**Ajanınıza verilecek istek:**

> https://github.com/Grit-77/done-is-a-claim deposunu kur. INSTALL.md dosyasını
> izle, mevcut çalışmamı koru, kurulumu doğrula; sonra neyin değiştiğini ve nasıl
> kullanmaya başlayacağımı açıkla. Mevcut hesabımı ve izinlerimi kullan.

## Try one boundary

Start with the [entry skill](../skills/using-done-is-a-claim/SKILL.md) for a whole
task, or choose a concrete failure below. Follow [INSTALL.md](../INSTALL.md) for
installation; installing a plugin does not place the optional Python tools inside
your project. Run tools from the separate toolkit checkout.

| Symptom | Skill and request to the agent | Observation to retain |
| --- | --- | --- |
| The command looked green | [reading-measurements](../skills/reading-measurements/SKILL.md): “Retain the verifier's own exit and distinguish it from the wrapper's exit.” | Run `python examples/false_green.py` from the toolkit checkout. The verifier exits 1, the summarizer exits 0, and the receipt is FAIL. The demo's outer exit 0 records the intended mismatch. |
| Evidence changed after checking | [evidence-freshness](../skills/evidence-freshness/SKILL.md): “Show which selected inputs this receipt checked and whether they still match.” | Follow the [reporter quickstart](REPORTS.md) using your real check. Keep the historical result separate from current freshness; unchanged selected files do not cover unselected dependencies. |
| A copied artifact did not arrive as intended | [checking-delivery](../skills/checking-delivery/SKILL.md): “Open the artifact at its actual destination and check what the recipient can use.” | Record the destination observation and any consumer check you could not perform. A send or copy acknowledgement alone does not establish usable delivery. |

## Claim receipts

| Copy claim | Source and boundary |
| --- | --- |
| Connected evidence-first workflow | [Entry skill](../skills/using-done-is-a-claim/SKILL.md) and [workflow](WORKFLOW.md). Instructions guide decisions; installation alone does not establish compliance. |
| Verifier 1; summarizer 0 | [Recording](demo-recording.md), [runnable source](../examples/false_green.py), [GIF](../assets/demo/false-green-recorded.gif) and [static proof](../assets/demo/false-green-recorded.png). Synthetic output, not a production incident or performance benchmark; recording identifies its source revision. |
| Markdown reporter separates history and freshness | [Reporter source](../tools/report_receipt.py) and [usage and limits](REPORTS.md). Editable hash consistency covers selected evidence, not task completion or a signed attestation. |
| Repository installation request | [Root installation guide](../INSTALL.md) and [native plugin guide](PLUGINS.md). Host, scope, loading and outcome need their own observations. |
| Concrete use feedback | [Use-report form](https://github.com/Grit-77/done-is-a-claim/issues/new?template=use-report.yml) and [evidence categories](USE-REPORTS.md). Benefits, failures and uncertainty are welcome; no independent user outcome is implied. |

## Distribution boundaries

| Route | What exists or is required |
| --- | --- |
| Own GitHub marketplace | Native package instructions in [PLUGINS.md](PLUGINS.md). Registration and task acceptance are separate. |
| skills.sh discovery | Root [skills.sh.json](../skills.sh.json) groups the catalog. The [official customization guide](https://www.skills.sh/docs/customize) says metadata is read from the default branch after a telemetry-enabled install; display refresh is separate from this local edit. The [FAQ](https://www.skills.sh/docs/faq) describes install-driven listing. Installation counts do not establish active use or improved outcomes. |
| Official directories | Platform review and publication are separate steps. This kit does not establish eligibility, approval or a submitted listing. |

Review the target platform's current posting limits before using a draft. No
community post, directory submission or external message is performed by this kit.
