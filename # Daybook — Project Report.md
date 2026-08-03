# Daybook — Project Report

## 1. Summary

Daybook began as a single-page static HTML/CSS/JS daily to-do app
(`index.html`, `style.css`, `script.js`, plus a stdlib-only Python CLI
that generated offline analytics reports from exported JSON). It was
rebuilt as a full Django application, then extended in nine phases into
a combined task manager and full-featured habit tracker: multiple habit
types, a swimlane day timeline, statistics and gamification, a journal,
account management, visual customization, and scheduled email reports.

This document records what was built, the reasoning behind the harder
design decisions, what was deliberately left out or simplified, and what
would be the natural next steps.

## 2. Architecture

Three Django apps, with a deliberate one-directional dependency:

```
reports  ──depends on──▶  tasks
habits   ──depends on──▶  tasks
tasks    ──never depends on either──
```

`tasks` owns authentication (register/login/logout) and the original
one-off task list, and knows nothing about habits. `habits` is the
larger app — it imports from `tasks` where it genuinely needs to (e.g.
the Yearly Calendar's day-detail view shows both habit entries and
tasks; the "Today's Habits" section embedded on the Tasks page is built
from a `tasks.views.index()` call into `habits.services`). This
direction was chosen once, early, and held for the rest of the build —
`tasks` never imports from `habits`, which keeps the dependency graph a
simple line rather than a cycle.

`reports` is the older, task-only analytics app (weekly/monthly/custom
reports on `Task` completion, inherited from the original Python CLI
tool); `habits/analytics.py` is a parallel, independent implementation
of the same *shape* of problem (day-by-day aggregation, calendar-week
padding, heatmaps) for habits, kept separate rather than sharing code
with `reports`, since forcing a shared abstraction across "tasks
completed" and "habits completed" turned out to need more special-casing
than it saved.

### Data model, by app

**tasks**
- `Task` — one-off items; also self-referential (`parent`) for subtasks, and optionally linked to a `TaskTemplate`
- `Tag` — free-form, per-user
- `TaskTemplate` — recurring-task definitions (daily/weekdays/custom days), materialized into real `Task` rows once per day
- `Streak` — per-user daily-completion streak counter

**habits**
- `Habit` — the core model: type (yes_no/numeric/checklist), section, schedule, duration, pause/archive state, grace-day allowance, color
- `HabitChecklistItem` — template sub-items for checklist-type habits
- `HabitEntry` — one row per habit per day; meaning of its value fields depends on the parent habit's type
- `UserSettings` — one per user: theme/accent/card-theme preferences, timeline hours, daily-report settings, avatar
- `JournalEntry` — one per user per day, with mood + free text
- `WeeklyReview` / `HabitReviewRating` — the weekly review wizard's stored ratings
- `UserBadge` — unlock records; badge *definitions* live in code (`habits/badges.py`), not the database

### Cross-cutting mechanisms

- **CSS custom properties as the theming backbone.** Every color in the app is a `var(--accent)`, `var(--accent-soft)`, etc., set at `:root`. Dark mode, the 8 accent-color presets, and the 3 card themes are all just attribute-selector overrides of these same variables (`[data-theme="dark"]`, `[data-accent="rose"]`, `[data-card-theme="bold"]`) — none of it required touching individual component styles, because the components were built referencing variables from day one.
- **A context processor** (`habits/context_processors.py`) injects the current user's `UserSettings` into every template as `global_user_settings`, so `base.html` can set the accent/theme attributes on `<html>` without every view needing to fetch and pass it manually.
- **Shared partials over duplicated markup.** The habit card markup exists once (`habits/templates/habits/_habit_card_compact.html`) and is reused both on the full Habits management page and the compact "Today's Habits" section on the Tasks page — same CSS classes and `data-` attributes, so the existing `habits.js` event handlers work on both without new JavaScript.

## 3. Build log, by phase

| Phase | What it added |
|---|---|
| 0 | Data model foundation: `Habit`, `HabitChecklistItem`, `HabitEntry`, `UserSettings` — models/admin/migrations only, no UI |
| 1 | Core habit CRUD, the three habit types' interaction UI, pause/resume, grace days |
| 2 | Drag-and-drop reordering (SortableJS) and bulk move/archive/delete |
| 3 | Swimlane Timeline — a from-scratch interval-partitioning/column-packing layout algorithm, unit-tested standalone before wiring into a view |
| 4 | Statistics: overview dashboard, year heatmap, report card (rolling 30-day letter grade), time-of-day analysis, per-habit stats page, and the JSON export endpoint (later reused by Backup & Restore) |
| 5 | Yearly Calendar + day detail, Daily Journal, Weekly Habit Review wizard |
| 6 | Badge rule engine, evaluated on-demand after any habit-logging action |
| 7 | Multi-part Profile page (account/password/preferences), Backup & Restore (import added, reusing the Phase 4 export), the browser back-button-after-logout cache fix |
| 8 | Accent colors, card themes, avatar upload with server-side resizing |
| 9 | Daily Report email (SMTP settings, HTML email template, management command, optional in-process scheduler), plus unifying habits onto the main Tasks screen |

