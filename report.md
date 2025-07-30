🚨 **CrashLens Token Waste Report** 🚨
📊 Analysis Date: 2025-07-30 14:01:37

| Metric | Value |
|--------|-------|
| Total AI Spend | $0.09 |
| Total Potential Savings | $0.09 |
| Wasted Tokens | 2,549 |
| Issues Found | 12 |
| Traces Analyzed | 12 |

📢 **Fallback Failure** | 5 traces | $0.07 wasted | Fix: remove redundant fallbacks
   🎯 **Wasted tokens**: 1,275
   🔗 **Traces** (5): demo_fallback_01, demo_fallback_02, demo_fallback_03, demo_fallback_04, demo_fallback_05

❓ **Overkill Model** | 6 traces | $0.02 wasted | Fix: optimize usage
   🎯 **Wasted tokens**: 1,166
   🔗 **Traces** (6): demo_overkill_01, demo_overkill_02, demo_fallback_01, demo_fallback_03, demo_fallback_04, +1 more
   📄 **Samples**: "What is 2+2?...", "What is the capital of France?..."

🔄 **Retry Loop** | 1 traces | $0.0002 wasted | Fix: exponential backoff
   🎯 **Wasted tokens**: 108
   🔗 **Traces** (1): demo_retry_01
   📄 **Samples**: "What is the weather like today..."


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
