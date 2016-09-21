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
		mixed_children = [self.build_node(k) for j in children[self.childkey].values]
		node = get_node(key,context,mixed_children)
		return node

	def get_node(self,key,context,mixed_children=[]):
		node = {
			'name': key,
			'children': mixed_children if len(mixed_children)>8 else None,
			'_children': mixed_children if len(mixed_children)<=8 else None
			}
		node.update(context)
		return node
		
	def dump(self,name):
		with open('../erdmap/erdmap/static/erdmap/%s.json'%name,'w') as f:
        	json.dump(self.sitemap,f)
