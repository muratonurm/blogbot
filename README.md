# BlogBot — Automated Blog Content Generator

BlogBot is a Python CLI that writes SEO-friendly blog posts with ChatGPT every day and delivers them to your inbox, ready to review and publish.

## 🔄 How It Works

```text
 ┌──────────────┐      ┌──────────────┐      ┌──────────────────────────┐
 │ prompts.txt  │ ───▶ │   BlogBot    │ ───▶ │ Scrape.do ChatGPT Plugin │
 │ one per line │      │ (daily run)  │ ◀─── │    returns Markdown      │
 └──────────────┘      └──────┬───────┘      └──────────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
      ┌─────────────────┐           ┌─────────────────┐
      │   HTML email    │           │  output/*.md    │
      │  to your inbox  │           │  saved locally  │
      └─────────────────┘           └─────────────────┘
```

1. You write your blog topics as complete ChatGPT prompts in `prompts.txt`.
2. Every day at your chosen time, BlogBot takes the next prompts in the list.
3. Each prompt is sent to ChatGPT through Scrape.do's ChatGPT plugin endpoint.
4. The generated posts are emailed to you as one HTML message and saved to `output/` as `.md` files.
5. BlogBot remembers where it stopped, so the next run continues with the next prompt.

## ✨ Features

- **Daily automated blog generation**: set a time and forget about it
- **Powered by ChatGPT** via the Scrape.do plugin
- **No OpenAI API key required**: a Scrape.do token is all you need
- **Unlimited retry on failed requests**: timeouts, HTTP 429 and 5xx errors are retried until they succeed
- **Progress tracking**: prompts are never repeated until the whole list has been used
- **HTML email delivery**: all posts from a run arrive in a single, nicely formatted email
- **Markdown output**: every post is also saved as a `.md` file
- **GitHub Actions ready**: run it in the cloud for free, no server needed
- **Simple CLI**: run, test, check status and reset with one command

## 📋 Requirements

