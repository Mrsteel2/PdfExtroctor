import os
import shutil
from pathlib import Path
from datetime import datetime

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, jsonify, send_file,
)

from core.extractor import PDFExtractor
from core.summarizer import Summarizer
from tools.search_tool import search_pdf
from tools.report_tool import generate_report
from tools.send_tool import send_report
from config import get_settings, Settings
from mailer.smtp_client import SMTPClient

app = Flask(__name__)
app.secret_key = os.urandom(24)

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = BASE_DIR / "input"
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER = BASE_DIR / "output"
OUTPUT_FOLDER.mkdir(exist_ok=True)

extractor = PDFExtractor()


@app.route("/")
def index():
    pdfs = sorted(UPLOAD_FOLDER.glob("*.pdf"), key=os.path.getmtime, reverse=True)
    return render_template("index.html", pdfs=pdfs)


@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("files")
    if not files or files[0].filename == "":
        flash("No files selected", "error")
        return redirect(url_for("index"))
    for f in files:
        if f.filename.lower().endswith(".pdf"):
            f.save(str(UPLOAD_FOLDER / f.filename))
            flash(f"Uploaded {f.filename}", "success")
    return redirect(url_for("index"))


@app.route("/extract/<filename>")
def extract(filename):
    path = UPLOAD_FOLDER / filename
    if not path.exists():
        flash(f"File not found: {filename}", "error")
        return redirect(url_for("index"))
    try:
        result = extractor.extract(path)
        return jsonify({
            "filename": result.filename,
            "content": result.content,
            "page_count": result.page_count,
            "metadata": result.metadata,
            "extracted_at": result.extracted_at.isoformat(),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/summarize/<filename>")
def summarize(filename):
    path = UPLOAD_FOLDER / filename
    if not path.exists():
        return jsonify({"error": "File not found"}), 404
    try:
        extraction = extractor.extract(path)
        summarizer = Summarizer()
        result = summarizer.summarize(extraction)
        return jsonify({
            "filename": result.extraction.filename,
            "summary": result.summary,
            "model": result.model,
            "tokens_used": result.tokens_used,
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search/<filename>")
def search(filename):
    pattern = request.args.get("q", "")
    if not pattern:
        return jsonify({"error": "No search query provided"}), 400
    path = UPLOAD_FOLDER / filename
    if not path.exists():
        return jsonify({"error": "File not found"}), 404
    try:
        result = search_pdf(file_path=str(path), pattern=pattern)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/report", methods=["POST"])
def report():
    filenames = request.form.getlist("files")
    if not filenames:
        flash("No files selected", "error")
        return redirect(url_for("index"))
    paths = [str(UPLOAD_FOLDER / f) for f in filenames]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = str(OUTPUT_FOLDER / f"report_{ts}.md")
    try:
        result = generate_report(file_paths=paths, output_path=out)
        flash(f"Report saved: {result['output_path']}", "success")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"Report failed: {e}", "error")
        return redirect(url_for("index"))


@app.route("/send", methods=["POST"])
def send():
    subject = request.form.get("subject", "PDF Report")
    body = request.form.get("body", "Please find the attached report.")
    to = request.form.get("to", "")
    attachment = request.form.get("attachment", "")
    try:
        result = send_report(
            subject=subject,
            body=body,
            attachment_path=attachment if attachment else None,
            to=to if to else None,
        )
        flash(f"Email sent to {result['to']}", "success")
    except Exception as e:
        flash(f"Email failed: {e}", "error")
    return redirect(url_for("index"))


@app.route("/generate_and_send", methods=["POST"])
def generate_and_send():
    filenames = request.form.getlist("files")
    to = request.form.get("to", "")
    subject = request.form.get("subject", "PDF Report")
    body = request.form.get("body", "Please find the attached PDF report.")
    if not filenames:
        flash("No files selected", "error")
        return redirect(url_for("index"))
    if not to:
        flash("No email address provided", "error")
        return redirect(url_for("index"))
    paths = [str(UPLOAD_FOLDER / f) for f in filenames]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = str(OUTPUT_FOLDER / f"report_{ts}.md")
    try:
        report_result = generate_report(file_paths=paths, output_path=out)
        email_result = send_report(
            subject=subject,
            body=body,
            attachment_path=out,
            to=to,
        )
        flash(f"Report generated and email sent to {email_result['to']}", "success")
    except Exception as e:
        flash(f"Failed: {e}", "error")
    return redirect(url_for("index"))


@app.route("/download/<path:filename>")
def download(filename):
    return send_file(OUTPUT_FOLDER / filename, as_attachment=True)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        env_path = Path(".env")
        lines = []
        for key in [
            "OPENROUTER_API_KEY", "OPENROUTER_MODEL",
            "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD",
            "EMAIL_FROM", "EMAIL_TO", "EMAIL_CC",
        ]:
            val = request.form.get(key, "")
            lines.append(f"{key}={val}")
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        flash("Settings saved. Restart the app to apply.", "success")
        return redirect(url_for("index"))
    return render_template("settings.html", settings=get_settings())


@app.route("/delete/<filename>")
def delete(filename):
    path = UPLOAD_FOLDER / filename
    if path.exists():
        path.unlink()
        flash(f"Deleted {filename}", "success")
    return redirect(url_for("index"))


@app.route("/preview/<filename>")
def preview(filename):
    path = UPLOAD_FOLDER / filename
    if not path.exists():
        flash(f"File not found: {filename}", "error")
        return redirect(url_for("index"))
    return send_file(path, mimetype="application/pdf")


@app.route("/history")
def history():
    reports = sorted(OUTPUT_FOLDER.glob("report_*.md"), key=os.path.getmtime, reverse=True)
    report_list = []
    for r in reports:
        report_list.append({
            "name": r.name,
            "size": round(r.stat().st_size / 1024, 1),
            "created": datetime.fromtimestamp(r.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return render_template("history.html", reports=report_list)


@app.route("/delete_report/<filename>")
def delete_report(filename):
    path = OUTPUT_FOLDER / filename
    if path.exists():
        path.unlink()
        flash(f"Deleted {filename}", "success")
    return redirect(url_for("history"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
