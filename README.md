# Daybook

A self-hosted, full-stack Django app that combines a daily task manager
with a complete habit tracker — tasks, recurring tasks, habits (Yes/No,
Numeric, Checklist), a swimlane day timeline, statistics, a journal,
gamification, and email reports, all under one login.

Built incrementally across 9 phases on top of an original single-file
static (HTML/CSS/JS) daily to-do app; this is the Django rewrite plus
everything added after it.

---

## Features

### Tasks (daily to-do list)
- One-off daily tasks with category, priority, due time, notes, tags, and subtasks
- Search and tag filtering
- Recurring task templates (daily / weekdays / custom days) that materialize onto today's list automatically
- Drag-free quick actions: toggle, edit, delete, clear completed
- Export to JSON/TXT, import from JSON, export dashboard as PNG
- Daily completion streak

### Habits
- Three habit types: **Yes/No**, **Numeric** (with a target + unit), **Checklist** (with sub-items)
- Three organizational sections: Have To Do / Need To Do / Would Do
- Optional scheduled time + duration, or "anytime"
- Pause/resume, archive, grace days (streak protection for occasional misses)
- Drag-and-drop reordering within and across sections; bulk move/archive/delete
- **Swimlane Timeline** — a day view with colored lanes per habit, automatic overlap/lane-packing, a live current-time needle, and an "anytime" row
- **Today's Habits** also appear directly on the main Tasks screen, fully interactive, alongside one-off tasks and recurring tasks

### Statistics & Analytics
- Overview dashboard: completion rate, section breakdown, top habits, time-of-day analysis
- Year-long GitHub-style contribution heatmap
- Per-habit page: report card (letter grade), current/longest streak, weekly/monthly/yearly numbers, a completion-trend chart, and a streak calendar
- Custom date ranges on every stat view
- Full JSON data export (also used by Backup & Restore)

### Productivity Suite
- Yearly calendar — click any day to see every task, habit entry, and journal entry logged that day
- Daily journal with mood tagging and full-text search
- Weekly Habit Review — a step-by-step wizard rating effort per habit with optional reflection notes

### Gamification
- Badges for streak milestones, total completions, and perfect weeks — unlocked automatically as you use the app, with an in-app toast notification

### Profile & Account
- Change username, email, and password from one Profile page
- Account avatar (auto-resized on upload)
- Preferences: accent color, card theme, compact mode, timeline hours, daily report settings

### Backup & Data Portability
- Download your entire habit history as one JSON file
- Restore from a backup file (additive only — never overwrites existing data; duplicates are skipped by id)

### Customization
- Dark / light mode
- 8 accent color presets, applied instantly across the whole app via CSS custom properties
- 3 card themes (Classic / Minimal / Bold)

### Daily Report email
- Optional daily email summarizing the day's tasks and habits
- SMTP settings via environment variables — nothing hardcoded
- Delivered either by an in-process scheduler (opt-in, single-process deployments) or an external cron job calling a management command (recommended for anything with multiple worker processes)

---

## Tech stack

- **Backend:** Django 4.2+ (tested on 5.2), SQLite
- **Frontend:** vanilla HTML/CSS/JS — no build step, no framework
- **Charts:** Chart.js (CDN)
- **Drag & drop:** SortableJS (CDN)
- **Images:** Pillow (avatar resizing)
- **PDF export:** xhtml2pdf
- **Scheduling:** APScheduler (optional, in-process)

---

## Project structure

```
daybook_django/
├── manage.py
├── requirements.txt
├── db.sqlite3              (created on first migrate)
├── daybook/                 project package
│   ├── settings.py
│   ├── urls.py
│   ├── middleware.py         no-cache middleware (prevents stale pages after logout)
│   └── wsgi.py
├── tasks/                    one-off tasks, recurring task templates, auth
│   ├── models.py             Task, Tag, TaskTemplate, Streak
│   ├── views.py               pages + JSON API + auth (register/login/logout)
│   └── templates/
├── reports/                   weekly/monthly/custom Task reports (heatmap, PDF, trend chart)
│   ├── analytics.py
│   └── templates/
├── habits/                    the habit tracker — the bulk of the app
│   ├── models.py              Habit, HabitChecklistItem, HabitEntry, UserSettings,
│   │                          JournalEntry, WeeklyReview, HabitReviewRating, UserBadge
│   ├── services.py            streak calculation, shared section-builder
│   ├── analytics.py           stats/heatmap/report-card aggregation
│   ├── timeline.py            swimlane layout algorithm (pure Python, unit-tested)
│   ├── badges.py              badge rule engine
│   ├── reports.py             daily report email content + sending
│   ├── scheduler.py           optional in-process APScheduler
│   ├── context_processors.py  injects accent color/card theme/avatar globally
│   ├── management/commands/
│   │   └── send_daily_reports.py
│   └── templates/
├── templates/                 shared base template + icon library
│   ├── base.html
│   └── icons.html             inline SVG icon set (no emoji anywhere in the UI)
└── static/
    ├── css/style.css          single global stylesheet — theming, layout, components
    └── js/
        ├── app.js              Task page interactions
        └── habits.js            Habit interactions (shared by the Habits page and
                                  the "Today's Habits" section on the Tasks page)
```

