# CrashLens CLI Test Log

## Scan: Slack Format

```
🔒 CrashLens runs 100% locally. No data leaves your system.
🚨 **CrashLens Token Waste Report**
==================================================
📅 **Analysis Date**: 2025-07-23 22:08:55
🔍 **Traces Analyzed**: 94

🧾 **Total AI Spend**: $0.05
💰 **Total Potential Savings**: $0.0434
🎯 **Wasted Tokens**: 2,522
📊 **Issues Found**: 73

❓ **Expensive Model Overkill** (52 issues)
  • 52 traces affected
  • Est. waste: $0.0406
  • Wasted tokens: 422
  • Sample prompts: "Translate to French: 'Text sam...", "Translate to French: 'Text sam...", "Explain briefly concept 1..."

🔄 **Retry Loop** (21 issues)
  • 21 traces with excessive retries
  • Est. waste: $0.0028
  • Wasted tokens: 2,100
  • Sample prompts: "What is the weather today in c...", "What is the weather today in c...", "What is the weather today in c..."
  • Suggested fix: implement exponential backoff and circuit breakers

📈 **Monthly Projection**: $1.30 potential savings
```

---

## Scan: Markdown Format

```
🔒 CrashLens runs 100% locally. No data leaves your system.

# CrashLens Token Waste Report

**Analysis Date:** 2025-07-23 22:09:13  

**Traces Analyzed:** 94  


## Summary

| Metric | Value |
|--------|-------|
| Total AI Spend | $0.05 |
| Total Potential Savings | $0.0434 |
| Wasted Tokens | 2,522 |
| Issues Found | 73 |
| Traces Analyzed | 94 |

## Expensive Model Overkill (52 issues)

| Metric | Value |
|--------|-------|
| Total Waste Cost | $0.0406 |
| Total Waste Tokens | 422 |

**Issue**: 52 traces affected

**Sample Prompts**:
1. `Translate to French: 'Text sample 1 expensive mode...`
2. `Translate to French: 'Text sample 2 expensive mode...`
3. `Explain briefly concept 1`


## Retry Loop (21 issues)

| Metric | Value |
|--------|-------|
| Total Waste Cost | $0.0028 |
| Total Waste Tokens | 2,100 |

**Issue**: 21 traces with excessive retries

**Sample Prompts**:
1. `What is the weather today in city 1?`
2. `What is the weather today in city 3?`
3. `What is the weather today in city 4?`

**Suggested Fix**: Implement exponential backoff and circuit breakers

## Monthly Projection

Based on current patterns, potential monthly savings: **$1.30**
```
