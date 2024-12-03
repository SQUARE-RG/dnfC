#常用网络下载功能的简单包装

import pycurl
import certifi
import wget
import os
from io import BytesIO
from urllib.parse import urlencode
import sys
curlCache={}
def sendCurl(URL:str,params:dict,additional:list=[])->dict:
	buffer = BytesIO()
	c = pycurl.Curl()
	URL=URL+'?'+urlencode(params)
	for ad in additional:
		URL=URL+"&"+ad
	if URL in curlCache:
		return curlCache[URL]
	c.setopt(c.URL,URL)
	c.setopt(c.HTTPGET,1)
	c.setopt(c.WRITEDATA,buffer)
	c.setopt(c.CAINFO,certifi.where())
	c.perform()
	c.close()
	body = buffer.getvalue().decode('iso-8859-1')
	curlCache[URL]=body
	return body
def bar_progress(current, total, width=80):
	pass
	#progress_message = "Downloading: %d%% [%d / %d] bytes" % (current / total * 100, current, total)
	# Don't use print() as it will print in new line every time.
	#sys.stdout.write("\r" + progress_message)
	#sys.stdout.flush()
def downloadFile(url,filePath,fileName)->str:
	if not os.path.exists(filePath):
		os.makedirs(filePath)
	filePath=os.path.join(filePath,fileName)
	if not os.path.isfile(filePath):
		wget.download(url,filePath,bar=bar_progress)
	return filePath