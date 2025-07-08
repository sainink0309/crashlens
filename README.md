# CrashLens

> Detect token waste patterns in GPT API logs. Offline, fast, and privacy-first.

## 🚀 What is CrashLens?

CrashLens is a CLI tool that scans Langfuse-style JSONL logs of GPT API usage and detects token waste patterns like retry loops, fallback storms, and inefficient GPT-4 usage. It estimates monthly cost waste and prints Slack-style or Markdown alerts to stdout. All processing is 100% local — no internet access, no SDK, no YAML input required.

## ⚡ Features

- **🔍 Detects token waste patterns**: Retry loops, fallback storms, and inefficient expensive model usage
- **💰 Cost estimation**: Supports GPT-4, GPT-3.5, and Claude models with accurate pricing
- **📊 Multiple output formats**: Slack-style, Markdown, and cost summary modes
- **🔒 Privacy-first**: 100% local processing, no data leaves your machine
- **📥 Flexible input**: File, stdin pipe, or clipboard paste
- **🎯 Smart suggestions**: Recommends cheaper model alternatives
- **📈 Monthly projections**: Estimates potential savings over time

## 📦 Installation

```bash
# Clone the repository
git clone <repository-url>
cd crashlens

# Install dependencies with Poetry
poetry install

# Run the tool
poetry run crashlens scan examples/demo-logs.jsonl
```

## 🛠️ Usage

### Basic Commands

#### File Input
```bash
# Analyze a log file
crashlens scan logs.jsonl

# With custom pricing config
crashlens scan logs.jsonl --config custom-pricing.yaml

# Output in Markdown format
crashlens scan logs.jsonl --format markdown
```

#### Piped Input
```bash
# Pipe logs from another command
cat logs.jsonl | crashlens scan --stdin

# Process logs from a database export
mysql -e "SELECT * FROM logs" | crashlens scan --stdin

# Chain with other tools
grep "gpt-4" logs.jsonl | crashlens scan --stdin
```

#### Clipboard Input
```bash
# Copy logs to clipboard, then analyze
crashlens scan --paste

# Combine with other options
crashlens scan --paste --format markdown --summary
```

### Output Modes

#### 1. **Waste Detection Mode** (Default)
Detects and reports token waste patterns:
```bash
crashlens scan logs.jsonl
```

**Detects:**
- 🔄 **Retry Loops**: Multiple calls with the same prompt
- 💎 **Expensive Model Usage**: GPT-4/Claude for simple tasks
- ⚡ **Fallback Storms**: Multiple model switches in one trace

#### 2. **Cost Summary Mode**
Aggregates costs by route, model, and team:
```bash
crashlens scan logs.jsonl --summary
```

**Shows:**
- 💰 Total cost breakdown
- 🛣️ Cost by API route
- 🤖 Cost by model type
- 👥 Cost by team (if metadata available)
- 🏆 Top 5 most expensive traces

#### 3. **Markdown Output**
Generates copy-paste ready reports:
```bash
crashlens scan logs.jsonl --format markdown
```

### Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `log_file.jsonl` | Path to JSONL log file | `crashlens scan logs.jsonl` |
| `--stdin` | Read from stdin pipe | `cat logs.jsonl \| crashlens scan --stdin` |
| `--paste` | Read from clipboard | `crashlens scan --paste` |
| `--format` | Output format | `--format markdown` |
| `--summary` | Cost summary mode | `--summary` |
| `--config` | Custom pricing config | `--config pricing.yaml` |
| `--demo` | Use sample data | `--demo` |

### Input Data Format

CrashLens expects Langfuse-style JSONL logs with these fields:

```json
{
  "trace_id": "unique_trace_id",
  "timestamp": "2024-01-15T10:00:00Z",
  "model": "gpt-4",
  "prompt": "Your prompt text",
  "completion_tokens": 150,
  "prompt_tokens": 50,
  "cost": 0.003,
  "status": "success",
  "route": "/api/chat",
  "metadata": {
    "team": "frontend"
  }
}
```

**Required fields:** `trace_id`, `model`, `prompt`  
**Optional fields:** `cost`, `route`, `metadata.team`

## 🧩 Project Structure

