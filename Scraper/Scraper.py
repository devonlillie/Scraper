from bs4 import BeautifulSoup
from Queue import Queue
from selenium import webdriver
from pprint import pprint
import pandas as pd
import re
import pickle
import time

from Scrape.urls import make_url

class Scraper:
	visited = {}
	to_visit = Queue()
	site = pd.DataFrame()
	
	def __init__(self,chrome_driver,chrome_path,name='ROOT',max_depth=2,max_length=100
				,parent="parent_url",child="child_url"):
		"""Set up scraper by designating driver specs, max_depth, max)"""
		self.create_driver(chrome_driver,chrome_path)
		self.name = name
		self.depth = max_depth
		self.length = max_length
		self.parentkey = parent
		self.childkey = child
		
	def create_driver(self,driverpath,binarypath):
		"""Initialize webdriver to machine specific paths."""
		chromeoptions = webdriver.ChromeOptions()
		chromeoptions.binary_location = binarypath
		self.driver = webdriver.Chrome(driverpath,chrome_options=chromeoptions)
	
	def push_page(self,page):
		"""Push a page definition into the to_visit queue."""
		if page['depth'] <= self.depth:
			self.to_visit.put_nowait(page)
	
	def get_links(self,soup):
		"""Given html soup, extract and return <a> elements and their parent elements."""
		possible_links = [link for link in soup.findAll('a') if link.has_attr('href')]
		return possible_links
		
	def define_page(self,link,context):
		"""Given a dictionary, that contains a link_href value and other context
		return a page definition."""
		test = link.copy()
		test.update(context)
		test.update({self.childkey: make_url(link['link_href'],self.driver)})
		test.update({self.parentkey: self.driver.current_url})
		return test
				
	def get_url(self,page):
		"""Return absolute url path froma  page definition."""
		return page[self.childkey]

	
	def handle_exception(self,driver):
		""" Handle alert exceptions by accepting them."""
		try:
			alert = driver.switch_to_alert()
			alert.accept()
			time.sleep(0.5)
			return True
			
		except Exception:
			return False	
			
	def scrape_page(self,page):
		self.driver.get(self.get_url(page))
		print(self.get_url(page))
		
		if self.visited.has_key(self.driver.current_url):
			return 'Skipped'
		
		soup = BeautifulSoup(self.driver.page_source,'html.parser')
		pageTitle = soup.title.text if (soup.title and soup.title.text) else ''
		links = self.get_links(soup)
		
		page_context = {'parent_title':pageTitle,'depth':page['depth']+1}
		
		edges = []
		for link in links:
			node = self.define_page({'link':link},page_context)
			edges+=[node]
			self.push_page(node)
		
		new_edges = pd.DataFrame(edges)
		self.site = self.site.append(new_edges)
		return 'Visited'

	def scrape(self,url,name='Home', parent='ROOT',root_context={}):
		firstnode = self.root(url,parent,name)
		firstnode.update(root_context)	
		self.site = self.site.append(pd.DataFrame([firstnode]))
		self.to_visit.put(firstnode)
		self.driver.get(self.get_url(firstnode))
		signin = raw_input('Sign in?')
				
		while self.to_visit.empty()==False:
			new_page = self.to_visit.get()
			try:
				message = self.scrape_page(new_page)
				self.visited[self.driver.current_url] = message
			except Exception as e:
				count=0
				while self.handle_exception(self.driver) and count<5:
					count+=1
				pprint(e)
				self.visited[self.driver.current_url] = 'Error'
			self.to_visit.task_done()
		self.site.index = range(len(self.site))
		
	def root(self,url,parent,name):
		return {  
			self.childkey:url,
			self.parentkey:parent,
			'link_text':name,
			'parent_name':parent,
			'parent_title':parent,
			'depth':0
			}
		
	def save(self,fn):
		with open(fn,'w') as f:
			pickle.dump(self.site,f)
			
	def __str__(self):
		return self.site['child_name'].iloc[0]
		
	def __unicode__(self):
		return self.site['child_name'].iloc[0]
		
		
		
		
		
		
		
