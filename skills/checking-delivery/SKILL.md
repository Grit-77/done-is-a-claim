---
name: checking-delivery
description: "Verify an artifact at its actual delivery destination and distinguish send attempts, acknowledgements, publication and consumer checks. Use when reporting a file, message, export or deployment as delivered; creating a local draft alone does not imply delivery."
---

# Checking delivery

Inspecting the source establishes what was prepared. Delivery requires
evidence about the destination the user was meant to receive. Check only
within the authorized scope; this skill grants no publishing or send rights.

## Identify the artifact and destination

Record the inspected source artifact and its revision or byte identity,
the intended destination and the relevant operation identity. A source path,
preview or successful build does not identify the delivered copy.

Keep these observations separate, using the states the system exposes:

- **Prepared:** the source exists and has been inspected.
- **Attempted:** a send, upload or publication operation was issued.
- **Acknowledged:** the system returned a receipt matching that operation.
- **Published:** the intended destination exposes the artifact or revision.
- **Consumer checked:** the delivered artifact was opened in its intended use.
- **Unverified:** a necessary observation is unavailable or inconclusive.

These are claims with separate evidence, not a universal status sequence.
An acknowledgement can establish system acceptance without establishing
publication, usable content or that a human read the message.

## Read the destination back

1. If delivery is authorized, inspect its result and retain the operation or
   receipt identity. Match an acknowledgement to the latest applicable attempt,
   including artifact, destination and revision where available. An old or
   unrelated receipt cannot verify a newer attempt.
2. Fetch or reopen the actual destination using an available read interface.
   Inspect the retrieved artifact rather than trusting a "saved" log, a status
   flag or a source preview. Record which destination revision was observed.
3. Compare the destination with the inspected source. Hashes can establish
   equal bytes when both copies are accessible. For a service that transforms
   content, check the relevant content and revision, and state the narrower
   comparison; do not claim byte equality from a successful response.
4. Check the delivered artifact through the appropriate consumer: decode an
   image, parse an export, open a document, or load and inspect the page.
   A matching hash does not establish that the format works or renders well.
   Likewise, a useful render alone does not establish source byte equality.
5. Report destination read-back and consumer outcomes independently. If the
   destination cannot be inspected, report delivery as unverified and retain
   any known attempt or acknowledgement evidence without upgrading the claim.

## Reconcile before retrying

A missing acknowledgement or timeout can leave a successful operation behind.
Inspect destination state and correlate durable receipts with the original
operation before resending. Unknown remains unresolved; do not manufacture
certainty by sending again. Operation identity helps reconciliation only to
the extent supported by that system; it is not a general exactly-once promise.

Use a brief receipt when delivery matters: source inspected, destination and
operation, acknowledgement, read-back comparison, consumer result and gaps.
For a local draft or trivial edit, report the observed result directly without
inventing a delivery workflow or requesting new permissions to verify it.