```
crashlens/
├── cli.py                      # Main Click CLI entrypoint
├── detectors/                  # Token waste detection rules
│   ├── retry_loops.py         # Detects repeated API calls
│   ├── gpt4_short.py          # Detects expensive model overuse
│   └── fallback_storm.py      # Detects model switching patterns
├── parsers/
│   └── langfuse.py            # JSONL loader, trace grouper by trace_id
├── reporters/
│   ├── slack_formatter.py     # Emoji-rich Slack-style output
│   ├── markdown_formatter.py  # Copy-paste ready Markdown reports
│   └── summary_formatter.py   # Cost aggregation by route/model/team
├── config/
│   └── pricing.yaml           # Model pricing configuration
├── examples/
│   └── demo-logs.jsonl        # Sample Langfuse-style logs
├── tests/
│   └── test_rules.py
├── README.md
├── LICENSE
├── pyproject.toml
└── .gitignore
```

## 🔧 Configuration

### Model Pricing

Edit `config/pricing.yaml` to customize model costs and detection thresholds:

```yaml
models:
  gpt-4:
    input_cost_per_1k: 0.03
    output_cost_per_1k: 0.06
  claude-3-opus:
    input_cost_per_1k: 0.015
    output_cost_per_1k: 0.075

thresholds:
  retry_loop:
    max_retries: 3
    time_window_minutes: 5
  gpt4_short:
    min_tokens_for_gpt4: 100
    gpt4_cost_multiplier: 20.0
```

### Supported Models

- **GPT Models**: `gpt-4`, `gpt-4-32k`, `gpt-4-turbo`, `gpt-3.5-turbo`, `gpt-3.5-turbo-16k`
- **Claude Models**: `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`, `claude-2.1`, `claude-2.0`, `claude-instant-1`

## 📋 Examples

### Example 1: Basic Waste Detection
```bash
crashlens scan logs.jsonl
```
**Output:**
```
🔒 CrashLens runs 100% locally. No data leaves your system.
🚨 **CrashLens Token Waste Report**
==================================================
💰 **Total Potential Savings**: $4.87
🎯 **Wasted Tokens**: 83,407
📊 **Issues Found**: 56

🔄 **Retry Loop** (4 issues)
  🟡 Retry loop detected: 5 calls for same prompt
     💰 Waste: $0.0015
     🎯 Tokens: 25
     🔄 Retries: 5
     ⏱️  Time: 4.0 seconds
     📄 Sample: What is 2+2?
     🔗 Trace: trace_001
```

### Example 2: Cost Summary
```bash
crashlens scan logs.jsonl --summary
```
**Output:**
```
🔒 CrashLens runs 100% locally. No data leaves your system.
📊 **CrashLens Cost Summary**
==================================================
💰 **Total Cost**: $0.2161
🎯 **Total Tokens**: 3,523
📈 **Total Traces**: 8

🛣️  **Cost by Route**
  /api/generate: $0.1200 (55.5%)
  /api/reports: $0.0480 (22.2%)
  /api/analyze: $0.0473 (21.9%)

🤖 **Cost by Model**
  gpt-4: $0.1683 (77.9%)
  claude-3-opus: $0.0450 (20.8%)
  claude-3-sonnet: $0.0023 (1.1%)
```

### Example 3: Markdown Report
```bash
crashlens scan logs.jsonl --format markdown
```
**Output:**
```markdown
🔒 CrashLens runs 100% locally. No data leaves your system.

# CrashLens Token Waste Report

## Summary

| Metric | Value |
|--------|-------|
| Total Potential Savings | $4.87 |
| Wasted Tokens | 83,407 |
| Issues Found | 56 |

## Retry Loop (4 issues)

### 🟡 Issue #1
**Description**: Retry loop detected: 5 calls for same prompt
- **Waste Cost**: $0.0015
- **Waste Tokens**: 25
- **Retry Count**: 5
- **Time Span**: 4.0 seconds
- **Trace ID**: `trace_001`
```

## 🚀 Quick Start

1. **Install**: `poetry install`
2. **Test**: `crashlens scan examples/demo-logs.jsonl`
3. **Analyze your logs**: `crashlens scan your-logs.jsonl`
4. **Get summary**: `crashlens scan your-logs.jsonl --summary`
5. **Generate report**: `crashlens scan your-logs.jsonl --format markdown`

## 📝 License

MIT License. See [LICENSE](LICENSE).

## 🙏 Acknowledgements

- Inspired by Langfuse, OpenAI, and the GPT developer community.

---

*CrashLens is a trust-first CLI tool designed to run offline and help you optimize your AI costs in 60 seconds.* 