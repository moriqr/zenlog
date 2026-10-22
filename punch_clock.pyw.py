"""
ZenLog launcher (double-click / legacy entry point).

The app lives in the `zenlog` package:
  - zenlog/app.py              shell + page navigation
  - zenlog/pages/punch_page.py punch clock UI
  - zenlog/pages/calendar_page.py calendar UI
  - zenlog/data.py             persistence / business logic

Run with:  python punch_clock.pyw.py
       or:  python -m zenlog
"""

from zenlog.app import run

if __name__ == "__main__":
    run()
