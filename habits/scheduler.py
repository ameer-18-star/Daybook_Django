"""
In-process scheduler for the Daily Report email — the lighter of the two
options from the plan (vs. Celery + Redis). Deliberately opt-in
(DAYBOOK_ENABLE_SCHEDULER=1), never auto-started, for two reasons:

1. Django's autoreloader (plain `manage.py runserver`, the default dev
   workflow) actually runs TWO processes — a parent watcher and a child
   worker — and calls AppConfig.ready() in both. Only the child sets
   RUN_MAIN=true. Without the guard below, a naive "just start it in
   ready()" would run two independent schedulers in development and
   double-send every email.

2. In production behind a multi-worker WSGI server (gunicorn -w 2+,
   uwsgi with multiple processes, etc.), EACH worker process loads this
   app and would start its OWN independent scheduler — meaning N workers
   sends every report N times, at the same moment, with no coordination
   between them. There is no clean fix for that from inside the app
   itself. If you deploy with more than one worker process, use the
   management command via external cron instead of this scheduler:

       */5 * * * * cd /path/to/project && python manage.py send_daily_reports

   That runs exactly once regardless of how many web workers you have.
   This in-process scheduler is the right tool specifically for a
   single-process deployment (e.g. `manage.py runserver`, or gunicorn
   with exactly one worker) — which is what a self-hosted, single-user
   tool like this most likely is, but it's worth confirming before you
   flip the switch in a different environment.
"""
import logging
import os

logger = logging.getLogger(__name__)

_started = False


def _run_daily_report_check():
    from django.core.management import call_command
    try:
        call_command('send_daily_reports')
    except Exception:
        logger.exception('send_daily_reports failed')


def start():
    global _started
    if _started:
        return

    if os.environ.get('DAYBOOK_ENABLE_SCHEDULER') != '1':
        return

    # See docstring point 1 — only skip in the autoreloader's parent
    # watcher process (RUN_MAIN present but not 'true'). If RUN_MAIN isn't
    # set at all (no autoreloader — production), proceed normally.
    if 'RUN_MAIN' in os.environ and os.environ.get('RUN_MAIN') != 'true':
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.warning(
            "DAYBOOK_ENABLE_SCHEDULER=1 but APScheduler isn't installed — "
            "run: pip install APScheduler"
        )
        return

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        _run_daily_report_check, 'interval', minutes=5,
        id='daybook_daily_report_check', replace_existing=True,
    )
    scheduler.start()
    _started = True
    logger.info('Daybook daily-report scheduler started (checks every 5 minutes).')