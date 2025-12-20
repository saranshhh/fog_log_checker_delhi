import requests
import ssl
import urllib3
from urllib3.util import create_urllib3_context
from requests.adapters import HTTPAdapter
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import os

# 1. Silence the InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DESecLevelAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.set_ciphers("DEFAULT@SECLEVEL=1")
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super(DESecLevelAdapter, self).init_poolmanager(*args, **kwargs)

def scrape_visibility():
    url = "https://amssdelhi.gov.in/fog/nitc15.php"
    session = requests.Session()
    session.mount("https://", DESecLevelAdapter())

    try:
        response = session.get(url, timeout=20, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_to_save = []

        # Try Method A: Find Table
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cols = [ele.text.strip() for ele in row.find_all(['td', 'th'])]
                if cols:
                    data_to_save.append([timestamp] + cols)
        
        # Try Method B: Find Pre-formatted Text (common on this gov site)
        if not data_to_save:
            pre_text = soup.find('pre')
            if pre_text:
                # Split text into lines and treat as single columns
                lines = pre_text.text.split('\n')
                for line in lines:
                    if line.strip():
                        data_to_save.append([timestamp, line.strip()])

        if not data_to_save:
            print(f"[{timestamp}] Page loaded, but no data found. Site might be blank/updating.")
            return

        # Save to CSV
        file_exists = os.path.isfile('delhi_fog_data.csv')
        with open('delhi_fog_data.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Timestamp', 'Data_Row'])
            writer.writerows(data_to_save)
            
        print(f"Success! Captured {len(data_to_save)} lines at {timestamp}")

    except Exception as e:
        print(f"Scrape Failed at {datetime.now()}: {e}")

if __name__ == "__main__":
    scrape_visibility()