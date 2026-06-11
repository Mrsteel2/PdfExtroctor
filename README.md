# PDF Extractor & Reporting System

Automated PDF extraction and summarization tool using MarkItDown + OpenRouter, with SMTP delivery and cron scheduling.

## Features

- **PDF Extraction** — Extract text from PDFs using [MarkItDown](https://github.com/Franc-dev/markitdown)
- **AI Summarization** — Summarize extracted content via OpenRouter (GPT-4o-mini, etc.)
- **5 Built-in Tools** — Extract, Summarize, Search, Report, Send
- **Email Reports** — SMTP delivery with attachments and CC/BCC
- **Scheduling** — Daily and weekly cron jobs via APScheduler
- **CLI** — Command-line interface for all operations
- **Web UI** — Browser-based interface for non-technical users

## Quick Start

```powershell
# Install dependencies
pip install -r requirements.txt

# Configure API keys
copy .env.example .env
# Edit .env with your OpenRouter API key and SMTP credentials

# Extract a PDF
python main.py extract "input\document.pdf"

# Summarize
python main.py summarize "input\document.pdf"

# Search within a PDF
python main.py search "input\document.pdf" "keyword"

# Generate a report file
python main.py report "input\*.pdf" --output output/report.md

# Send report via email
python main.py send --subject "Report" --body "See attached" --attachment output/report.md

# List all available tools
python main.py tools

# Start the scheduler (daily 8AM + weekly Monday 9AM)
python main.py schedule

# Start the Web UI
python -m web.app
# Open http://localhost:5000 in your browser
```

## Project Structure

```
├── main.py                  # CLI entry point
├── config/settings.py       # Configuration (env vars)
├── core/
│   ├── extractor.py         # PDF extraction via MarkItDown
│   ├── summarizer.py        # OpenRouter summarization
│   └── models.py            # Data models
├── tools/
│   ├── registry.py          # Tool harness (decorator-based)
│   ├── extract_tool.py      # Tool: extract PDF(s)
│   ├── summarize_tool.py    # Tool: summarize PDF/text
│   ├── search_tool.py       # Tool: search within PDFs
│   ├── report_tool.py       # Tool: generate reports
│   └── send_tool.py         # Tool: email delivery
├── mailer/smtp_client.py    # SMTP email automation
├── scheduler/cron.py        # Daily/weekly cron scheduling
├── web/
│   ├── app.py               # Flask web application
│   └── templates/           # HTML templates
├── input/                   # Place PDFs here
├── output/                  # Generated reports
├── .env.example             # Configuration template
└── requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and set:

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | Your OpenRouter API key |
| `OPENROUTER_MODEL` | Model name (default: `openai/gpt-4o-mini`) |
| `SMTP_HOST` / `SMTP_PORT` | SMTP server settings |
| `SMTP_USER` / `SMTP_PASSWORD` | SMTP credentials |
| `EMAIL_FROM` / `EMAIL_TO` | Sender and recipient addresses |
| `PDF_WATCH_DIR` | Directory to watch for PDFs (default: `input`) |
