from Scrape import Scraper
from bs4 import BeautifulSoup
from Queue import Queue
from selenium import webdriver
from pprint import pprint

import pandas as pd
import re
import pickle
import time

class TeimsScraper(Scraper.Scraper):
	def scrape_page(self,page):
		"""Scrape a page for all relevant links, and add links to the visit queue.
		Input:
			- page: a dictionary that defines a page to visit
		Output:
			- result message: 'Skipped','Taurus','Visited'
		"""
		# If url points outside of times, exit out of page
		# else, visit the page
		if self.is_internal(self.get_url(page)):
			self.driver.get(self.get_url(page))
			print(self.get_url(page))
		else:
			return 'External page'
		
		# If page has been visited don't push any links to the visit queue
		if self.visited.has_key(self.driver.current_url):
			return 'Skipped'
		
		soup = BeautifulSoup(self.driver.page_source,'html.parser')
		
		# Templatized pages put the unique page content in a div[class=pageContent]
		# If there is none, the class is a Taurus gen page
		pageContent =  soup.find('div',{'id':'pageContent'})
		
		# Change link extraction based on page generation (i.e. Taurus vs. Templatized)
		if not pageContent:
			gen = 'Taurus'
			pageTitle = soup.find('p',{'class':'page_title'})
			return 'Taurus'
		else:
			gen = 'Templatized'
			pageTitle = soup.find('div',{'id':'pageTitle'}).text if soup.find('div',{'id':'pageTitle'}) else ''
			links = self.get_links(pageContent)
			
		page_context = {'parent_title':pageTitle,'depth':page['depth']+1,'gen':gen}
		
		# For each link:
		# 1) Define a node (i.e. page definition) with given page_context
		# 2) add page definition to the edges list 
		# 3) Push the page to the visit queue
		edges = []
		for link in links:
			node = self.define_page(link,page_context)
			edges+=[node]
			self.push_page(node)
			
		new_edges = pd.DataFrame(edges)
		self.site = self.site.append(new_edges)
		return 'Visited'
	
	def get_links(self,soup):
		"""Given html soup, extract and return <a> elements and their parent elements."""
		# Templatized pages have panels to separate groups of links
		panels = [h.parent for h in soup.findAll("div",{"class":"contentHeader"})]
		rows = [td for p in panels for td in p.findAll('td') if td and p]
		pars = [p.span.text if p.span else '' for p in panels for td in p.findAll('td') if td and p]

		# For each row, 
		# 1) fetch all link elements <a>
		# 2) if the link is valid, extract info about the link
		# 3) return all valid link definitions
		singlelink=[]
		for i in range(len(rows)):
			rowlinks = [a for a in rows[i].findAll('a') if a and a.text and a.has_attr('href')]
			for a in rowlinks:
				if self.valid_url(a):
					singlelink+=[{
						'link':a,
						'link_href': a['href'],
						'link_text': a.text,
						'section_text':pars[i],
						'has_multiple_links':len(rowlinks)>1
						}]
		return singlelink

	def valid_url(self,url):
		"""Return whether a url is valid to scrape."""
		if 'javascript' in url['href']:
			return False
		if '.xls' in url['href']:
			return False
		return True
		
	def is_internal(self,url):
		"""Return whether a page points to a teims page."""
		if url.startswith('https://teims'):
			return True
		return False
		
	def save(self,fn):
		temp= self.site.fillna('')
		strify = lambda x: ''.join([c for c in x if ord(c)<128])
		temp['link_text'] = temp['link_text'].map(lambda x: strify(x))
		temp['parent_title'] = temp['parent_title'].map(lambda x: strify(x))
		temp['section_text'] = temp['section_text'].map(lambda x: strify(x))
		temp.to_csv(fn)
		
		
		
