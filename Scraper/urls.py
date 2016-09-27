def make_url(url,driver):
	"""Convert href links to absolute paths."""
	if url.startswith('http'):
		return url
	elif url.startswith('/'):
		base = driver.current_url.split('//')
		return base[0]+'//'+base[1].split('/')[0] + url
	else:
		base = driver.current_url.split('/')
		url2 = '/'.join(filter(lambda x: x!='..',url.split('/')))
		return '/'.join(base[:-1-url.count('..')])+'/'+url2
