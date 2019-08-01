import re
import csv
import json
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin

class OcdImageScraper(object):
    def __init__(self):
        self.url = 'http://ocdimage.emnrd.state.nm.us/imaging/CaseFileCriteria.aspx'
        self.session = requests.Session()

    def csv_save(self, data):
        headers = [
            'Case Number',
            'Case Type',
            'Applicant',
            'Filing Date',
            'URL'
        ]

        with open('records.csv', 'w') as fp:
            writer = csv.writer(fp, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(headers)

            for d in data:
                row = [
                    d.get('case-number', ''),
                    d.get('case-type', ''),
                    d.get('applicant', ''),
                    d.get('filing-date', ''),
                    d.get('url', ''),
                ]

                writer.writerow(row)
    
    def submit_search(self, filing_date='07/01/2019'):
        resp = self.session.get(self.url)
        soup = BeautifulSoup(resp.text, 'lxml')

        form = soup.select_one('form#form1')
        data = {
            '__EVENTTARGET': None,
            '__EVENTARGUMENT': None
        }

        for i in form.find_all('input'):
            if i.get('name'):
                data[i['name']] = i.get('value')

        for s in form.find_all('select'):
            if s.get('name'):
                data[s['name']] = s.get('value')

        # Case Type: Compulsory Pooling
        # Filing Date: Is After
        data['ctl00$main$ddlCaseType'] = 'CP'
        data['ctl00$main$FilingDate$DateCriteriaList1$ddlCriteria'] = 'GreaterThan'
        data['ctl00$main$FilingDate$txtDate'] = filing_date

        # Make sure only one specific Search button sent
        del data['ctl00$main$btnClearAll']
        del data['ctl00$main$btnGoBack']
        del data['ctl00$main$btnCaseNo']
        
        resp = self.session.post(self.url, data=data)
        return resp

    def goto_next_page(self, soup):
        form = soup.select_one('form#form1')
        data = {}

        for i in form.find_all('input'):
            if i.get('name'):
                data[i['name']] = i.get('value')

        del data['ctl00$main$CaseFileList1$btnReturn']
        
        next_page = soup.select_one('a#Next')
        if next_page == None:
            return None
    
        r = re.compile(r"__doPostBack\('([^']+)',''\)")
        m = re.search(r, next_page['href'])

        data['__EVENTTARGET'] = m.group(1)
        data['__EVENTARGUMENT'] = None

        resp = self.session.post(self.url, data=data)
        return resp

    def get_records(self, filing_date='07/01/2019'):
        records = []
        
        resp = self.submit_search(filing_date)

        while resp != None:
            soup = BeautifulSoup(resp.text, 'lxml')
            
            for a in soup.select('div#pnlList > table a'):
                tr = a.find_parent('tr')
                td = tr.find_all('td')
                
                rec = {}
                rec['url'] = urljoin(self.url, a['href'])
                rec['case-number'] = td[0].text
                rec['case-type'] = td[1].text
                rec['applicant'] = td[2].text
                rec['filing-date'] = td[3].text

                records.append(rec)

            resp = self.goto_next_page(soup)

        return records
        
    def scrape(self, filing_date='07/01/2019'):
        records = self.get_records(filing_date)
        self.csv_save(records)

if __name__ == '__main__':
    scraper = OcdImageScraper()
    scraper.scrape()
