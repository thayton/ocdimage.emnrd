# ocdimage.emnrd

## Requirements

- Python 3
- [Redis](https://redis.io/download)

The webapps-rrc-texas.py script uses Redis for caching. The script needs to know the password used in your Redis setup. You'll
need to set the password that Redis uses on your setup in the script in the [init_cache](https://github.com/thayton/ocdimage.emnrd/blob/83b7f8dcdee386d963141bf8c81122655fbf158c/webapps-rrc-texas.py#L68). It's currently set to 'foobared' as a placeholder.

## Setup

    $ python -m venv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt

## Usage

### ocdimage.py Scraper

Specify the filing date using the '-f/--filing-date' command line option:

    $ python ocdimage.py -f '<mm/dd/yyyy>'

Eg,

    $ python ocdimage.py -f '07/01/2019'
    [ ocdimage.py:124 - get_records() ] 25 results
    [ ocdimage.py:82 - goto_next_page() ] Going to next page
    [ ocdimage.py:124 - get_records() ] 50 results
    [ ocdimage.py:82 - goto_next_page() ] Going to next page
    [ ocdimage.py:124 - get_records() ] 52 results
    [ ocdimage.py:82 - goto_next_page() ] Going to next page
    [ ocdimage.py:127 - get_records() ] Completed scraping with 52 results

Results are written into the CSV file records.csv in the current directory.

### webapps-rrc-texas.py Scraper

Specify the from date, to date, and operator number using the '-f', '-t' and '-o' command line options:

    $ python webapps-rrc-texas.py -f '01/01/2018' -t '01/01/2019' -o '251726'
