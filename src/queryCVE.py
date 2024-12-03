# 向服务器端上传SBOM文件，将返回结果分析并输出

import loadConfig
import requests
import json
def queryCVE(spdxObj,dnfConfigure:loadConfig.dnfcConfigure):
	url=dnfConfigure.querycveURL
	try:
		response = requests.post(url, json=spdxObj)
	except requests.exceptions.ConnectionError as e:
		print("failed to query CVE: Unable to connect: "+url)
		return {}
	except Exception as e:
		print(f'failed to query CVE: {e}')
	if response.status_code == 200:
		return response.json()
	else:
		print(f'failed to query CVE: Request failed with status code {response.status_code}')
		return {}
	
def queryCVECli(args):
	dnfConfigure=loadConfig.loadConfig()
	if dnfConfigure is None:
		print('ERROR: cannot load config file in /etc/dnfC/config.json, please check config file ')
		return False
	if len(args)==0:
		print("usage: dnf queryCVE <spdxfile>")
		return False
	spdxPath=args[0]
	
	with open(spdxPath,"r") as f:
		spdxObj=json.load(f)
	cves=queryCVE(spdxObj,dnfConfigure)
	haveOutput=False
	for projectName,cves in cves.items():
		if len(cves)==0:
			continue
		haveOutput=True
		print("package: "+projectName)
		print(" have cve:")
		for cve in cves:
			print(" "+cve['name']+", score: "+str(cve['score']))
	if haveOutput is False:
		print("All packages have no CVE")
	return False