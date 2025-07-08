🔒 CrashLens runs 100% locally. No data leaves your system.

# CrashLens Token Waste Report

**Analysis Date:** 2025-07-08 11:38:07  

**Traces Analyzed:** 6  


## Summary

| Metric | Value |
|--------|-------|
| Total AI Spend | $0.01 |
| Total Potential Savings | $0.0050 |
| Wasted Tokens | 130 |
| Issues Found | 6 |
| Traces Analyzed | 6 |

## Expensive Model Short (4 issues)

| Metric | Value |
|--------|-------|
| Total Waste Cost | $0.0053 |
| Total Waste Tokens | 82 |

**Issue**: 4 traces used GPT-4 instead of gpt-3.5-turbo

**Sample Prompts**:
1. `What is 2+2?`
2. `Hello`
3. `Translate this`

**Suggested Fix**: Route short prompts to `gpt-3.5-turbo`

## Expensive Model Short (2 issues)

| Metric | Value |
|--------|-------|
| Total Waste Cost | $0.0007 |
| Total Waste Tokens | 48 |

**Issue**: 2 traces used CLAUDE-3-SONNET instead of claude-3-haiku

**Sample Prompts**:
1. `Simple question`
2. `Yes`

**Suggested Fix**: Route short prompts to `claude-3-haiku`

## Monthly Projection

Based on current patterns, potential monthly savings: **$0.15**
