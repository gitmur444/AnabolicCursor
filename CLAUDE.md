# Claude Code Review Guidelines

This repo includes automated PR reviews by Claude Code. Use these guidelines to structure findings and reduce noise.

## Focus Areas
- Code quality, readability, maintainability
- Correctness: errors, edge cases, input validation
- Security: secrets, auth/authz, dependency risks
- Performance and resource usage
- Tests: coverage of edge cases, determinism, clarity
- Docs: comments for non-obvious logic, updated README/API

## Expectations
- Prefer inline comments for specific issues; a short summary comment for overall notes.
- For each issue: problem, severity, concrete fix suggestion.
- Avoid duplicates and trivial nits; group related feedback.
- Follow repo style; propose larger refactors only if clearly beneficial.

## Severity
- Blocker: correctness/security must-fix before merge
- Major: significant maintainability/perf issues
- Minor: small improvements, readability
- Nit: optional polish

## Output Structure
1) Brief summary (what’s good, key risks)
2) Issues grouped by severity with code references
3) Checklists for multi-step recommendations

## Safe Changes
Provide minimal, incremental edits that are safe to apply independently. Mark risky or broader changes as optional with rationale.
