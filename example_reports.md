# 📊 CrashLens Report Examples

Here are examples of CrashLens reports in different formats using realistic AI usage data.

---

## 🔥 **Slack Format Report**

```
🚨 **CrashLens Token Waste Report**
==================================================
📅 **Analysis Date**: 2025-07-23 04:10:23
🔍 **Traces Analyzed**: 156
🧾 **Total AI Spend**: $47.32
💰 **Total Potential Savings**: $12.84
🎯 **Wasted Tokens**: 8,420
📊 **Issues Found**: 23

🔍 **Top Expensive Traces**:
  1. trace_3921 → gpt-4o → $3.02
  2. trace_3867 → gpt-3.5-turbo → $1.14
  3. trace_3843 → claude-sonnet → $0.82

📊 **Cost by Model**:
  • gpt-4o: $14.82 (79%)
  • gpt-3.5-turbo: $2.56 (14%)
  • claude-3-sonnet: $1.34 (7%)

❓ **Overkill Model** (15 issues)
  • 15 traces affected
  • $8.45 potential savings
  • Sample prompts: "Translate 'hello' to Spanish...", "What's 2+2?..."

🔄 **Retry Loops** (5 issues)  
  • 5 traces affected
  • $3.21 potential savings
  • Sample prompts: "Generate a haiku about cats...", "Write a short story..."

🌩️ **Fallback Storm** (3 issues)
  • 3 traces affected  
  • $1.18 potential savings
  • Sample prompts: "Complex data analysis...", "Advanced reasoning task..."
```

---

## 📝 **Markdown Format Report**

```markdown
# CrashLens Token Waste Report

**Analysis Date:** 2025-07-23 04:10:39  
**Traces Analyzed:** 156

## Summary

| Metric | Value |
|--------|-------|
| Total AI Spend | $47.32 |
| Total Potential Savings | $12.84 |
| Wasted Tokens | 8,420 |
| Issues Found | 23 |
| Traces Analyzed | 156 |

## Top Expensive Traces

| Rank | Trace ID | Model | Cost |
|------|----------|-------|------|
| 1 | trace_3921 | gpt-4o | $3.02 |
| 2 | trace_3867 | gpt-3.5-turbo | $1.14 |
| 3 | trace_3843 | claude-sonnet | $0.82 |

## Cost by Model

| Model | Cost | Percentage |
|-------|------|------------|
| gpt-4o | $14.82 | 79% |
| gpt-3.5-turbo | $2.56 | 14% |
| claude-3-sonnet | $1.34 | 7% |

## Overkill Model (15 issues)

| Metric | Value |
|--------|-------|
| Total Waste Cost | $8.45 |
| Total Waste Tokens | 5,230 |

**Issue**: 15 traces affected  
**Description**: Using expensive models for simple tasks that could be handled by cheaper alternatives

**Sample Prompts**:
1. `Translate 'hello' to Spanish`
2. `What's 2+2?`
3. `Generate a simple greeting`
4. `Count to 10`
5. `Convert temperature 32F to C`

**Recommended Actions**:
- Use gpt-3.5-turbo instead of gpt-4 for simple translation tasks
- Consider using specialized translation APIs for basic language tasks
- Implement prompt complexity scoring to route to appropriate models

## Retry Loops (5 issues)

| Metric | Value |
|--------|-------|
| Total Waste Cost | $3.21 |
| Total Waste Tokens | 2,156 |

**Issue**: 5 traces affected  
**Description**: Excessive retry attempts for the same prompt without meaningful changes

**Sample Prompts**:
1. `Generate a haiku about cats`
2. `Write a short story about space`
3. `Create a product description`

**Recommended Actions**:
- Implement exponential backoff for retries
- Add variation to retry prompts
- Set maximum retry limits (recommend 3-5 attempts)

## Fallback Storm (3 issues)

| Metric | Value |
|--------|-------|
| Total Waste Cost | $1.18 |
| Total Waste Tokens | 1,034 |

**Issue**: 3 traces affected  
**Description**: Rapid fallback attempts causing cascading costs without resolution

**Sample Prompts**:
1. `Complex data analysis with multiple variables`
2. `Advanced reasoning task requiring chain-of-thought`

