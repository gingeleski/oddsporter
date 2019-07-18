
# oddsporter

Scraping utility for Odds Portal (oddsportal.com) results.

## Setup

These instructions are for Windows Powershell. There will be some differences for OS X / MacOS, like in activating the virtual environment and using the web driver.

Before the scraper will work correctly, you'll need to put the [Chromium web driver](https://sites.google.com/a/chromium.org/chromedriver/) (chromedriver.exe) inside of the *chromedriver* directory. You may also need to update the path to `chromedriver` in the script.

```
cd oddsporter

# Get into a new virtualenv
virtualenv venv
.\venv\Scripts\activate.ps1

# Install the requirements
pip install -r requirements.txt

# Run the program
python op.py

# Then eventually when you're done...
deactivate
```

## Running

By default, the program will scrape all available results for the history of what's specified in `config/sports.json`.

```
python op.py
```

As of this writing, the configured sports/leagues encompass the following:

- NBA (American basketball)
- NHL (American hockey)
- NFL (American football)
- AFL (Australian football)
- NRL (Australian rugby)

It may be possible to scrape other sports/leagues by adding them to the JSON file. This has not been explicitly tested but seems quite possible given the comprehensive nature of this software.

While the program runs, it will print out some log information to the console and also to a timestamped file under `logs/`.

After completion, see the directory `output/`, under which will be populated JSON files of the scraped results.
