import sys
import logging
from pathlib import Path
from typing import Optional

import rich
from rich.logging import RichHandler

from config import get_settings
from tools.registry import get_registry
from tools.extract_tool import extract_pdf, extract_pdf_batch
from tools.summarize_tool import summarize_pdf, summarize_text
from tools.search_tool import search_pdf, search_batch
from tools.report_tool import generate_report
from tools.send_tool import send_report
from scheduler.cron import Scheduler
from core.summarizer import Summarizer
from core.extractor import PDFExtractor
from mailer.smtp_client import SMTPClient


def setup_logging():
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )


def cmd_extract(args):
    result = extract_pdf(file_path=args.file)
    rich.print(f"[green]Extracted:[/] {result['filename']}")
    rich.print(f"Pages: {result['page_count']}")
    rich.print(f"Content length: {len(result['content'])} chars")


def cmd_summarize(args):
    result = summarize_pdf(file_path=args.file, max_tokens=args.max_tokens)
    rich.print(f"[green]Summary of[/] {result['filename']}:")
    rich.print(result["summary"])
    rich.print(f"\n[dim](model: {result['model']}, tokens: {result['tokens_used']})[/dim]")


def cmd_search(args):
    result = search_pdf(file_path=args.file, pattern=args.pattern, case_sensitive=args.case_sensitive)
    rich.print(f"[green]Search[/] '{args.pattern}' in {result['filename']}:")
    rich.print(f"  {result['match_count']} matches found")
    for m in result["matches"][:20]:
        rich.print(f"  L{m['line']}: {m['text'][:120]}")


def cmd_report(args):
    result = generate_report(file_paths=args.files, output_path=args.output)
    if result["output_path"]:
        rich.print(f"[green]Report saved to:[/] {result['output_path']}")
    else:
        rich.print(result["report"])


def cmd_send(args):
    result = send_report(
        subject=args.subject,
        body=args.body,
        attachment_path=args.attachment,
        to=args.to,
    )
    rich.print(f"[green]Email sent[/] to {result['to']}")


def cmd_schedule(args):
    scheduler = Scheduler()

    def daily_job():
        settings = get_settings()
        pdf_dir = Path(settings.pdf_watch_dir)
        pdfs = list(pdf_dir.glob("*.pdf"))
        if not pdfs:
            logging.info("Daily job: no PDFs found in %s", pdf_dir)
            return
    scheduler.daily(daily_job, hour=8, minute=0, job_id="daily_report")

    def weekly_job():
        settings = get_settings()
        pdf_dir = Path(settings.pdf_watch_dir)
        pdfs = [str(p) for p in pdf_dir.glob("*.pdf")]
        if not pdfs:
            logging.info("Weekly job: no PDFs found in %s", pdf_dir)
            return
        report = generate_report(file_paths=pdfs)
        client = SMTPClient()
        client.send(
            subject="Weekly PDF Report",
            body=report["report"],
            to=[settings.email_to],
        )
    scheduler.weekly(weekly_job, day_of_week="mon", hour=9, minute=0, job_id="weekly_report")

    scheduler.start()
    rich.print("[green]Scheduler started[/]")
    rich.print("Jobs:")
    for j in scheduler.list_jobs():
        rich.print(f"  {j['id']} ({j['schedule']}) - next: {j['next_run']}")

    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.stop()
        rich.print("\n[yellow]Scheduler stopped[/]")


def cmd_list_tools(args):
    registry = get_registry()
    rich.print("[bold]Registered Tools:[/bold]")
    for t in registry.list_tools():
        rich.print(f"  [cyan]{t.name}[/]")
        rich.print(f"    {t.description}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        prog="pdfextroctor",
        description="Automated PDF extraction and reporting system",
    )
    sub = parser.add_subparsers(dest="command")

    p_extract = sub.add_parser("extract", help="Extract text from a PDF")
    p_extract.add_argument("file", help="Path to PDF")

    p_summarize = sub.add_parser("summarize", help="Extract and summarize a PDF")
    p_summarize.add_argument("file", help="Path to PDF")
    p_summarize.add_argument("--max-tokens", type=int, default=1024)

    p_search = sub.add_parser("search", help="Search within a PDF")
    p_search.add_argument("file", help="Path to PDF")
    p_search.add_argument("pattern", help="Search pattern")
    p_search.add_argument("--case-sensitive", action="store_true")

    p_report = sub.add_parser("report", help="Generate report from PDFs")
    p_report.add_argument("files", nargs="+", help="PDF files")
    p_report.add_argument("--output", "-o", help="Output file path")

    p_send = sub.add_parser("send", help="Send an email report")
    p_send.add_argument("--subject", required=True)
    p_send.add_argument("--body", required=True)
    p_send.add_argument("--attachment")
    p_send.add_argument("--to")

    p_schedule = sub.add_parser("schedule", help="Start the scheduler")
    p_tools = sub.add_parser("tools", help="List registered tools")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    setup_logging()

    cmds = {
        "extract": cmd_extract,
        "summarize": cmd_summarize,
        "search": cmd_search,
        "report": cmd_report,
        "send": cmd_send,
        "schedule": cmd_schedule,
        "tools": cmd_list_tools,
    }

    handler = cmds.get(args.command)
    if handler:
        handler(args)


if __name__ == "__main__":
    main()
