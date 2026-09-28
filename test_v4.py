import os, tempfile
from bs4 import BeautifulSoup
import config, scraper, formatter, exporter

BASE='https://test.local/'
HTML='''<html><head><title>Test Shop</title></head><body>
<h1>Widget</h1><p>This is a sufficiently long paragraph for general extraction.</p>
<span class="price">$19.99</span><span class="stock">In Stock</span>
<img src="/a.jpg"><img src="/b.jpg">
<a href="mailto:test@example.com">test@example.com</a>
<a href="https://example.org">Link</a><a href="https://instagram.com/test">Social</a>
<table><tr><th>Name</th><th>Price</th></tr><tr><td>A</td><td>10</td></tr></table>
</body></html>'''

soup=BeautifulSoup(HTML,'html.parser')
assert scraper.scrape_general_content(soup, BASE)['Heading']=='Widget'
p=scraper.scrape_product_details(soup, BASE)
assert p['Price']=='$19.99' and p['Availability']=='In Stock' and p['Image URLs'].count('http')==2
c=scraper.scrape_contacts_and_links(soup, BASE)
assert 'test@example.com' in c['Emails Found'] and 'https://example.org' in c['Links Found']
assert len(scraper.scrape_tables(soup, BASE))==1
assert scraper.scrape_auto(soup, BASE)['HTML Tables Found']==1

# formatter handles dict and list
assert formatter.clean_extracted_data({'A':'  x   y '})['A']=='x y'
assert formatter.clean_extracted_data([{'A':' x '}])[0]['A']=='x'

# exporter handles dict + list results
old=config.OUTPUT_FILENAME
fd,path=tempfile.mkstemp(suffix='.xlsx'); os.close(fd); config.OUTPUT_FILENAME=path
exporter.export_to_structured_excel([p, scraper.scrape_tables(soup, BASE)])
assert os.path.getsize(path)>0
os.remove(path); config.OUTPUT_FILENAME=old

# pagination: two pages, next href, no duplicate loop
P1='''<html><body><h1>Page One</h1><p>Long enough paragraph for page one content.</p><a rel="next" href="/page2">Next</a></body></html>'''
P2='''<html><body><h1>Page Two</h1><p>Long enough paragraph for page two content.</p></body></html>'''
original_fetch=scraper.fetch_page
original_mode=config.SCRAPE_MODE
original_pag=config.ENABLE_PAGINATION
original_max=config.MAX_PAGES
pages={BASE:(BeautifulSoup(P1,'html.parser'),BASE), 'https://test.local/page2':(BeautifulSoup(P2,'html.parser'),'https://test.local/page2')}
scraper.fetch_page=lambda u: pages[u]
config.SCRAPE_MODE='GENERAL'; config.ENABLE_PAGINATION=True; config.MAX_PAGES=5
result=scraper.scrape_single_url(BASE)
assert isinstance(result,list) and len(result)==2 and result[0]['Page']==1 and result[1]['Page']==2
scraper.fetch_page=original_fetch; config.SCRAPE_MODE=original_mode; config.ENABLE_PAGINATION=original_pag; config.MAX_PAGES=original_max
print('V4 LOCAL COMPREHENSIVE TESTS: PASS')
print('GENERAL: PASS')
print('PRODUCT: PASS')
print('CONTACTS: PASS')
print('TABLE: PASS')
print('AUTO: PASS')
print('FORMATTER: PASS')
print('EXCEL EXPORT: PASS')
print('PAGINATION LOGIC: PASS')
