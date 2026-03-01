#!/usr/bin/env python3
"""
Morning Briefing Printer
Prints a daily briefing receipt with weather, news headlines, and calendar events.
Designed for a thermal receipt printer via CUPS on a Raspberry Pi.
"""

import subprocess
import textwrap
import json
import urllib.request
import ssl
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from icalendar import Calendar

# ============================================================
# CONFIGURATION
# Override via environment variables or edit defaults here.
# ============================================================

PRINTER_NAME = os.environ.get("PRINTER_NAME", "your-printer-name")
PRINT_WIDTH = int(os.environ.get("PRINT_WIDTH", "32"))

# Weather: Open-Meteo (free, no API key needed)
LATITUDE = float(os.environ.get("LATITUDE", "52.20"))
LONGITUDE = float(os.environ.get("LONGITUDE", "21.01"))
LOCATION_NAME = os.environ.get("LOCATION_NAME", "city")

# Calendar: comma-separated list of iCal URLs
# Supports multiple calendars (Outlook, Apple, Google, etc.)
ICAL_URLS = [
    url.strip() for url in
    os.environ.get("ICAL_URLS", "https://your-ical-url-here.ics").split(",")
    if url.strip()
]

# News
NUM_HEADLINES = int(os.environ.get("NUM_HEADLINES", "5"))
NEWS_RSS_URL = os.environ.get("NEWS_RSS_URL", "https://feeds.bbci.co.uk/news/world/rss.xml")

# Greeting
GREETING = os.environ.get("GREETING", "Have a great day!")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def separator(char="="):
    return char * PRINT_WIDTH

def center(text):
    return text.center(PRINT_WIDTH)

def wrap(text):
    return "\n".join(textwrap.wrap(text, width=PRINT_WIDTH))

def fetch_json(url):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "MorningBriefing/1.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        return json.loads(r.read().decode())

def fetch_text(url):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "MorningBriefing/1.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        return r.read()


# ============================================================
# DATA FETCHERS
# ============================================================

def get_weather():
    """Get current weather from Open-Meteo (free, no API key)."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={LATITUDE}&longitude={LONGITUDE}"
            f"&current=temperature_2m,weathercode,windspeed_10m,relative_humidity_2m"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode"
            f"&timezone=auto&forecast_days=1"
        )
        data = fetch_json(url)
        c = data["current"]
        d = data["daily"]

        codes = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Rime fog", 51: "Light drizzle", 53: "Drizzle",
            55: "Heavy drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain",
            71: "Light snow", 73: "Snow", 75: "Heavy snow",
            80: "Showers", 81: "Heavy showers", 82: "Violent showers",
            95: "Thunderstorm",
        }
        desc = codes.get(c.get("weathercode", 0), "Unknown")

        lines = [
            f"  {desc}",
            f"  Now:      {c['temperature_2m']}C",
            f"  High/Low: {d['temperature_2m_max'][0]} / {d['temperature_2m_min'][0]}C",
            f"  Humidity: {c['relative_humidity_2m']}%",
            f"  Wind:     {c['windspeed_10m']} km/h",
        ]
        rain = d["precipitation_probability_max"][0]
        if rain and rain > 0:
            lines.append(f"  Rain:     {rain}%")
        return lines
    except Exception as e:
        return [f"  Weather unavailable: {e}"]


def get_news():
    """Get top headlines from an RSS feed."""
    try:
        req = urllib.request.Request(
            NEWS_RSS_URL,
            headers={"User-Agent": "MorningBriefing/1.0"})
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            tree = ET.parse(r)
        items = tree.findall(".//item")[:NUM_HEADLINES]
        lines = []
        for i, item in enumerate(items, 1):
            title = item.findtext("title") or "No title"
            lines.append(wrap(f"{i}. {title}"))
        return lines if lines else ["  No news available"]
    except Exception as e:
        return [f"  News unavailable: {e}"]


def get_calendar_events():
    """Get today's events from one or more iCal URLs."""
    today = datetime.now().date()
    all_events = []

    for url in ICAL_URLS:
        if "your-" in url and "-here" in url:
            continue
        try:
            cal = Calendar.from_ical(fetch_text(url))
            for component in cal.walk():
                if component.name != "VEVENT":
                    continue
                dtstart = component.get("dtstart")
                if not dtstart:
                    continue
                dt = dtstart.dt
                if hasattr(dt, "date"):
                    event_date = dt.date()
                    time_str = dt.strftime("%H:%M")
                else:
                    event_date = dt
                    time_str = "All day"
                if event_date == today:
                    summary = str(component.get("summary", "No title"))
                    all_events.append((time_str, summary))
        except Exception as e:
            all_events.append(("??:??", f"Error: {e}"))

    if not all_events:
        return ["  No events today - enjoy!"]
    all_events.sort(key=lambda x: x[0])
    return [wrap(f"  {t} - {s}") for t, s in all_events]


# ============================================================
# BUILD & PRINT
# ============================================================

def build_briefing():
    """Assemble the full briefing text."""
    now = datetime.now()
    lines = [
        "", separator("="),
        center("MORNING BRIEFING"),
        center(now.strftime("%A, %d %B %Y")),
        center(now.strftime("%H:%M")),
        separator("="),
        "", f" WEATHER - {LOCATION_NAME}", separator("-"),
        *get_weather(),
        "", " TOP HEADLINES", separator("-"),
        *get_news(),
        "", " TODAY'S SCHEDULE", separator("-"),
        *get_calendar_events(),
        "", separator("="),
        center(GREETING),
        separator("="), "", "",
    ]
    return "\n".join(lines)


def print_briefing(text):
    """Send text to the thermal printer via CUPS with auto-cut."""
    try:
        data = text.encode("ascii", errors="replace")
        # Feed paper + ESC/POS full cut command
        data += b'\n' * 6
        data += b'\x1d\x56\x00'  # GS V 0 = full cut

        p = subprocess.run(
            ["lp", "-d", PRINTER_NAME, "-o", "raw"],
            input=data, capture_output=True, timeout=30,
        )
        if p.returncode == 0:
            print(f"Printed successfully at {datetime.now()}")
        else:
            print(f"Print error: {p.stderr.decode()}")
    except Exception as e:
        print(f"Failed to print: {e}")


def main():
    print("Building morning briefing...")
    briefing = build_briefing()
    print(briefing)
    print_briefing(briefing)


if __name__ == "__main__":
    main()