## 4. Notable design decisions

**Streak definition.** A day counts toward a streak if it has an entry
marked `completed` or `used_grace_day`. A day with *no entry at all* —
including today, before anything's been logged — does not break an
otherwise-live streak; it simply isn't counted yet. This is
deliberately more lenient than the "longest streak ever" calculation
used on stats pages, which does treat a gap day as a break, since that
one is describing settled history rather than an in-progress streak.

**Report Card rubric.** A simple lookup table (A ≥90%, B ≥75%, C ≥60%,
D ≥40%, F below), evaluated over a fixed rolling 30-day window ending
today — independent of whatever custom date range a stats page happens
to be showing, since a report card answers "how am I doing right now,"
not "how did I do in this arbitrary past window."

**Backup/restore without a merge UI.** The plan explicitly cut a
conflict-resolution interface as disproportionate effort for how rarely
two divergent datasets actually need merging. Import instead just skips
any habit whose id already exists — safe by construction, since ids are
UUIDs and only collide when re-importing data that came from this same
account's own earlier export.

**Card theming via a consolidated `!important` override list**, rather
than retrofitting every page's local component styles to reference
shared spacing/shadow variables. Each page's `<style>` block was written
independently across nine phases with its own hardcoded radius/shadow
values; centralizing those retroactively across ~15 templates was judged
not worth the regression risk for a "polish" feature, so the theme
override instead targets every known card-like class by name from one
place. The tradeoff is explicit in a code comment: a future new "card"
class won't be automatically themeable.

**Auto-color assignment for habits.** A habit with no manually chosen
color gets one deterministically derived from its own UUID
(`int(habit.id.hex[:8], 16) % len(palette)`), so the same habit always
renders the same color across sessions without needing to store a value —
and without needing every habit to be manually colored just to look
visually distinct on the timeline.

## 5. Known limitations and deliberate simplifications

- No per-user timezone for the daily report send time (server-local only) — flagged in code comments and the README rather than silently implied to work.
- No true push notifications — in-app due-time badges only; a real implementation needs a service worker, Push API, and VAPID keys, which is a materially larger feature.
- The in-process scheduler duplicates sends under multiple worker processes; there is no in-app fix for this, only the documented recommendation to switch to cron + management command in that deployment shape.
- `UserSettings.dark_mode` exists as a field but nothing reads it; an earlier version of the Preferences form included it despite no template rendering it, which meant every settings save silently reset it to `False` — caught and fixed by removing it from the form during Phase 8.
- Checklist habit items are regenerated wholesale on every edit (new ids each time), so heavily edited checklists can lose clean historical continuity.
- Bulk "move to section" doesn't renumber the `order` field, so moved habits can land in a not-quite-predictable position until manually dragged once.

## 6. Testing methodology

Django itself could not be run in the environment this project was
built in (no network access to install it), so verification relied on
static analysis at every phase:

- `python -m py_compile` on every Python file touched
- `node --check` on every JavaScript file touched
- A small script counting `{% if %}/{% endif %}`, `{% for %}/{% endfor %}`,
  and `{% block %}/{% endblock %}` per template, flagging any imbalance
- A second script cross-referencing every `{% url 'name' %}` reference
  against every `path(..., name=...)` actually defined, project-wide
- Pure-logic functions with no database dependency (the timeline
  layout algorithm, heatmap color thresholds, letter-grade cutoffs,
  calendar-week padding) were extracted and unit-tested directly with
  hand-constructed scenarios

This caught real bugs before they reached the user (an inverted
`widthratio` denominator, a `make_list` filter misuse in a progress-bar
loop, the silent `dark_mode` reset described above) but is not a
substitute for actually running the app — several issues surfaced
afterward regardless were consistently traced back to instructed file
edits not being applied verbatim, rather than logic errors, and were
resolved by shifting to handing over complete files for anything
previously edited rather than incremental diffs.

## 7. Suggested next steps

- Add a real per-user timezone field to `UserSettings` if the daily
  report's send time needs to be accurate to the user's actual location.
- Move card-theme styling onto shared CSS variables consumed directly by
  each component, retiring the `!important` override list.
- A lightweight "add subtask"/checklist-item editor that preserves item
  identity across edits, instead of full regeneration.
- CSV export/import for habits, alongside the existing JSON backup.
- A Correlation Chart and a proper conflict-resolution UI for imports —
  both explicitly deferred earlier in the project as low-value for the
  effort relative to everything else on the list.