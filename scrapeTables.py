from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd

chromeoptions = webdriver.ChromeOptions()
chromeoptions.binary_location = "/Applications/Google Chrome 52.0.2743.116.app/Contents/MacOS/Google Chrome"

driver = webdriver.Chrome('/Users/bates28/Downloads/chromedriver',chrome_options=chromeoptions)

driver.get('https://myconfluence.llnl.gov/display/ERDW/Level+2+REST+API+Abstractions')
c = raw_input('Signed in?')
soup = BeautifulSoup(driver.page_source,'html.parser')
tables = soup.findAll('table',{'class':'confluenceTable'})
strify = lambda s: ''.join([c for c in s if ord(c)<128])
alltables =[]
for table in tables:
	rows = [tr for tr in table.findAll('tr')]
	headers = rows[0:2]
	columns = [th.text for th in headers[1]][1:]
	for row in rows[2:]:
		application = row.th.text
		for a in row.findAll('a'):
			if not a.has_attr('href'):
				continue
			link = a['href']
			for (i,td) in enumerate(row.findAll('td')):
				if strify(td.text)!='':
					column = columns[i]
					for t in td.text.replace(', ',',').split(','):
						alltables +=[{
							'table':t,
							'group':column,
							'application':application,
							'link':link
						}]	
	

	
results = pd.DataFrame(alltables)
results['link'] = results['link'].str.replace('user_id=dubil1(;|$)','').str.strip('?')
results['link'] = results['link'].str.replace('.gov:[0-9]{4}','.gov')
results['link'] = results['link'].str.replace('teimsdev','teims')

results.to_csv('tables.csv')

