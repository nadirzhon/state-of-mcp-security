# State of MCP Security — Round 1

*A reproducible security audit of Model Context Protocol servers. Round 1 covers the
official MCP reference servers plus four popular hosted servers.*

> **TL;DR** — We scanned **8 MCP servers** with [mcpscan](https://github.com/nadirzhon/mcpscan).
> **6 of 8 (75%)** exposed at least one medium-or-higher hardening issue to connecting AI agents.
> The dominant patterns are **unconstrained free-text inputs** (path/command/url params with no
> validation) and **dangerous capabilities exposed without guardrails**. Findings are heuristic
> hardening observations, not confirmed exploits.

---

## Why this matters

An MCP server hands tools straight into an AI agent's context, and the agent will act on
whatever those tools describe and accept. That makes a server's *tool surface* a security
boundary — and today almost nobody measures it. This is Round 1 of an attempt to measure it
systematically and reproducibly.

## Headline numbers

![Findings by severity](assets/severity.svg)

![Findings by category](assets/category.svg)

| Metric | Value |
|---|---|
| Servers scanned | **8 / 8** (0 failed) |
| Total findings | **71** |
| Servers with a medium-or-higher finding | **6 (75%)** |
| Severity spread | 1 high · 28 medium · 3 low · 39 info |
| Most common issue | `loose-schema` (39) → `unconstrained-input` (18) → `dangerous-capability` (11) |

## What we found (the systemic patterns)

1. **Unconstrained inputs are everywhere (18 findings).** Free-text `path`, `command`, `url`,
   and `query` parameters with no `enum`/`pattern`/`format` are the norm, not the exception. On a
   filesystem server, *every* path parameter is a traversal surface an injected instruction can aim at.
2. **Schemas rarely lock down inputs (39 findings, `info`).** Most tools omit
   `additionalProperties: false`, so unexpected fields pass through. Low-severity hygiene, but
   pervasive — even in the reference implementations.
3. **Dangerous capabilities ship without guardrails (11 findings).** File write/delete, network
   egress, and command-execution-shaped tools are commonly exposed with no authorization or
   confirmation signal in the definition. In an agent, a prompt-injected instruction can reach them.
4. **One hosted server tripped a high-severity multi-capability heuristic** (file + network +
   credential access in a single tool). This is a heuristic flag requiring manual review, **not a
   confirmed vulnerability** — it has been set aside for manual verification and vendor
   notification rather than publication (see Ethics).

## The corpus

**Official reference servers** (public code from `@modelcontextprotocol`, scanned via `npx`):

| Server | Findings | Notable |
|---|---|---|
| `server-filesystem` | 25 | 12× unconstrained `path`, 1× file-write-delete capability |
| `server-memory` | 12 | 4× unconstrained inputs |
| `server-everything` | 11 | 2× dangerous-capability |
| `server-sequential-thinking` | 2 | clean apart from schema hygiene |

The official Python servers (`fetch`, `git`, `time`) were **excluded** from Round 1 due to a
local Python 3.14 packaging incompatibility, not scanned — not a finding.

**Popular hosted servers** (HTTP, connected read-only; **presented in aggregate only** per the
ethics policy below): four widely-used hosted MCP servers contributed 21 findings, ranging from
clean (schema hygiene only) to the single high-severity heuristic flag noted above.

## Methodology

- **Tool:** [mcpscan](https://github.com/nadirzhon/mcpscan) — connects to a server, enumerates its
  tools/resources/prompts, and runs deterministic checks (hidden text, tool-poisoning phrasing,
  dangerous capabilities, unconstrained inputs, loose schemas).
- **Read-only.** No tool is ever invoked. mcpscan inspects *definitions*, it does not exercise them.
- **Reproducible.** The corpus is [`scripts/corpus.json`](scripts/corpus.json); rerun with
  [`scripts/scan.py`](scripts/scan.py). Official-server detail in [`data/results.json`](data/results.json); anonymized hosted aggregates in [`data/hosted-aggregate.json`](data/hosted-aggregate.json).
- **Heuristic, by design.** Findings are pattern-based hardening observations, not verified
  vulnerabilities. `--ai` mode (Claude-assisted reasoning about tool *combinations*) was not used
  for these aggregate numbers to keep the dataset fully deterministic.

## Ethics & responsible disclosure

- **Only public servers**, scanned **read-only**, tools never invoked.
- **Official reference servers are named** — they are public reference code, and these are
  design-hardening observations on published examples, not vulnerability disclosures.
- **Hosted third-party services are aggregated and anonymized.** The single high-severity
  heuristic flag on a hosted server is **not published against a named vendor**; it will be
  verified manually and, if it holds up, reported privately to that vendor first.
- **Detect, not exploit.** Nothing here is a working exploit or an invitation to attack anyone.

## Limitations

- **Round 1 is small (N=8).** This is a methodology and baseline, not a census. The value is that
  it is *reproducible and extensible* — see below.
- **Heuristic checks** over-report hygiene (`loose-schema`) and can false-positive on broad tools
  (the high-severity flag is exactly such a case pending review).
- **stdio servers require executing their code**, so this round deliberately limited stdio scans
  to trusted official servers and used HTTP for third-party ones.

## Help expand Round 2

Add a server to [`scripts/corpus.json`](scripts/corpus.json) and open a PR, or run it yourself:

```bash
uvx --from git+https://github.com/nadirzhon/mcpscan mcpscan "<your MCP server>" --json
```

The goal for Round 2 is a larger corpus of **hosted** servers (safe to scan without running
untrusted code) and per-category trend lines over time.

---

*Produced with [mcpscan](https://github.com/nadirzhon/mcpscan). Findings are AI-assisted /
heuristic and may be imperfect — treat them as a first pass, not a verdict.*
