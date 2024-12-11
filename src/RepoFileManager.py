import os
import xml.dom.minidom
import gzip
import pyzstd
import PackageInfo
import SpecificPackage
from collections import defaultdict
def splitVersionRelease(version_release):
	version_release=version_release.strip().rsplit('-',1)
	version=version_release[0]
	if len(version_release)>1:
		release=version_release[1]
	else:
		release=None
	return version,release
def parseRPMItemInfo(data):
    res=[]
    for item in data:
        item=item.strip()
        name=None
        flags=None
        version=None
        release=None
        parse=item.split(' = ')
        if len(parse)>1:
            name=parse[0]
            flags="EQ"
            version,release=splitVersionRelease(parse[1])
        parse=item.split(' <= ')
        if len(parse)>1:
            name=parse[0]
            flags="LE"
            p2=parse[1].split('-')
            version,release=splitVersionRelease(parse[1])
        parse=item.split(' < ')
        if len(parse)>1:
            name=parse[0]
            flags="LT"
            p2=parse[1].split('-')
            version,release=splitVersionRelease(parse[1])
        parse=item.split(' >= ')
        if len(parse)>1:
            name=parse[0]
            flags="GE"
            p2=parse[1].split('-')
            version,release=splitVersionRelease(parse[1])
        parse=item.split(' > ')
        if len(parse)>1:
            name=parse[0]
            flags="GT"
            p2=parse[1].split('-')
            version,release=splitVersionRelease(parse[1])
        if name is None:
            name=item
        #log.debug(" "+name)
        res.append(SpecificPackage.PackageEntry(name,flags,version,release))
    return res
def parseEntry(node:xml.dom.minidom.Element,fullName:str,type:str)->list:
	#fullName just for debug info, can be empty string
	nodelist=node.childNodes
	res=[]
	for subnode in nodelist:
		if subnode.nodeType==xml.dom.Node.TEXT_NODE:
			continue
		name=subnode.getAttribute('name').strip()
		flags=None
		if subnode.hasAttribute('flags'):
			flags=subnode.getAttribute('flags').strip()
		version=None
		if subnode.hasAttribute('ver'):
			version=subnode.getAttribute('ver').strip()
		else:
			# if flags is not None:
			# 	log.warning(fullName+" have a package have flags but no version")
			pass
		release=None
		if subnode.hasAttribute('rel'):
			release=subnode.getAttribute('rel').strip().split('.')[0]
		res.append(SpecificPackage.PackageEntry(name,flags,version,release))
	return res
def sub2dict(node):
    subDict=defaultdict(SpecificPackage.defaultNoneList)
    nodelist=node.childNodes
    for subnode in nodelist:
        name=subnode.nodeName
        subDict[name].append(subnode)
    return subDict
def parseRPMPackage(node:xml.dom.minidom.Element,osType,dist,repoURL)->SpecificPackage.SpecificPackage:
	childsNode=sub2dict(node)
	packageFormat=childsNode['format'][0]
	formatChilds=sub2dict(packageFormat)
	sourceTag=formatChilds['rpm:sourcerpm'][0]
	if sourceTag.firstChild is None:
		return None
	fullName=childsNode['name'][0].firstChild.nodeValue
	versionNode=childsNode['version'][0]
	version=versionNode.getAttribute('ver').strip()
	sourcerpm=sourceTag.firstChild.nodeValue
	name=sourcerpm.split('-'+version)[0]
	release=versionNode.getAttribute('rel').strip()
	arch=childsNode['arch'][0].firstChild.nodeValue
	provides=[]
	res=formatChilds['rpm:provides']
	if len(res)!=0:
		provides=parseEntry(res[0],fullName,'provides')
	requires=[]
	res=formatChilds['rpm:requires']
	if len(res)!=0:
		requires=parseEntry(res[0],fullName,'requires')
	res=formatChilds['rpm:recommends']
	if len(res)!=0:
		requires.extend(parseEntry(res[0],fullName,'requires'))
	filePath=childsNode['location'][0].getAttribute('href').strip()
	# if fullName.endswith("-fonts"):
	# 	print(repoURL)
	# 	print(fullName)
	packageInfo=PackageInfo.PackageInfo(osType,dist,name,version,release,arch)
	return SpecificPackage.SpecificPackage(packageInfo,fullName,provides,requires,arch,repoURL=repoURL,fileName=filePath)

def parseRPMFiles(repodata,osType,dist,repoURL):
	#entryMap=EntryMap()
	res=[]
	doc=xml.dom.minidom.parseString(repodata)
	root=doc.documentElement
	nodelist=root.childNodes
	for subnode in nodelist:
		if subnode.nodeType==xml.dom.Node.TEXT_NODE:
			continue
		package=parseRPMPackage(subnode,osType,dist,repoURL)
		if package is not None:
			res.append(package)
	return res


class RepoFileManager:
	def __init__(self,repoPath,osType,dist,repoURL):
		self.repoPath=repoPath
		self.packageMap=SpecificPackage.defaultdict(SpecificPackage.defaultNoneList)
		if repoPath.endswith('.gz'):
			with gzip.open(repoPath,"rb") as f:
				data=f.read()
		elif repoPath.endswith('.zst'):
			with open(repoPath, "rb") as f:
				data = f.read()
				data = pyzstd.decompress(data)
		else:
			print("warning: cannot extract file "+repoPath)
		self.packages=parseRPMFiles(data,osType,dist,repoURL)
		for package in self.packages:
			self.packageMap[package.fullName].append(package)
	def queryPackage(self,name,version,release,arch):
		#print("\nquery:")
		#print(name,version,release,arch)
		e=SpecificPackage.PackageEntry(name,"EQ",version,release)
		if name in self.packageMap:
			for specificPackage in self.packageMap[name]:
				#print(specificPackage.packageInfo.version,specificPackage.packageInfo.release,specificPackage.packageInfo.arch)
				if SpecificPackage.compareEntry(specificPackage.getSelfEntry(),e)==0:
					if specificPackage.packageInfo.arch==arch:
							return specificPackage
			return None
	def getAllPackages(self):
		return self.packages
		
	