---

## Setup (fresh install)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser      # optional, for /admin/
python manage.py runserver
```

Open `http://127.0.0.1:8000` — you'll be redirected to sign in. Click
"Create one" to register your first account. Everything (tasks, habits,
journal, stats) is scoped per-account.

## Environment variables

None are required to run locally — sensible defaults are used everywhere
(console email backend, scheduler off). Set these for real email delivery:

| Variable | Purpose | Default |
|---|---|---|
| `DAYBOOK_EMAIL_BACKEND` | Django email backend | console (prints to terminal) |
| `DAYBOOK_EMAIL_HOST` | SMTP host | `localhost` |
| `DAYBOOK_EMAIL_PORT` | SMTP port | `587` |
| `DAYBOOK_EMAIL_HOST_USER` | SMTP username | *(empty)* |
| `DAYBOOK_EMAIL_HOST_PASSWORD` | SMTP password | *(empty)* |
| `DAYBOOK_EMAIL_USE_TLS` | `true`/`false` | `true` |
| `DAYBOOK_DEFAULT_FROM_EMAIL` | From address | `noreply@daybook.local` |
| `DAYBOOK_ENABLE_SCHEDULER` | `1` to auto-start the in-process daily-report scheduler | unset (off) |

**Never commit real SMTP credentials.** Set these in your shell, a
`.env` file loaded before Django starts, or your hosting platform's
secrets manager — not in `settings.py`.

## Sending daily reports

Two ways to trigger `send_daily_reports`, pick one based on your deployment:

- **Single-process deployment** (e.g. `manage.py runserver`, or one gunicorn worker): set `DAYBOOK_ENABLE_SCHEDULER=1` and the app checks every 5 minutes internally.
- **Multiple worker processes** (gunicorn `-w 2+`, uwsgi with multiple processes, etc.): **do not** use the in-process scheduler — each worker would start its own copy and every user would get duplicate emails. Use external cron instead:
  ```
  */5 * * * * cd /path/to/project && python manage.py send_daily_reports
  ```

Test the whole pipeline without real SMTP first:
```bash
python manage.py send_daily_reports --force-user yourusername
```

## Upgrading an existing single-user deployment

If you're running an older version of this app from before multi-user
accounts existed, existing tasks have no owner yet:

```bash
python manage.py migrate
python manage.py createsuperuser --username yourname   # if you don't have one
python manage.py assign_orphan_tasks yourname           # claims pre-existing tasks
```

## Known limitations (worth knowing before you rely on them)

- **Daily report send time is server-local, not per-user.** `UserSettings.daily_report_time` has no timezone attached; "send at 7am" means 7am in the server's configured `TIME_ZONE` (currently UTC), not wherever you actually are.
- **`UserSettings.dark_mode` field is currently unused.** Dark mode is a client-side (localStorage) toggle; this DB field exists for a future server-rendered version but isn't wired to anything yet.
- **No true push notifications.** "Reminders" are in-app due-time badges (Due soon / Overdue) shown while the page is open — not phone/browser push notifications, which would need a service worker, the Push API, and VAPID keys.
- **Backup import never merges conflicting data** — only adds what's missing (matched by id). There's no UI for resolving a true conflict between two divergent datasets.
- **Card themes use `!important` overrides** on a hand-maintained list of container classes; a new "card-like" component added later needs to be added to that list in `static/css/style.css` to stay themeable.
- **Editing a checklist habit's items regenerates them from scratch**, so historical checked-state can go stale if you rename/reorder items after the fact.
- **Bulk "move to section" doesn't renumber `order`** — moved habits may land in a slightly arbitrary position within their new section until you drag one to fix it.

## Testing this project

Where possible, logic that doesn't require a live database was unit-tested
directly (the swimlane timeline layout algorithm, the heatmap color
thresholds, the report-card letter grades, the calendar-week padding).
Everything else was verified through static checks — every Python file
compiles, every JS file passes `node --check`, every template's
`{% if %}/{% for %}/{% block %}` tags balance, and every `{% url %}`
reference resolves to a defined route — but the actual request/response
cycle should still be run and clicked through locally before trusting
any single feature in production.w