import json
import pandas as pd
import re
import pickle


class SiteMap:

	edges = pd.DataFrame()
	log={}
	sitemap = {}
	
	def __init__(self,parent="parent_url",child="child_url"):
		self.parentkey = parent
		self.childkey = child

	def load_site(sitename,logname=None,parentkey=None,childkey=None):
		""" Load a specific site with the relevant edges and the key names."""
		with open(sitename,'r') as f:
			self.edges = pickle.load(f)
			
		if logname:
			with open(logname,'r') as f:
				self.log = pickle.load(f)
		
		if parentkey:
			self.parentkey = parentkey
		if childkey:
			self.childkey = childkey
	
	def load_data(self,site,parentkey=None,childkey=None):
		self.edges = site
		if parentkey:
			self.parentkey = parentkey
		if childkey:
			self.childkey = childkey

	def build_node(self,key):
		"""Build a node recursively, creating group nodes, single nodes and templatized
		nodes as appropriate.
	
		Inputs:
			- the key of the node being built

		Outputs:
			- node: nested, json compatible object, that contains the entire sitemap tree
			- each node is required to have at basic: name, children and _children
			** the basics for creating a d3 tree
		"""
		children = self.edges.loc[self.edges[self.parentkey]==key]
		parent = self.edges.loc[self.edges[self.childkey]==key]
		context = {'link':key}
		mixed_children = [self.build_node(k) for k in children[self.childkey].values]
		node = self.get_node(key,context,mixed_children)
		return node

	def get_node(self,key,context,mixed_children=[],hide=8):
		n = len(mixed_children)
		node = {
			'name': key,
			'children': mixed_children if (n>0) and (n<=hide) else [],
			'_children': mixed_children if (n>hide)  else []
			}
		node.update(context)
		return node
		
	def build_tree(self):
		root_key = self.edges[self.parentkey].iloc[0]
		root_context = {'link':root_key}
		head_nodes = self.edges[self.edges[self.parentkey]==root_key]
		children = [self.build_node(k) for k in head_nodes[self.childkey].values]
		self.sitemap = self.get_node(root_key,root_context,children)
	
	def dump(self,name):
		with open('../erdmap/erdmap/static/erdmap/%s.json'%name,'w') as f:
			json.dump(self.sitemap,f)
		
	
