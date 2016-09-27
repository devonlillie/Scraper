import pandas as pd
import numpy as np
import re
import pickle

from Map import SiteMap

class TeimsSiteMap(SiteMap):

	attr = re.compile('=.*(;|$)')
	user = re.compile('user_id=[a-zA-Z0-9]*;?')
	tables = pd.DataFrame()
	
	def template_nodes(self,children,key,thresh=5):
		"""Given a set of pages, check if any subset of them should be templatized.
		
		Input:
			- children, set of pages who share a parent
			- key, the field being used to match templated pages
			- thresh, minimum number of pages in a template to group up
		Output:
			- template_nodes, a list of template nodes created recursively
			- singles, a pandas DataFrame with pages that weren't templatized
			
		Note:
			- templatized pages share the same script base and the same set of 
			 parameter names, but with different values
			- the link value of a template node is inherited from their parent
			- template nodes can have associate tables
		"""
		if children.empty:
			return [],children
		
		# Strip the actual parameter values from the url, but keep the parameter names
		# from table=SAMPLE;,table=PARAMETER; --> table=;,table=;
		children['stripped'] = children[key].map(lambda x: re.sub(self.attr,'=;',x)).values
		singles = children.groupby('stripped').filter(lambda x: len(x)<=thresh)
		templates = children.groupby('stripped').filter(lambda x: len(x)>thresh)
		
		# If there are no template groups large enough, return empty list of 
		# template_nodes
		if templates.empty:
			return [],singles
		
		template_nodes =[]
		for s in templates['stripped'].drop_duplicates().values:
			v = templates[templates['stripped']==s]
			v0 = v.iloc[0]
			attrnames = filter(lambda y: y,s.split('?')[1].replace('=','').split(';'))
			lbl = '%s(%s)'%(v0[key].split('.')[0].split('/')[-1],','.join(attrnames))
			tempname = '%s: %s(%s)'%(
							v0['section_text'],
							v0[key].split('.')[0],
							','.join(attrnames))
			
			# Define the context of the template node
			temp_context = {'link':children[self.parentkey].iloc[0],'type':'template',
					'tables':[],'num':len(v),'label':lbl}
			
			# Build children nodes recursively
			template_children = [self.build_node(v.loc[k]) for k in v.index]
			template_nodes += [self.get_node(tempname,temp_context,template_children)]
		return template_nodes,singles
	
	def dummy_node(self,key,link):
		"""Handle multiple links to the same page by choosing one main link and 
		create dummy nodes for subsequent links. Add dependency links from a 
		dummy node to the main node."""
		context = {'type':'dummy','main':key,'link':key}
		return context
	
	def group_nodes(self,children,key):
		"""Given a set of pages, check if any subset of them should be grouped 
		sections based on the structure of webpage.
		Input:
			- children, set of pages who share a parent page
			- key, the field being used to match the groups
		Output:
			- group_nodes, a list of group nodes created recursively
			- singles, a pandas DataFrame with pages that weren't grouped
			
		Note:
			- don't insert a group node for groups with 1 node
			- if page has one group, don't insert a group node
			- group nodes inherit link from parent node
			- group nodes don't have associated tables
		"""
		if children.empty:
			return [],children
		
		group_keys = children[key].drop_duplicates().values
		if len(group_keys)<=1:
			return [],children
		
		# Inherit the link from parent
		link = children[self.parentkey].iloc[0]
		singles = children.groupby(key).filter(lambda x: len(x)<=1)
		groups = children.groupby(key).filter(lambda x: len(x)<1)
		
		group_nodes = []
		for g in group_keys:
			nodes = children[children[key]==g]
			if len(nodes)>1:
				group_children = [self.build_node(nodes.loc[k]) for k in nodes.index]
				group_context = {'link':link,'type':'group','label':g,'num':len(nodes),'tables':[]}
				group_nodes += [self.get_node(link+g,group_context,group_children)]
		return group_nodes,singles

	def build_tables(self,key):
		"""For a given key, build list of table nodes that are attached that url.
		
		Note:
			- table nodes do not have children and are not unique with this 
			implementation.
		"""
		tables = self.tables[self.tables['link']==key].drop_duplicates().dropna(how="any")
		if len(tables)==0:
			a = self.tables['link'].str.startswith(key)
			b = self.tables['link'].map(lambda x: key.startswith(x))
			tables = self.tables[a|b].drop_duplicates()
		table_nodes = []
		for i in tables.index:
			table_nodes+=[{'name': tables.loc[i,'table'],
							'appname': tables.loc[i,'application'],
							'group':tables.loc[i,'group'],
							'link':tables.loc[i,'link'],
							'children':[],
							'_children':[]
						}]
		return table_nodes
		

	def build_node(self,parent):
		"""Build a node recursively, creating group nodes, single nodes and templatized
		nodes as appropriate.
	
		Inputs:
			- the key of the node being built

		Outputs:
			- node: nested, json compatible object
			- each node is required to have at basic: name, children and _children
			** the basics for creating a d3 tree
		"""
		key = parent[self.childkey]
		children = self.edges.loc[self.edges[self.parentkey]==key]

		parent_title = children['parent_title'].iloc[0] if not children.empty else ''
		link_text = parent['link_text']
		label = link_text if not (type(link_text) is np.float) else parent_title
		
		context = {'link':key,
				'type':'node',
				'label':label,
				'tables':self.build_tables(key)
				}
			
		## Handle Groups
		#templates,children = templatize_nodes(children)
		next_children=[]
		if not children.empty:
			templates,children = self.template_nodes(children,'link_href',10)
			groups,children = self.group_nodes(children,'section_text')
			node_children = [self.build_node(children.loc[k]) for k in children.index]
			next_children = groups+templates+node_children
		else:
			next_children =[]

		if parent['dummy']:
			context['type']='dummy'
			context['parent']=key
			node = self.get_node(key + ' %s'%parent['count'],context,[])
		else:
			node = self.get_node(key,context,next_children)
		return node

		
	def build_tree(self,root="TEIMS"):
		"""From internal edges object, build a nested representation of the sitemap.
		Inputs:
			- root (optional): label node for root
		Note:
			- if 
		"""
		# Create a field to indicate if a link is internal or external
		self.edges['internal'] = self.edges[self.childkey].str.startswith('http')==False
		self.tables = pd.read_csv('tables.csv')
		# Normalize link urls and table url keys
		self.normalizeKeys()
		self.markDummies()
		
		root_context = {'label':root+' Node','type':'root','link':'#'}
		root_key = self.edges[self.parentkey].iloc[0]
		head_nodes = self.edges[self.edges[self.parentkey]==root_key].fillna(root_key)
		children = [self.build_node(head_nodes.loc[k]) for k in head_nodes.index]
		self.sitemap = self.get_node(root_key,root_context,children)
	
	def markDummies(self):
		self.edges['count'] = self.edges.groupby(['child_url']).cumcount()
		self.edges['dummy'] = self.edges['count']!=0
	
	def normalizeKeys(self):
		self.edges[self.childkey] = self.edges[self.childkey].str.replace('user_id=bates28(;|$)','').str.strip('?')
		self.edges[self.childkey] = self.edges[self.childkey].str.replace('.gov:[0-9]{4}','.gov')
		self.edges[self.parentkey] = self.edges[self.parentkey].str.replace('user_id=bates28(;|$)','').str.strip('?')
		self.edges[self.parentkey] = self.edges[self.parentkey].str.replace('.gov:[0-9]{4}','.gov')
				
