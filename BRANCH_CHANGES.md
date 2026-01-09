# Branch Changes: `oceangitlab` vs `main`

> ⚠️ 🤖 **Notice:** This document was generated with LLM assistance. Please verify details before relying on them.

## Summary

Rate limiting, better logging, and more robust MR/branch handling for migrations.

## Key Changes

### `ratelimit.go` (new)
Token bucket rate limiter wrapping the HTTP client:
- Core API: ~1.3 req/sec
- Search API: ~0.45 req/sec

### `main.go`
- Wraps HTTP transport with rate limiter
- Logs `X-Ratelimit*` headers on retries

### `project.go`
- Mirror clone with `NoCheckout` + fetch all tags
- Logs cloned branches
- Fetches `refs/merge-requests/<iid>/head` when commits are missing
- Better fallbacks when user lookups fail
- Logs skip reasons for MRs

### `oceangitlab.sh` (new)
Convenience script for local runs with tokens/flags.

### `go.mod`
Bumped to Go 1.24.0.

## Quick Test

```bash
go build
LOG_LEVEL=TRACE ./oceangitlab.sh
# Check for: "rate limiting enabled", cloned branches list, MR ref fetches
```
