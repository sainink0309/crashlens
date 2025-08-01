🔒 CrashLens runs 100% locally. No data leaves your system.

# CrashLens Token Waste Report

**Analysis Date:** 2025-07-31 22:11:51  

**Traces Analyzed:** 12  


## Summary

| Metric | Value |
|--------|-------|
| Total AI Spend | $0.09 |
| Total Potential Savings | $0.07 |
| Wasted Tokens | 1,414 |
| Issues Found | 8 |
| Traces Analyzed | 12 |

## Retry Loop (1 issues)

| Metric | Value |
|--------|-------|
| Total Waste Cost | $0.0002 |
| Total Waste Tokens | 108 |

**Trace IDs**:
`demo_retry_01`

**Issue**: 1 traces flagged by Retry Loop


## Fallback Failure (5 issues)

| Metric | Value |
|--------|-------|
| Total Waste Cost | $0.0728 |
| Total Waste Tokens | 1,275 |

**Trace IDs**:
`demo_fallback_01, demo_fallback_02, demo_fallback_03, demo_fallback_04, demo_fallback_05`

**Issue**: 5 traces flagged by Fallback Failure


## Overkill Model (2 issues)

| Metric | Value |
|--------|-------|
| Total Waste Cost | $0.0007 |
| Total Waste Tokens | 31 |

**Trace IDs**:
`demo_overkill_01, demo_overkill_02`

**Issue**: 2 traces flagged by Overkill Model


## Top Expensive Traces

| Rank | Trace ID | Model | Cost |
|------|----------|-------|------|
| 1 | demo_norm_03 | gpt-4 | $0.03 |
| 2 | demo_norm_04 | gpt-4 | $0.02 |
| 3 | demo_fallback_05 | gpt-3.5-turbo | $0.02 |

## Cost by Model

| Model | Cost | Percentage |
|-------|------|------------|
| gpt-4 | $0.09 | 99% |
| gpt-3.5-turbo | $0.0012 | 1% |

## Next Steps

- Run `crashlens --detailed` for grouped JSON reports
- Review trace patterns to optimize model routing
- Implement suggested fixes to reduce token waste
