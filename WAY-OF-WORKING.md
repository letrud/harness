# Way of working

How repositories built on this harness are changed, proven, accepted and released. Learned by running two fleet repos and one product repo through it in a day; every rule here was paid for.

## 1. The intent is the contract

`intent/` states what must be true. Code, data, evidence and documentation are downstream of it. Where code and intent disagree, the code is wrong. Nothing is ever changed in the intent to make a check pass.

**Only the intent reaches the agent.** A decision in a commit message, an ADR outside `intent/`, a chat — none of it exists for the next implementer. If a choice matters, it is one line in the intent. If it does not, the implementer decides and records the decision in the pull request.

## 2. A change is to the intent or to the implementation — never both

- **An intent change** is deliberate, has its own pull request or commit, and touches only `intent/`. It says what changed and why in one sentence. Every intent change on the default branch dispatches the agent with the diff.
- **An implementation change** touches nothing under `intent/` — not the specification, not the packs or data, not the generated files. It states what it did and what it could not verify.

CI refuses a pull request that does both. Two writers own `intent/`: people, for the specification and the declared data; the automation on the default branch, for whatever the intent declares as generated — evidence, generated docs, collected data. A pull request is neither writer.

Something learned while implementing that belongs in the intent — a bank's quirk, a source's mapping, a limitation — is proposed as its own intent change and named in the implementation change that depends on it.

## 3. Whoever changes it, proves it — before submitting

Unit tests prove the implementation's own logic. Only the intent's evaluation — against the real test environment, the real source — proves the counterparty accepts what is sent. Both are required; neither substitutes.

Whoever makes a change runs the evaluation before submitting, with the credentials available to them, and reads it as a verdict on the change:

- a failure against a **reachable** environment is a **defect in the change**, to be fixed before submission — never recorded as evidence and moved past, unless a limitation the intent itself declares explains it, in which case the submission names it;
- skipped for want of credentials is not a verdict; the submission says which could not be evaluated and why;
- no operation that passed before the change passes less after it.

The submission states the result per instance and per operation. CI runs the same evaluation on the change and gates on lost operations. The submission's claim and CI's verdict must agree.

## 4. Derived data has one writer

Evidence, generated docs, collected data: written by the automation on the default branch, on a schedule or after acceptance, and by nobody else. Not hand-edited, not carried in pull requests. A conflict in a derived file is resolved by regenerating it, never by merging it.

## 5. Secrets

Credentials are named by convention in the intent (`PSD2_CRED_<BANK>_<ENV>_CERT`, a token's environment variable) and held as **Actions** secrets on the repository — never in the tree, never in Codespaces secrets (workflows cannot read those). The agent's environment gets exactly the secrets the repository's own CI references, so its proofs are CI's proofs. One secret for many repositories needs an organisation; on a personal account it is one per repo.

## 6. The agent's loop

```
intent change on main ──► hand-off (push cannot run the agent) ──► dispatch with before..after
        │
        ▼
resume an unfinished rebuild/* branch if one exists, else start one
read every top-level *.md under intent/, then the diff, then the repository
run the intent's proofs with the repo's own secrets ── fix what fails against a reachable environment
commit and push as you go ── CI and the pull request no later than the last quarter of the budget
        │
        ▼
pull request: what the intent required, how it is satisfied, what was decided, what could not be verified
CI on the change: build · tests · evaluation · lost-operation gate · intent-or-implementation guard
human merges ──► automation on main writes evidence ──► tag v* ──► release.yml ships the binaries
```

The caller workflow in each repository is content-free and copied verbatim; everything repository-specific is in `intent/`. What every such repository shares — `build.yml` proves, `release.yml` ships, the transcript policy, resume — is the harness's, stated once in the brief it composes.

## 7. Accepting a pull request

Read the pull request as a claim and CI as its verification:

1. the intent-or-implementation guard is green — the change is one thing;
2. tests pin the MUSTs the change touches; a MUST NOT has a test that fails when violated;
3. the evaluation ran on the change and lost nothing; the submission's per-operation result matches CI's;
4. decisions where the intent was silent are stated, and none should have been an intent change instead;
5. what could not be verified is said plainly.

A pull request opened by the agent is authored by `github-actions[bot]`, and GitHub holds its workflow runs until a person approves them once (the run's page → *Approve and run*, or `gh api -X POST repos/<owner>/<repo>/actions/runs/<id>/approve`). A push to the branch by a person lifts the hold too. Until then the checks show as awaiting action, not as failed.

Merge with a merge commit; the agent's commits are its account of the work. Rebase, do not merge, when the branch is behind — and if a derived file conflicts, take the default branch's copy and regenerate.

## 8. Releasing

A `v*` tag on the default branch releases. The tag message states what ships and what is excluded, from the evidence on that commit. Nothing is released from a branch.

## 9. Authoring an intent

Two skills in `plugins/fleet-control` say how: `fleet-intent` for many comparable units held against a standard, `product-intent` for one thing that source code is written from. Both come down to the same tests — is every declared datum binding, does every MUST have a test, does the intent say whose defect a rejection is, what happens to evidence when the environment is unreachable, and could a stranger in another language produce the same result from the folder alone.

## 10. What the harness owes the repositories

The harness carries what would otherwise be repeated in every repository: the workflows, the brief, the conventions, the transcript, the resume, the credential handling, the skills. When a rule here needs enforcing, it is enforced once, here, and every caller inherits it on the next `v1`. When a repository needs to say something about itself, it says it in its intent — never in its caller, never in a prompt.
