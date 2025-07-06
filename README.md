# CrashLens

> Detect token waste patterns in GPT API logs. Offline, fast, and privacy-first.

## 🚀 What is CrashLens?

CrashLens is a CLI tool that scans Langfuse-style JSONL logs of GPT API usage and detects token waste patterns like retry loops, fallback storms, and inefficient GPT-4 usage. It estimates monthly cost waste and prints Slack-style or Markdown alerts to stdout. All processing is 100% local — no internet access, no SDK, no YAML input required.

## ⚡ Features

- **Detects token waste**: Retry loops, fallback storms, and inefficient GPT-4 usage
- **Estimates cost waste**: Uses editable `config/pricing.yaml`
- **Slack-style or Markdown output**: Choose your preferred format
- **Offline & privacy-first**: No network calls, no data leaves your machine
- **Easy to use**: One command, 60 seconds to ROI simulation

## 📦 Installation

### With Poetry
```bash
poetry install
poetry run crashlens scan examples/demo-logs.jsonl
```

### With pipx
```bash
pipx run crashlens scan examples/demo-logs.jsonl
```

## 🛠️ Usage

```bash
crashlens scan <log_file.jsonl> [--format slack|markdown] [--config config/pricing.yaml]
```

- `log_file.jsonl`: Path to your Langfuse-style JSONL log file
- `--format`: Output format (`slack` or `markdown`, default: `slack`)
- `--config`: Optional path to pricing config

## 🧩 Project Structure

```
crashlens/
├── cli.py                  # Main Click CLI entrypoint
├── detectors/              # Token waste detection rules
│   ├── retry_loops.py
│   ├── gpt4_short.py
│   └── fallback_storm.py
├── parsers/
│   └── langfuse.py         # JSONL loader, trace grouper by trace_id
├── reporters/
│   ├── slack_formatter.py
│   └── markdown_formatter.py
├── config/
│   └── pricing.yaml        # Editable model pricing config
├── examples/
│   └── demo-logs.jsonl     # Sample Langfuse-style logs
├── tests/
│   └── test_rules.py
├── README.md
├── LICENSE
├── pyproject.toml
└── .gitignore
```

## 📝 License

MIT License. See [LICENSE](LICENSE).

## 🙏 Acknowledgements

- Inspired by Langfuse, OpenAI, and the GPT developer community.

---

*CrashLens is a trust-first CLI MVP designed to run offline and simulate ROI in 60 seconds.* 