**Recommended Actions**:
- Implement circuit breaker patterns
- Add delays between fallback attempts
- Review prompt engineering for complex tasks
```

---

## 📊 **Summary Format Report**

```
📊 **CrashLens Cost Summary**
==================================================
📅 **Analysis Date**: 2025-07-23 04:10:50
🔍 **Traces Analyzed**: 156
💰 **Total Cost**: $47.32
🎯 **Total Tokens**: 94,240
📈 **Total Traces**: 156

🤖 **Cost by Model**
  gpt-4: $32.45 (68.6%) - 23,450 tokens
  gpt-3.5-turbo: $12.87 (27.2%) - 51,230 tokens  
  claude-3-sonnet: $2.00 (4.2%) - 19,560 tokens

🛣️ **Cost by Route**
  /api/chat/completions: $28.90 (61.0%)
  /api/generations: $15.42 (32.6%)
  /api/embeddings: $3.00 (6.3%)

👥 **Cost by Team/User**
  engineering-team: $23.66 (50.0%)
  product-team: $12.45 (26.3%)
  data-science: $8.21 (17.3%)
  marketing: $3.00 (6.3%)

🏆 **Top 5 Most Expensive Traces**
  trace_4A7B: $4.32 - Complex code generation task
  trace_8F2E: $3.87 - Long document summarization  
  trace_1C9D: $3.45 - Multi-turn conversation
  trace_6B4A: $2.98 - Data analysis with charts
  trace_9E7F: $2.76 - Creative writing task

⏰ **Usage by Hour (Top 5)**
  14:00-15:00: $8.45 (17.9%) - Peak afternoon usage
  10:00-11:00: $6.78 (14.3%) - Morning work session
  15:00-16:00: $5.23 (11.0%) - Late afternoon
  09:00-10:00: $4.89 (10.3%) - Early morning
  13:00-14:00: $4.12 (8.7%) - Lunch hour

🚨 **Waste Detection Summary**
📊 **Issues Found**: 23
💰 **Total Potential Savings**: $12.84 (27.1% of total spend)

  • Overkill Model: 15 issues, $8.45 potential savings
    └── Avg waste per issue: $0.56
    
  • Retry Loops: 5 issues, $3.21 potential savings  
    └── Avg waste per issue: $0.64
    
  • Fallback Storm: 3 issues, $1.18 potential savings
    └── Avg waste per issue: $0.39

💡 **Key Recommendations**:
1. Route simple tasks to cheaper models (potential $8.45 savings)
2. Implement retry limits and backoff strategies ($3.21 savings) 
3. Add circuit breakers for fallback scenarios ($1.18 savings)
4. Peak usage at 14:00-15:00 - consider rate limiting
5. Engineering team accounts for 50% of costs - review usage patterns
```

---

## 🎯 **Use Cases for Each Format**

### 📢 **Slack Format**
- **Quick team updates** in engineering channels
- **Alert notifications** when waste thresholds exceeded  
- **Daily/weekly summaries** for stakeholders
- **Incident reports** during cost spikes

### 📝 **Markdown Format**  
- **Detailed documentation** for engineering reviews
- **GitHub issues** and pull request descriptions
- **Wiki pages** and knowledge base articles
- **Email reports** to management with formatting

### 📊 **Summary Format**
- **Executive dashboards** and business reviews
- **Financial analysis** and budget planning
- **Team performance** reviews and optimization
- **Trend analysis** and capacity planning

---

## 🚀 **Command Examples**

```bash
# Quick Slack update for team channel
poetry run python -m crashlens scan logs.jsonl -f slack

# Detailed analysis for engineering review  
poetry run python -m crashlens scan logs.jsonl -f markdown

# Executive summary with cost breakdown
poetry run python -m crashlens scan logs.jsonl --summary

# Privacy-safe summary for external sharing
poetry run python -m crashlens scan logs.jsonl --summary-only

# Pipeline integration
cat logs.jsonl | poetry run python -m crashlens scan --stdin -f json

# Interactive testing
poetry run python -m crashlens scan --paste -f human
```

Each format is optimized for different audiences and use cases, ensuring CrashLens provides value across the entire organization from engineers to executives! 🎉
