# ocdimage.emnrd

## Requirements

- Python 3
    
## Setup

    $ python -m venv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt

## Usage

Specify the filing date using the '-f/--filing-date' command line option:

    $ python scraper.py -f '<mm/dd/yyyy>'

Eg,

    $ python scraper.py -f '07/01/2019'
    [ scraper.py:124 - get_records() ] 25 results
    [ scraper.py:82 - goto_next_page() ] Going to next page
    [ scraper.py:124 - get_records() ] 50 results
    [ scraper.py:82 - goto_next_page() ] Going to next page
    [ scraper.py:124 - get_records() ] 52 results
    [ scraper.py:82 - goto_next_page() ] Going to next page
    [ scraper.py:127 - get_records() ] Completed scraping with 52 results

Results are written into the CSV file records.csv in the current directory.

