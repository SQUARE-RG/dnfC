#读取spdx格式的SBOM信息，仅用于scanDeb模块分析外部依赖的内部依赖后，筛查是否分析出有效的内部依赖（若无有效内部依赖则跳过查询CVE步骤）

import os
import sys
from loguru import logger as log
DIR=os.path.split(os.path.abspath(__file__))[0]
sys.path.insert(0,os.path.join(DIR,'..','src'))
import PackageInfo
import normalize
#def loadSpdxFile(fileName):
#	res=[]
#	with open(fileName,"r") as f:
#		spdxObj=json.load(f)
#		packages=spdxObj['packages']
#		for package in packages:
#			packageType=package['description']
#			if packageType=='Deb' or packageType=='Rpm':
#				purlStr=package['externalRefs'][0]['referenceLocator']
#				res.append(PackageInfo.loadPurl(purlStr))
#	return res
def parseSpdxObj(spdxObj,duplicate_removal=True):
	res=[]
	known_names=set()
	packages=spdxObj['packages']
	for package in packages:
		packageType=package['description']
		if 'sourceInfo' in package and package['sourceInfo']=="External Dependency" and (packageType.lower()=='deb' or packageType.lower()=='rpm'):
			packageinfo=None
			for externalRefs in package['externalRefs']:
				if externalRefs['referenceCategory']!='PACKAGE_MANAGER':
					continue
				purlStr=package['externalRefs'][0]['referenceLocator']
				purlStr=normalize.reNormalReplace(purlStr)
				packageinfo=PackageInfo.loadPurl(purlStr)
				if 'comment' in package:
					packageinfo.gitLink=package['comment']
			if packageinfo is not None:
				if duplicate_removal is True:
					name=packageinfo.name
					if name in known_names:
						continue
					known_names.add(name)
					res.append(packageinfo)
				else:
					res.append(packageinfo)
			else:
				log.warning('ERROR:spdxReader:cannot find PACKAGE_MANAGER infomation in externalRefs')
		else:
			spdxid=package['SPDXID']
			if spdxid.startswith("SPDXRef-DocumentRoot-Directory"):
				continue
			name=package['name']
			version=package['versionInfo']
			packageinfo=PackageInfo.PackageInfo("maven","",name,version,None,None)
			if duplicate_removal is True:
				name=packageinfo.name
				if name in known_names:
					continue
				known_names.add(name)
				res.append(packageinfo)
			else:
				res.append(packageinfo)
					
			res.append(packageinfo)
	return res


#pl=loadSpdxFile("my_spdx_document.spdx.json")
#print(cveSolver.solve(pl))