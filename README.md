# CrashLens

> Detect token waste patterns in GPT API logs. Offline, fast, and privacy-first.

## 🚀 What is CrashLens?

CrashLens is a CLI tool that scans Langfuse-style JSONL logs of GPT API usage and detects token waste patterns like retry loops, fallback storms, and inefficient expensive model usage. It estimates monthly cost waste and prints Slack-style or Markdown alerts to stdout. All processing is 100% local — no internet access, no SDK, no YAML input required.

## ⚡ Features

- **🔍 Detects token waste patterns**: Retry loops, fallback storms, and inefficient expensive model usage
- **💰 Cost estimation**: Supports GPT-4, GPT-3.5, and Claude models with accurate pricing
- **📊 Multiple output formats**: Slack-style, Markdown, and cost summary modes
- **🔒 Privacy-first**: 100% local processing, no data leaves your machine
- **🛡️ PII Protection**: Automatically scrubs sensitive data from outputs
- **📥 Flexible input**: File, stdin pipe, or clipboard paste
- **🎯 Smart suggestions**: Recommends cheaper model alternatives
- **📈 Monthly projections**: Estimates potential savings over time
- **📋 Aggregated reporting**: Groups similar issues for cleaner output
- **🔐 Safe sharing**: Summary-only mode for internal reports

## 📦 Installation

```bash
# Clone the repository
git clone <repository-url>
cd crashlens

# Install dependencies with Poetry
poetry install

# Activate the Poetry shell
poetry shell

# Run the tool
crashlens scan examples/demo-logs.jsonl
```

## 🛠️ Usage

### Basic Commands

#### File Input
```bash
# Analyze a log file (includes pricing by default)
crashlens scan logs.jsonl

# With custom pricing config
crashlens scan logs.jsonl --config custom-pricing.yaml

# Output in Markdown format
crashlens scan logs.jsonl --format markdown

# Safe internal report (no prompts/trace IDs)
crashlens scan logs.jsonl --summary-only
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
crashlens scan --paste --format markdown --summary-only
```

### Output Modes

#### 1. **Waste Detection Mode** (Default)
Detects and reports token waste patterns with aggregated summaries:
```bash
crashlens scan logs.jsonl
```

**Detects:**
- 🔄 **Retry Loops**: Multiple calls with the same prompt
- 💎 **Expensive Model Usage**: GPT-4/Claude for simple tasks
- ⚡ **Fallback Storms**: Multiple model switches in one trace

**Shows:**
- 🧾 Total AI spend for analyzed period
- 💰 Potential savings from optimization
- 📊 Aggregated issues by type and model
- 🎯 Sample prompts and suggested fixes

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

#### 4. **Summary-Only Mode**
Safe for internal sharing (suppresses prompts and trace IDs):
```bash
crashlens scan logs.jsonl --summary-only
```

### Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `log_file.jsonl` | Path to JSONL log file | `crashlens scan logs.jsonl` |
| `--stdin` | Read from stdin pipe | `cat logs.jsonl \| crashlens scan --stdin` |
| `--paste` | Read from clipboard | `crashlens scan --paste` |
| `--format` | Output format | `--format markdown` |
| `--summary` | Cost summary mode | `--summary` |
| `--summary-only` | Safe internal report | `--summary-only` |
| `--config` | Custom pricing config (uses built-in by default) | `--config pricing.yaml` |
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
│   ├── short_model_detector.py # Detects expensive model overuse
│   └── fallback_storm.py      # Detects model switching patterns
├── parsers/
│   └── langfuse.py            # JSONL loader, trace grouper by trace_id
├── reporters/
│   ├── slack_formatter.py     # Emoji-rich Slack-style output
│   ├── markdown_formatter.py  # Copy-paste ready Markdown reports
│   └── summary_formatter.py   # Cost aggregation by route/model/team
├── utils/
│   └── pii_scrubber.py        # PII detection and scrubbing
├── config/
│   └── pricing.yaml           # Model pricing configuration
├── examples/
│   ├── demo-logs.jsonl        # Sample Langfuse-style logs
│   ├── aggregation-test.jsonl # Test aggregation functionality
│   └── pii-test.jsonl         # Test PII scrubbing
├── tests/
│   └── test_rules.py
├── README.md
├── LICENSE
├── pyproject.toml
└── .gitignore
```

## 🔧 Configuration

### Automatic Pricing

CrashLens now includes pricing configuration by default! Every scan automatically calculates:

- **Total AI Spend**: Complete cost of all API calls
- **Total Tokens**: Combined input and output tokens
- **Total Traces**: Number of unique trace IDs
- **Model Usage Breakdown**: Cost per model with call counts
- **Waste Percentage**: Percentage of spend that's wasted

No need to specify `--config` unless you want to use custom pricing.

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
🧾 **Total AI Spend**: $77.84
💰 **Total Potential Savings**: $62.27
🎯 **Wasted Tokens**: 1,682,325
📊 **Issues Found**: 6,629

💎 **Expensive Model Short** (4,231 issues)
  • 4,231 traces used GPT-4 instead of gpt-3.5-turbo
  • Est. waste: $45.23
  • Sample prompts: "What is 2+2?...", "Hello...", "Translate this..."
  • Suggested fix: route short prompts to gpt-3.5-turbo

🔄 **Retry Loops** (2,398 issues)
  • 2,398 traces with excessive retries
  • Est. waste: $17.04
  • Suggested fix: implement exponential backoff and circuit breakers

📈 **Monthly Projection**: $1,868.10 potential savings
```

