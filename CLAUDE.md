# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

md-drop captures Markdown content from web forms and email, then syncs it into an Obsidian vault. It consists of a Google Apps Script web app (form submission → Google Sheet) and a Python sync client that pulls pending notes from Sheets/Gmail and writes them to a vault.

## Commands

```bash
# Install in dev mode (from repo root, with venv active)
pip install -e ".[dev]"

# Run tests
pytest

# Run a single test
pytest tests/test_writer.py::test_function_name

# Run the sync client
md-drop --once --dry-run        # one-shot dry run
md-drop --once --verbose        # one-shot with logging
md-drop                         # continuous mode (5-min interval)
md-drop --config path.toml --vault /path/to/vault
```

## Architecture

**Data flow:** Web Form/Email → Google Sheet/Gmail → `sync.py` (fetch → deduplicate via SHA256 content hash → write → mark synced) → Obsidian Vault

**Key modules in `src/md_drop/`:**

- **sync.py** — CLI entry point (Click). Orchestrates the fetch→write→mark loop. Handles OAuth2 credentials with token refresh. Supports `--once` or looping mode.
- **config.py** — TOML config loader. Defines `VaultConfig` (path, strategy, folders), `GoogleConfig` (credentials, sheet_id), `GmailConfig` (enabled, labels), `SyncConfig` (interval).
- **writer.py** — Two vault strategies: **inbox** (one file per note, `YYYY-MM-DD-{slug}.md`) and **daily** (append to `YYYY-MM-DD.md` under `## Captures`). Generates YAML frontmatter.
- **sources/sheet.py** — Fetches rows where status='pending' from Google Sheets, marks them 'synced' after write.
- **sources/gmail.py** — Fetches messages by label, extracts body (prefers text/plain, falls back to HTML→Markdown), marks synced via label. Auto-creates labels if missing.
- **formatter.py** — HTML→Markdown via `markdownify`. Strips script/style/img tags, collapses excess newlines.
- **note.py** — `Note` dataclass: timestamp, title, body, source ("web"/"email"), source_id.

**Google Apps Script (`appscript/`):** `Code.gs` serves an HTML form and appends submissions to a Google Sheet. Auth via token in query param validated against Script Properties.

- `Form.html` — single-file web UI with a Markdown toolbar, Edit/Preview toggle (marked.js via CDN), collapsible Markdown + keyboard shortcuts cheatsheet, and Emacs-style line navigation. All edits go through `execCommand('insertText')` so Ctrl+Z works.
- `deploy.sh` — stamps `VERSION` with the current datetime, runs `clasp push`, then redeploys the existing deployment in-place via `CLASP_DEPLOYMENT_ID` env var (so the web app URL never changes). Run from `appscript/`: `./deploy.sh`.

**PIN-based access (`docs/index.html`):** GitHub Pages entry point served at `maciekk.github.io/md-drop`. Accepts `?pin=` in the URL, redirects to the GAS deployment URL passing the PIN along. GAS then validates the PIN against the `PIN` Script Property, looks up `AUTH_TOKEN`, and meta-refresh redirects to `?t=AUTH_TOKEN`. Lets you access the form from any browser with just a short memorable URL — no long deployment ID or token to remember.

## Build System

Uses `hatchling` for building. Python 3.12+ required. Dependencies: click, google-api-python-client, google-auth-oauthlib, markdownify, python-frontmatter.
