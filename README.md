# ocdimage.emnrd

## Requirements

- Python 3
- [Redis](https://redis.io/download)

The webapps-rrc-texas.py script uses Redis for caching. The script needs to know the password used in your Redis setup. You
can configure the password in the script in [init_method](). It's currently set to 'foobared' as a placeholder.

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

