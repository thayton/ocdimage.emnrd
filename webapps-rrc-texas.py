import os
import re
import csv
import json
import shutil
import logging
import argparse
import requests
import mimetypes

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

#
# 1. Plug in Date From, Date To, and Filing Operator No (e.g., 01/01/2018, 01/01/2019, 251726)
# 2. Click Search at the very bottom of the form
# 3. Crawl all of the ‘Tracking No’ links on all of the resulting pages
# 4. Create a folder on the local filesystem with name corresponding to ‘API No.’ for each above link
# 5. Crawl all of the ‘View’ links beneath each ‘Tracking No’ Link
# 6. Create a subfolder to #4 above with name corresponding to ‘Operator Name’
# 7. Save each attachment in the #6 subfolder above named according to the value in the Form/Attachment column (e.g., W-2.pdf)
#
class RccTexasScraper(object):
    def __init__(self):
        self.url = 'http://webapps.rrc.texas.gov/CMPL/publicSearchAction.do'
        self.params = {
            'formData.methodHndlr.inputValue': 'init',
            'formData.headerTabSelected': 'home',
            'formData.pageForwardHndlr.inputValue': 'home'
        }
        self.search_params = {
            'pager.pageSize': 100,
            'pager.offset': 0,
            'formData.methodHndlr.inputValue': 'search',
            'searchArgs.paramValue': '|0={0}|1={1}|5={2}|17=N|18=N|19=N|21=N',
            'offset': 0,
            'pageSize': '10',
            'formData.hrefValue': '|1003=home|1005=home|1007=0'
        }
        
        self.session = requests.Session()        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
        }

        FORMAT = "[ %(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
        logging.basicConfig(format=FORMAT)

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def is_already_downloaded(self, filename):
        pass
    
    def download_forms(self, record, check_if_already_downloaded=True):
        # download / api-no / operator-name / <form-name>
        self.logger.info(f'Getting forms at {record["url"]}')

        subdir = os.path.realpath(os.path.join(
            os.path.dirname(__file__), f'downloads/{record["api-no"]}/{record["operator-name"]}/'
        ))
        os.makedirs(subdir, exist_ok=True)

        for f in record['forms']:
            resp = self.session.get(f['url'], headers=self.headers, stream=True)
            file_ext = mimetypes.guess_extension(resp.headers['Content-Type'])

            # Add the numeric suffic to the filenames as some of the form/attachment names
            # are duplicated. Ie, there's multiple rows named 'Plat' or 'Other' etc. so this
            # is a way to differentiate them
            r = re.compile(r'dpimages/r/(\d+)$')
            m = re.search(r, f['url'])

            if m:
                filename = f'{f["name"]}-{m.group(1)}{file_ext}'
            else:
                filename = f'{f["name"]}{file_ext}'

            path = os.path.realpath(os.path.join(subdir, filename))
            if check_if_already_downloaded and os.path.exists(path):
                self.logger.info(f'Form {path} already downloaded - skipping download')
                continue

            self.logger.info(f'Downloading {os.path.basename(path)}')
            with open(path, 'wb') as fd:
                resp.raw.decode_content = True
                shutil.copyfileobj(resp.raw, fd)

        self.logger.info(f'Finished downloading {len(record["forms"])} forms at {record["url"]}')

    def get_record_details(self, record):
        #XXX Caching here with Redis
        resp = self.session.get(record['url'], headers=self.headers)
        soup = BeautifulSoup(resp.text, 'html.parser')

        f = lambda t: t.name == 'td' and t.text.strip().startswith('Operator Name:')
        td = soup.find(f)
        record['operator-name'] = td.strong.text.strip()

        f = lambda t: t.name == 'th' and t.text.strip() == 'Form/Attachment'
        th = soup.find(f)
        tb = th.find_parent('table')

        record['forms'] = []
        
        f = lambda t: t.name == 'a' and t.text.strip() == 'View'
        for a in tb.find_all(f):
            tr = a.find_parent('tr')
            td = tr.find_all('td')

            form = {}
            form['name'] = td[0].text.strip()
            form['url'] = urljoin(self.url, a['href'])

            record['forms'].append(form)
    
    def submit_search(self, from_date='01/01/2018', to_date='01/01/2019', filing_operator='251726'):
        '''
        Submit search via query parameters
        '''
        self.search_params['searchArgs.paramValue'] = self.search_params['searchArgs.paramValue'].format(from_date, to_date, filing_operator)
        resp = self.session.get(self.url, params=self.search_params, headers=self.headers)
        return resp

    def submit_search_post(self, from_date='01/01/2018', to_date='01/01/2019', filing_operator='251726'):
        '''
        Submit search by posting form data
        '''
        resp = self.session.get(self.url, params=self.params, headers=self.headers)
        soup = BeautifulSoup(resp.text, 'html.parser')

        form = soup.find('form', attrs={'name': 'externalPacketForm'})
        data = {}
        
        for i in form.find_all('input'):
            if i.get('type') == 'button' and i.get('value') != 'Search':
                # Only send the search button
                continue
            
            if i.get('name'):
                data[i['name']] = i.get('value')

        for s in form.find_all('select'):
            if s.get('name'):
                data[s['name']] = s.get('value')

        #data[form['name']] = form['value']

        del data['searchArgs.excludeStatusAndApprovedDtHndlr.booleanValue']
        
        data['searchArgs.fromSubmitDtArgHndlr.inputValue'] = from_date
        data['searchArgs.toSubmitDtArgHndlr.inputValue'] = to_date
        data['searchArgs.operatorNoArgHndlr.inputValue'] = filing_operator

        # From the page source:
        #
        # function doSearch(){
        #   document.forms[1]['formData.methodHndlr.inputValue'].value='search';
        #   document.forms[1].submit();
        # }
        data['formData.methodHndlr.inputValue'] = 'search'

        form_url = urljoin(self.url, form.attrs['action'])
        resp = self.session.post(form_url, data=data, headers=self.headers)

        return resp
        
    def get_records(self, from_date='01/01/2018', to_date='01/01/2019', filing_operator='251726'):
        records = []
        
        resp = self.submit_search(from_date, to_date, filing_operator)

        while resp != None:
            soup = BeautifulSoup(resp.text, 'html.parser')

            for a in soup.select('table.DataGrid a[href*="?packetSummary"]'):
                tr = a.find_parent('tr')
                td = tr.find_all('td')

                rec = {}
                rec['tracking-no'] = a.text.strip()
                rec['url'] = self.url + re.sub(r';jsessionid=[^?]*', '', a['href'])
                rec['api-no'] = td[3].text.strip()
                
                records.append(rec)

            break #XXX
            self.logger.info(f'{len(records)} records')

            f = lambda t: t.name == 'a' and t.text.strip() == '[Next>]'
            next_page = soup.find(f)
            if next_page is None:
                break

            self.logger.info('Going to next page')

            url = urljoin(self.url, next_page['href'])
            resp = self.session.get(url, headers=self.headers)
            
        self.logger.info(f'Completed scraping with {len(records)} results')            
        return records

    def scrape(self, from_date='01/01/2018', to_date='01/01/2019', filing_operator='251726'):
        records = self.get_records(from_date, to_date, filing_operator)

        # Get the links to the forms from the details page
        for r in records:
            self.get_record_details(r)
            break #XXX

        # Download the attachments
        for r in records:
            self.download_forms(r)
            
def is_valid_date(s):
    try:
        d = datetime.strptime(s, "%m/%d/%Y")
    except ValueError:
        msg = "Invalid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)
    else:
        return d.strftime("%m/%d/%Y")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--from-date", help="From date in format mm/dd/yyyy", required=True, type=is_valid_date)
    parser.add_argument("-t", "--to-date", help="To date in format mm/dd/yyyy", required=True, type=is_valid_date)
    parser.add_argument("-o", "--filing-operator", help="Filing operator Number", required=True, type=int)    

    args = parser.parse_args()

    scraper = RccTexasScraper()
    scraper.scrape(args.from_date, args.to_date, args.filing_operator)
    