### Example 2: Cost Summary Mode
```bash
crashlens scan logs.jsonl --summary
```
**Output:**
```
🔒 CrashLens runs 100% locally. No data leaves your system.
📊 **CrashLens Cost Summary**
==================================================
💰 **Total Cost**: $123.45
🎯 **Total Tokens**: 2,500,000
📈 **Total Traces**: 1,000

🛣️ **Cost by Route**
  /api/chat: $98.76 (80.0%)
  /api/completions: $24.69 (20.0%)

🤖 **Cost by Model**
  gpt-4: $74.07 (60.0%)
  gpt-3.5-turbo: $49.38 (40.0%)

👥 **Cost by Team**
  engineering: $61.73 (50.0%)
  marketing: $37.04 (30.0%)
  sales: $24.68 (20.0%)
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
| Total AI Spend | $77.84 |
| Total Potential Savings | $62.27 |
| Wasted Tokens | 1,682,325 |
| Issues Found | 6,629 |
| Traces Analyzed | 1,000 |

## Expensive Model Short (4,231 issues)

| Metric | Value |
|--------|-------|
| Total Waste Cost | $45.23 |
| Total Waste Tokens | 1,200,000 |

**Issue**: 4,231 traces used GPT-4 instead of gpt-3.5-turbo

**Sample Prompts**:
1. `What is 2+2?...`
2. `Hello...`
3. `Translate this...`

**Suggested Fix**: Route short prompts to `gpt-3.5-turbo`
```

### Example 4: Safe Internal Report
```bash
crashlens scan logs.jsonl --summary-only
```
**Output:**
```
🔒 CrashLens runs 100% locally. No data leaves your system.
📝 Summary-only mode: Prompts, sample inputs, and trace IDs are suppressed for safe internal sharing.
🚨 **CrashLens Token Waste Report**
==================================================
🧾 **Total AI Spend**: $77.84
💰 **Total Potential Savings**: $62.27
🎯 **Wasted Tokens**: 1,682,325
📊 **Issues Found**: 6,629

💎 **Expensive Model Short** (4,231 issues)
  • 4,231 traces used GPT-4 instead of gpt-3.5-turbo
  • Est. waste: $45.23
  • Suggested fix: route short prompts to gpt-3.5-turbo
```

## 🔒 Privacy & Security

### PII Protection
CrashLens automatically scrubs sensitive information from outputs:
- **Removed fields**: `user_id`, `email`, `phone`, `api_key`, `password`, etc.
- **Masked patterns**: Email addresses, phone numbers, credit cards, SSNs, IPs, UUIDs
- **Safe metadata**: Recursively cleans nested metadata objects

### Local Processing
- **No internet access**: All processing happens on your machine
- **No data transmission**: Logs never leave your system
- **No external dependencies**: Works offline with just Python

## 🎯 Detection Rules

### 1. Expensive Model Short Detector
**Triggers when:** Expensive models (GPT-4, Claude-3-Opus) used for short prompts
**Threshold:** Configurable minimum tokens (default: 100)
**Suggestion:** Route to cheaper alternatives (GPT-3.5-Turbo, Claude-3-Haiku)

### 2. Retry Loop Detector
**Triggers when:** Same prompt called multiple times in short period
**Threshold:** Configurable retry count and time window
**Suggestion:** Implement exponential backoff and circuit breakers

### 3. Fallback Storm Detector
**Triggers when:** Multiple model switches in single trace
**Threshold:** Configurable fallback count and time window
**Suggestion:** Optimize model selection logic

## 📊 Aggregation & Reporting

### Smart Aggregation
- **Groups similar issues**: Combines identical waste patterns
- **Shows sample prompts**: Up to 3 unique examples per group
- **Consolidated metrics**: Total counts, costs, and tokens per group
- **Actionable summaries**: Clear suggested fixes for each pattern

### Output Formats
- **Slack-style**: Emoji-rich, compact summaries for team chat
- **Markdown**: Copy-paste ready reports for documentation
- **Summary-only**: Safe for internal sharing (no sensitive data)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Inspired by the need for better GPT API cost monitoring
- Built with privacy and simplicity in mind
- Thanks to the open source community for the tools that made this possible 