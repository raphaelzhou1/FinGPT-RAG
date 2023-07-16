import requests
from bs4 import BeautifulSoup
from lxml.html import fromstring
from zenrows import ZenRowsClient
import numpy as np
import pandas as pd
import sys

# Grab a set of proxies
# ----------------------------
# def get_proxies():
#     url = 'https://free-proxy-list.net/anonymous-proxy.html'
#
#     response = requests.get(url)
#     parser = fromstring(response.text)
#     proxies = set()
#     for i in parser.xpath('//tbody/tr')[:10]:
#         if i.xpath('.//td[7][contains(text(),"yes")]'):
#             proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
#             proxies.add(proxy)
#     return proxies


# Test proxy
# ----------------------------
# def test_proxy(proxy):
#     try:
#         response = requests.get('https://www.google.com', proxies={'http': proxy, 'https': proxy}, timeout=5)
#         if response.status_code == 200:
#             return True
#     except Exception:
#         pass
#     return False


# Header settings
# ----------------------------
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0',
    'From': 'tianyu_zhou1@brown.edu'
}


# Bloomberg scraper function
# ----------------------------
def scrape_bloomberg(subject, page_number):
    client = ZenRowsClient("6026db40fdbc3db28235753087be6225f047542f")
    params = {"premium_proxy": "true", "proxy_country": "us"}

    full_url = 'https://www.bloomberg.com/search?query=' + subject + '&sort=relevance:asc&startTime=2015-04-01T01:01:01.001Z&' + '&page=' + str(page_number)
    print("Trying url " + full_url)
    # response = requests.get(full_url, headers=headers, proxies=proxies)
    response = client.get(full_url, params=params)
    print("Response code: " + str(response.status_code))
    soup = BeautifulSoup(response.content, 'html.parser')
    links = [a['href'] for a in soup.select('a[class^="headline_"]') if 'href' in a.attrs]
    print("Found " + str(len(links)) + " links", "these are: " + str(links))
    return links



if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Error: Please provide subject title, page_min, and pages_max. \nFor Example: >Bloomberg_extractor.py bitcoin 1 99\n")
        sys.exit(1)

    subject = str(sys.argv[1])
    pages_min = int(sys.argv[2])
    pages_max = int(sys.argv[3])

    completed_page = pages_min - 1
    full = np.array(['link'])

    # proxy_list = list(get_proxies())

    # print("Found " + str(len(proxy_list)) + " proxies")

    # for proxy in proxy_list:
    #     if not test_proxy(proxy):
    #         print('Proxy ' + proxy + ' failed')
    #         continue

    pages = np.arange(completed_page + 1, pages_max + 1, 1)

    # proxies = {
    #     'http': proxy,
    #     'https': proxy,
    # }

    for page in pages:
        # print('Trying Page ' + str(page) + ' using proxy ' + proxy)
        try:
            full = np.append(full, scrape_bloomberg(subject=subject, page_number=page))
            print('Page ' + str(page) + ' completed\n')
            np.savetxt('RESULTS_TMP.csv', full, fmt='%s', delimiter=',')
            completed_page = page
        except Exception as e:
            print(str(e))
            # print('Failed Page ' + str(page) + ' using proxy ' + proxy)
            break

    np.savetxt('results'+ subject + str(pages_max) + '.csv', full, fmt='%s', delimiter=',')
