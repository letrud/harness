---
name: product-intent
description: Author a product intent - a specification under intent/ from which an implementation is written by an agent, not inherited from code. Use for "write the intent for this tool", "specify this so it can be rebuilt", "the spec is the source of truth", "intent-first repo", "what must this product do", "make this spec enforceable", or before pointing rebuild-from-intent at a repository. The intent is the deliverable; source code is one of its outputs.
---

# Author a product intent

A **product intent** specifies one thing to be built - a CLI, a service, a library - well enough that an implementation written from it, in any language, by anyone, is correct if it conforms. The harness's `rebuild-from-intent` workflow hands the intent to an agent on every change; what the intent leaves unsaid, the agent decides. Author for that reader.

The reference is `letrud/psd2-cli/intent/`: three normative Markdown files and one declarative folder per instance of the thing the product talks to.

## Shape

```
intent/
  INTENT.md      what the product MUST be - obligations, honesty, distribution
  SPEC.md        how its data is represented - the shape of a declarative pack
  EVAL.md        what a build may claim, how that is proven, when a change is accepted
  <instance>/    one folder per thing the product talks to: data, never code
```

Few files at the top, all normative, all read first. Rationale, history and alternatives do not belong here - nor does anything a capable implementer would arrive at unaided. The intent states what MUST be true so that it reads as instructions.

## Write in RFC 2119

Every requirement is a MUST or a MUST NOT. This is not style: a MUST maps to a test that passes, a MUST NOT to a test that fails when violated, and the agent's brief tells it to pin both. Narrative cannot be pinned. If a sentence has no MUST in it, ask what it is for.

## What the intent has to say

These are the sections an agent cannot do without. Each was learned by leaving it out.

**1. Declared is binding.** Anything the intent declares as data - a header name, a path, a convention, a limit - is a requirement on the implementation unless the intent says it is illustrative. Say so once, generally: *"everything a pack declares under `conventions` MUST be honoured on every request the concept applies to."* Otherwise an implementer treats the parts you did not single out as optional, and the first real environment tells you which.

**2. Unknown is null; status reflects execution.** The honesty rules are the load-bearing part. *"A host, path or header that has not been confirmed MUST be `null`, never inferred."* *"`verified` MUST mean real calls succeeded."* An agent follows these to the letter, and they are what make every later failure legible instead of hidden behind a plausible guess.

**3. Generated outputs, declared - and who writes them.** Name the files under `intent/` that the implementation writes - evidence, generated docs - and state that the automation on the default branch writes them, after a change is accepted, and that *a change to the implementation modifies nothing under `intent/`*. Two writers own the folder - people for the specification and the declared data, automation for the generated files - and a pull request is neither. This is what lets "never edit the intent" coexist with "record what happened"; without it, every pull request carries regenerated evidence and conflicts with the default branch on merge. Say too that a change is to the intent or to the implementation, never both, so that CI can refuse the mixture.

**4. Acceptance.** The section most often missing. State:
- what proves the implementation: unit tests against a stand-in prove the logic; only evaluation against the real test environment proves the counterparty accepts what is sent. Both, neither substitutes;
- **who runs the evaluation and when** - whoever makes the change, before submitting it, with the credentials available to them;
- **what a failure means** - an operation that fails against a *reachable* test environment is a defect in the change, never evidence to record and move past, unless a limitation the intent itself declares explains it;
- what a change must not do - lose an operation that passed before it.

Without this an agent records a failure honestly, opens the pull request, and is right to.

**5. Limitations, declared alongside requirements.** A place for facts about the environment that make a correct implementation look broken: *"test users ship with an empty ledger"*, *"pagination never engages with four accounts"*. An implementation MUST surface them when a result is empty. Without them, the agent cannot tell an environment limit from its own defect - and neither can a reader of the evidence.

**6. External inputs, named by convention.** Credentials, endpoints, tokens: state the environment variable names and resolution order - *"`PSD2_CRED_<BANK>_<ENV>_CERT` / `_KEY`, base64 or PEM; then a committed test identity, evaluation only; then the local profile."* One convention makes CI, local use and the agent's own proof identical, with no per-repository wiring.

**7. Where specific knowledge goes.** Behaviour learned from a real counterparty belongs in that instance's declarative folder, stated as a testable failure - *"without `psu-id`: FORMAT_ERROR 'Missing header'"* - never in a prompt, a README or a chat. The loop that keeps the intent complete: the environment surfaces a behaviour, the change records it as a quirk in the same pull request, the next implementer inherits it.

## Silence is a decision surface

Where the intent is silent, the agent decides like a careful engineer and records the decision in the pull request - never in the intent. So: nothing outside `intent/` reaches it. A language choice in a commit message, a layout in an ADR, a convention agreed in a chat - none of it exists. If you want a particular choice, it is one line in the intent; if you are content to let the implementer choose, say nothing and read the PR.

## What does not belong in the intent

- Cross-repository conventions - the CI file names other systems read, where a transcript is kept, how a cut-short session resumes. Those are the harness's, stated once in the brief it composes.
- Toolchain instructions, permitted commands, repository-specific hints. The caller of `rebuild-from-intent` is content-free on purpose; if the agent needs to know something, the intent needs to say it.
- Anything about the agent. The intent specifies the product for any implementer.

## Pressure-test before you hand it to an agent

- **Pick any declared datum. Does the intent say it is binding?** If it has to be inferred, it will not be.
- **Pick any MUST. What test fails when it is violated?** If none is imaginable, it is narrative.
- **Suppose the test environment rejects a request. Does the intent say whose defect that is?**
- **Suppose it is unreachable. Does the intent say what happens to the evidence that exists?**
- **Suppose a result is empty. Can the implementation tell the reader why, from the intent alone?**
- **Is every choice you care about written down?** Language, layout, distribution, defaults.
- **Could this folder be handed to a stranger in another language and produce the same product?** That is the test the whole approach rests on.

## The way of working

How a change moves from intent to release - who proves what, how a pull request is read, why derived data has one writer - is the harness's `WAY-OF-WORKING.md`. An intent that follows this skill makes every step of it enforceable.

## Changing an intent

Every change under `intent/` on the default branch dispatches the agent with the diff. Make the change deliberate and self-contained: one rule, the tests it implies, the evidence it will demand. A change that alters what an existing requirement means invalidates every implementation downstream; say so in the change, and expect the pull request to be large.