- Python **3.10+**
- A [Scrape.do](https://scrape.do) account (free tier available)
- An email account with SMTP access

## 🚀 Quick Start

**Step 1: Clone the repo**

```bash
git clone https://github.com/muratonurm/blogbot.git
cd blogbot
```

**Step 2: Create a virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Step 3: Configure your environment**

```bash
cp .env.example .env
```

Then open `.env` and fill in your credentials (see **Configuration** below).

**Step 4: Add your prompts**

Open `prompts.txt` and add one ChatGPT prompt per line (see **Writing Good Prompts** below).

**Step 5: Run**

```bash
python main.py --now --count 1
```

About 20–30 seconds later, a post appears in `output/` and an email lands in your inbox. You're all set.

## ⚙️ Configuration (.env)

```ini
SCRAPE_DO_TOKEN=your_scrape_do_token
EMAIL_FROM=you@yourdomain.com
EMAIL_TO=you@yourdomain.com
EMAIL_PASSWORD=your_email_password
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
```

| Variable | Description |
|---|---|
| `SCRAPE_DO_TOKEN` | Your API token. Get it from [dashboard.scrape.do](https://dashboard.scrape.do). |
| `EMAIL_FROM` | The sender address. It's also used as the SMTP login username. |
| `EMAIL_TO` | Where to receive the blogs. Separate multiple addresses with commas: `a@x.com,b@x.com`. |
| `EMAIL_PASSWORD` | The password (or app password) for `EMAIL_FROM`. |
| `SMTP_HOST` | Your SMTP server, e.g. `smtp.gmail.com` or `mail.privateemail.com`. |
| `SMTP_PORT` | Usually `587` (STARTTLS). Use `465` for SSL. |

> `.env` is git-ignored. Never commit real credentials.

Other settings live in `config.py`:

| Setting | Default | Description |
|---|---|---|
| `PROMPTS_PER_RUN` | `2` | Prompts processed per run |
| `SCHEDULE_TIME` | `"09:00"` | Daily run time in scheduler mode (`HH:MM`) |
| `TIMEZONE` | `"Europe/Istanbul"` | Timezone for `SCHEDULE_TIME` |
| `REQUEST_TIMEOUT` | `60` | Seconds to wait for a single Scrape.do response |
| `RETRY_DELAY` | `30` | Seconds to wait between retries |
| `LOG_LEVEL` | `"INFO"` | Logging verbosity |
| `OUTPUT_DIR` | `"output"` | Folder for generated `.md` files |

## ✍️ Writing Good Prompts (prompts.txt)

Each line in `prompts.txt` is one complete ChatGPT prompt. Here is a template that works well:

```text
Write a complete SEO-optimized blog post titled "Your Title Here". Requirements: 900-1100 words, H2 and H3 subheadings, target audience [your audience], strong CTA at the end directing readers to [your website]. Format: Markdown only.
```

**Rules**

- One prompt per line. A prompt can't contain line breaks.
- Lines starting with `#` are ignored.
- Empty lines are skipped.
- Prompts cycle back to the start when the list is finished.

**Tips**

- **Put the title in quotes after `titled`.** BlogBot uses it for the email heading and the file name.
- **End with `Format: Markdown only.`** so ChatGPT doesn't add "Sure! Here's your post:" around the content.
- **Be specific about your audience.** "Operations managers at e-commerce brands" gives much better results than "businesses".
- **Ask for structure explicitly**, e.g. "include a comparison table" or "add an FAQ section with 4 questions".
- **Add new prompts at the end of the file.** Reordering lines shifts the saved position. If you do reorder, run `python main.py --reset`.

## 💻 CLI Commands

```bash
python main.py                   # Start scheduler
python main.py --now             # Run immediately
python main.py --now --count 1   # Test with 1 prompt
python main.py --status          # Show progress
python main.py --reset           # Reset progress
```

Example `--status` output:

```text
BlogBot Status

Total prompts  : 10
Processed today: 2
Last run       : 2026-08-11 09:00
Next run       : 2026-08-12 09:00
Last index     : 4
Remaining      : 6
Total processed: 4
```

Example `--now` output:

```text
[2026-08-11 09:00:01] INFO: Starting run: 2 prompt(s) from index 0
[2026-08-11 09:00:01] INFO: Processing prompt 1/2 (prompts.txt #1)
[2026-08-11 09:00:24] INFO: Succeeded on attempt 1
[2026-08-11 09:00:24] INFO: Saved: output/2026-08-11_blog_1_your-title.md (1012 words)
[2026-08-11 09:00:24] INFO: Processing prompt 2/2 (prompts.txt #2)
[2026-08-11 09:00:47] WARNING: Attempt 1 failed (HTTP 502), retrying in 30s...
[2026-08-11 09:01:40] INFO: Succeeded on attempt 2
[2026-08-11 09:01:40] INFO: Saved: output/2026-08-11_blog_2_another-title.md (987 words)
[2026-08-11 09:01:42] INFO: Email sent to you@yourdomain.com
[2026-08-11 09:01:42] INFO: Run finished: 2/2 succeeded
```

Logs are written to both the console and `blogbot.log`.

## ☁️ GitHub Actions Setup (Free Automated Runs)

The workflow at `.github/workflows/blogbot.yml` runs BlogBot in the cloud every day, so you don't need a machine that stays on.

**1. Fork this repository**

**2. Enable Actions on your fork**

Open the **Actions** tab of your fork and click **I understand my workflows, go ahead and enable them**. GitHub disables scheduled workflows on forks by default.

**3. Add repository secrets**

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Value |
|---|---|
| `SCRAPE_DO_TOKEN` | Your Scrape.do token |
| `EMAIL_FROM` | Your sender email |
| `EMAIL_PASSWORD` | Your email password |
| `EMAIL_TO` | Where to receive blogs |
| `PROMPTS_CONTENT` | The full content of your `prompts.txt` |

> **Why `PROMPTS_CONTENT`?** The workflow writes this secret into `prompts.txt` before each run. Your prompts never have to be committed to the repository, so they stay private even if the repo is public.

**4. Set your SMTP server**

`SMTP_HOST` and `SMTP_PORT` are set directly in `.github/workflows/blogbot.yml`. Change them to match your email provider:

```yaml
SMTP_HOST: smtp.yourprovider.com
SMTP_PORT: "587"
```

**5. Done**

The workflow runs **daily at 06:00 UTC**. GitHub Actions always uses UTC, so edit `cron: "0 6 * * *"` to change the time. To run it right away, open **Actions → BlogBot Daily Run → Run workflow**.

> **Note:** every Actions run starts from a fresh checkout, and `progress.json` is not committed back to the repository. On GitHub Actions, each run therefore starts from the first prompt. Progress tracking works fully when you run BlogBot locally or with cron.

## 📁 Output

Every post is saved to the `output/` folder:

```text
output/2026-08-11_blog_1_your-title.md
```

The file name is `{date}_blog_{prompt number}_{title slug}.md`. If a response can't be parsed, the raw response is saved to `output/raw/` for debugging.

**Email format**

- **Subject:** `BlogBot | 2026-08-11 | 2 Blogs Ready`
- **Body:** HTML formatted, all blogs in one email, tables included. A plain-text version is included for clients that don't render HTML.

If no post was generated in a run, no email is sent.

## 🛠️ Troubleshooting

| Error | Solution |
|---|---|
| `HTTP 401` | Check `SCRAPE_DO_TOKEN`. This error isn't retried. |
| `HTTP 502` | Temporary issue. It's retried automatically every `RETRY_DELAY` seconds. |
| `HTTP 429` | Rate limit reached. It's retried automatically. If it keeps happening, check your Scrape.do credits. |
| Timeout | Retried automatically. If it happens often, increase `REQUEST_TIMEOUT` in `config.py`. |
| `SMTP authentication failed` | Check `EMAIL_FROM` and `EMAIL_PASSWORD`. Gmail requires an [app password](https://support.google.com/accounts/answer/185833). |
| `Failed to send email: ... timed out` | Your SMTP port may be blocked. Try `SMTP_PORT=465`. |
| `No prompts found` | Check that `prompts.txt` exists and has content. On GitHub Actions, check the `PROMPTS_CONTENT` secret. |
| `Could not parse JSON response` | Inspect the saved response in `output/raw/`. |

For anything else, check `blogbot.log`.

## 🔌 How Scrape.do ChatGPT Plugin Works

BlogBot uses Scrape.do's ChatGPT plugin endpoint to generate content. No OpenAI API key is required, just a Scrape.do token.

```http
GET https://api.scrape.do/plugin/chatgpt/chat?token=YOUR_TOKEN&q=URL_ENCODED_PROMPT
```

The response is JSON, and the generated post lives in `output.markdown`:

```json
{
  "output": {
    "markdown": "# Your Title Here\n\n..."
  }
}
```

BlogBot parses this JSON, removes `:::` citation blocks and any wrapping code fences, then saves the post and emails it. A response usually takes around 20–25 seconds.

## 📄 License

MIT License

## 🧰 Built With

- [Python 3.10+](https://www.python.org/)
- [Scrape.do ChatGPT Plugin](https://scrape.do)
- [schedule](https://pypi.org/project/schedule/), [requests](https://pypi.org/project/requests/), [markdown2](https://pypi.org/project/markdown2/), [pytz](https://pypi.org/project/pytz/), [python-dotenv](https://pypi.org/project/python-dotenv/)
