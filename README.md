# md-drop

Capture Markdown content from anywhere and sync it into your Obsidian vault.

## How It Works

```
[Any Browser] --POST--> [Google Apps Script Web App] --> [Google Sheet]
                                                              |
[Any Email Client] --email--> [Gmail label: md-drop]          |
                                    |                         |
                                    +-------+    +------------+
                                            v    v
                                      [sync.py on laptop]
                                            |
                                            v
                                    [Obsidian Vault/Inbox/]
```

**Two input methods:**
- **Web form** — a Google Apps Script web app you can open on any browser (even devices you don't own). Bookmark the URL and you're set.
- **Email** — send an email to your Gmail address (with an optional `+md` alias). The subject becomes the title, the body becomes the note.

**Storage buffer:** Google Sheets (for web submissions) and Gmail (for email). Both are always available and human-readable — you can open the Sheet or Gmail to see pending captures anytime.

**Sync client:** A Python script that runs on the machine with your Obsidian vault. It pulls pending content from both sources, writes `.md` files to your vault, and marks items as synced.

## Setup

### 1. Create the Google Sheet

1. Go to [Google Sheets](https://sheets.google.com) and create a new spreadsheet
2. Name it `md-drop-inbox` (or anything — the ID is what matters)
3. Rename the first sheet tab to `inbox`
4. Add headers in row 1: `timestamp | title | body | source | status | synced_at`
5. Copy the **spreadsheet ID** from the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`

### 2. Deploy the Google Apps Script Web App

Install `clasp` (the Apps Script CLI):

```bash
npm install -g @google/clasp
clasp login
```

Create and deploy the web app:

```bash
cd appscript/
clasp create --title "md-drop" --type standalone --rootDir .
clasp push
```

Set the required Script Properties:

```bash
# Open the Apps Script editor in your browser
clasp open
```

In the Apps Script editor:
1. Go to **Project Settings** (gear icon) > **Script Properties**
2. Add `SHEET_ID` = the spreadsheet ID from step 1
3. Add `AUTH_TOKEN` = a random secret string (e.g., generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`)

Deploy the web app:
1. Click **Deploy** > **New deployment**
2. Type: **Web app**
3. Execute as: **Me**
4. Who has access: **Anyone**
5. Click **Deploy** and copy the URL

Your capture URL is: `https://script.google.com/macros/s/.../exec?t=YOUR_AUTH_TOKEN`

Bookmark this URL on all your devices. The token in the URL acts as authentication — anyone with the full URL can submit notes.

### 3. Set Up the Gmail Filter

1. Open [Gmail](https://mail.google.com)
2. In the search bar, click the filter icon (or go to Settings > Filters)
3. Create a filter:
   - **To:** `your+md@gmail.com` (your Gmail address, optionally with a `+md` alias)
4. Choose action:
   - **Apply the label:** `md-drop` (create it if it doesn't exist)
   - **Skip the Inbox** (optional, keeps your inbox clean)
5. Save the filter

Now any email sent to that address will be automatically labeled.

### 4. Set Up Google Cloud OAuth (for the sync client)

The sync client needs OAuth credentials to access the Sheets API and Gmail API.

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project called `md-drop`
3. Enable the **Google Sheets API** and **Gmail API**:
   - Go to **APIs & Services** > **Library**
   - Search for and enable both APIs
4. Create OAuth credentials:
   - Go to **APIs & Services** > **Credentials**
   - Click **Create Credentials** > **OAuth client ID**
   - Application type: **Desktop app**
   - Name: `md-drop`
   - Download the JSON file
5. Place it at `~/.config/md-drop/credentials.json`

> **Note:** You may also need to configure the OAuth consent screen (under APIs & Services > OAuth consent screen). Set it to "External" and add yourself as a test user. This is a one-time setup.

### 5. Install the Sync Client

```bash
cd /path/to/md-drop
pip install -e .
```

### 6. Configure the Sync Client

Create `~/.config/md-drop/config.toml`:

```toml
[vault]
path = "/path/to/your/obsidian/vault"
strategy = "inbox"        # "inbox" = individual files, "daily" = append to daily note
inbox_folder = "Inbox"

[google]
credentials_file = "~/.config/md-drop/credentials.json"
token_file = "~/.config/md-drop/token.json"
sheet_id = "YOUR_SPREADSHEET_ID"

[gmail]
enabled = true
label = "md-drop"
synced_label = "md-drop-synced"

[sync]
interval_seconds = 300
```

### 7. First Run (OAuth)

```bash
md-drop --once --verbose
```

This will open a browser window for Google OAuth consent. Log in and grant access. The refresh token is saved to `~/.config/md-drop/token.json` — you won't need to do this again.

### 8. Set Up Automatic Sync

Add a cron job on the machine with your Obsidian vault:

```bash
crontab -e
```

Add:

```
*/5 * * * * /path/to/venv/bin/md-drop --once >> ~/.local/log/md-drop.log 2>&1
```

Or use a systemd user timer for more control:

```ini
# ~/.config/systemd/user/md-drop.service
[Unit]
Description=md-drop sync

[Service]
ExecStart=/path/to/venv/bin/md-drop --once
```

```ini
# ~/.config/systemd/user/md-drop.timer
[Unit]
Description=md-drop sync timer

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

```bash
systemctl --user enable --now md-drop.timer
```

## Usage

### Web Form

Open your bookmarked URL on any device. Type a title (optional) and your Markdown content, then hit Send.

### Email

Send an email to your Gmail address (the one you set up the filter for) from any email client. The subject line becomes the note title, and the email body becomes the content. HTML emails are automatically converted to Markdown.

### Manual Sync

```bash
# Dry run — see what would be synced
md-drop --once --dry-run

# Sync once
md-drop --once

# Run in a loop (every 5 minutes by default)
md-drop

# Verbose output
md-drop --once -v

# Custom config file
md-drop --config /path/to/config.toml --once

# Override vault path
md-drop --vault /tmp/test-vault --once
```

## Vault Output

### Inbox Strategy (default)

Each capture becomes its own file in `Vault/Inbox/`:

```
Vault/
  Inbox/
    2026-03-25-quick-thought-about-api-design.md
    2026-03-25-article-to-read-later.md
```

Each file has YAML front matter:

```yaml
---
date: '2026-03-25T14:32:00+00:00'
source: web
tags:
- inbox
title: Quick thought about API design
---

The actual content here...
```

### Daily Strategy

Captures are appended to today's daily note under a `## Captures` heading:

```markdown
# 2026-03-25

## Captures

### 14:32 (web)
**Quick thought about API design**
The actual content here...

### 15:10 (email)
**Article to read later**
Check out this article...
```

## Security

- The web form URL contains a secret token as a query parameter. Anyone with the full URL can submit. Keep it private — treat it like a password.
- To rotate the token: update the `AUTH_TOKEN` Script Property in the Apps Script editor and update your bookmarks.
- OAuth credentials and refresh tokens are stored locally at `~/.config/md-drop/`. Keep this directory secure.
- The Google Sheet is accessible only to your Google account.

## Troubleshooting

**"credentials file not found"** — Download OAuth credentials from [Google Cloud Console](https://console.cloud.google.com) and place at `~/.config/md-drop/credentials.json`.

**"Invalid token" on web form** — The `AUTH_TOKEN` Script Property doesn't match the `?t=` parameter in your URL. Check both.

**Gmail label not found** — Create the `md-drop` label in Gmail manually, or send a test email to your address and the filter will create it.

**OAuth token expired** — Delete `~/.config/md-drop/token.json` and run `md-drop --once` to re-authenticate.

**"SHEET_ID not configured"** — Set the `SHEET_ID` Script Property in the Apps Script editor.

**Duplicates appearing** — The sync client deduplicates by content hash within each run, but if the same content is submitted multiple times across runs (and already synced), it won't prevent re-creation. Items are marked as synced in the source (Sheet/Gmail) so they won't be re-processed.
