# Morning Briefing

A Python script that prints a daily morning briefing on a thermal receipt printer. Designed to run on a Raspberry Pi via cron.

## What It Prints

```
================================
        MORNING BRIEFING
     Sunday, 01 March 2026
             09:00
================================

 WEATHER - *YOUR CITY*
--------------------------------
  Partly cloudy
  Now:      6.5C
  High/Low: 11.8 / 3.6C
  Humidity: 85%
  Wind:     6.3 km/h

 TOP HEADLINES
--------------------------------
  1. Some world news headline
  2. Another headline here
  ...

 TODAY'S SCHEDULE
--------------------------------
  09:00 - Team standup
  14:00 - Dentist appointment

================================
      Have a great day!
================================
```

## Features

- **Weather** via [Open-Meteo](https://open-meteo.com/) (free, no API key needed)
- **News headlines** via BBC World RSS (configurable to any RSS feed)
- **Calendar events** via iCal URLs (supports multiple calendars – Outlook, Apple, Google)
- **Auto-cut** after printing (ESC/POS command)
- **Zero external APIs** requiring authentication for weather and news

## Hardware

- Raspberry Pi (any model with network access)
- ESC/POS thermal receipt printer (tested with Epson TM-T20II)
- Printer connected via USB and configured in CUPS

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/morning-briefing.git
cd morning-briefing
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
nano .env
```

At minimum, set your `PRINTER_NAME` and `ICAL_URLS`. See [Configuration](#configuration) below.

### 4. Test it

```bash
venv/bin/python morning_briefing.py
```

You should see the briefing output in your terminal and a receipt printed.

### 5. Schedule it with cron

```bash
crontab -e
```

Add this line (adjust path and time as needed):

```
0 9 * * * /home/pi/morning-briefing/venv/bin/python /home/pi/morning-briefing/morning_briefing.py
```

## Configuration

All configuration is done via environment variables. Copy `.env.example` to `.env` and fill in your values.

| Variable | Description | Default |
|---|---|---|
| `PRINTER_NAME` | CUPS printer name (find with `lpstat -p`) | — |
| `PRINT_WIDTH` | Character width of your thermal printer | `32` |
| `LATITUDE` | Weather location latitude | `52.50` |
| `LONGITUDE` | Weather location longitude | `20.01` |
| `LOCATION_NAME` | Location name shown on the receipt | `City` |
| `ICAL_URLS` | Comma-separated list of iCal URLs | — |
| `NUM_HEADLINES` | Number of news headlines to show | `5` |
| `NEWS_RSS_URL` | RSS feed URL for news | BBC World RSS |
| `GREETING` | Footer message on the receipt | `Have a great day!` |

### Getting iCal URLs

**Outlook / Microsoft 365:**
Settings → View all Outlook settings → Calendar → Shared calendars → Publish a calendar → Copy the ICS link

**Apple Calendar (iCloud):**
iCloud.com → Calendar → Share icon → Public Calendar → Copy URL

**Google Calendar:**
Settings → Click your calendar → Integrate calendar → Secret address in iCal format

### Multiple Calendars

Set `ICAL_URLS` as a comma-separated list:

```
ICAL_URLS=https://calendar1.ics,https://calendar2.ics
```

Events from all calendars are merged and sorted by time.

## Customization

- **News source**: Change `NEWS_RSS_URL` to any RSS feed (e.g. `https://rss.dw.com/xml/rss/en/top` for Deutsche Welle)
- **Print width**: Set `PRINT_WIDTH` to `48` for 80mm paper, `32` for 58mm
- **Cut command**: Change `b'\x1d\x56\x00'` (full cut) to `b'\x1d\x56\x01'` (partial cut) in `print_briefing()`
- **Paper feed**: Adjust the number of `\n` in `print_briefing()` if the cut happens too early or too late

## Requirements

- Python 3.7+
- `icalendar` (installed via requirements.txt)
- CUPS configured with your thermal printer

## License

MIT
