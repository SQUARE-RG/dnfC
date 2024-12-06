#对本地二进制包进行分析

import os
import SourcesListManager
import RepoFileManager
import PackageInfo
from subprocess import PIPE, Popen
import SpecificPackage
import PackageInfo
import normalize
import subprocess
import osInfo
import scanSrc
import shutil
from spdx import spdxmain

def parseRPMInfo(data):
	rpmhdr={}
	for item in data:
		pair=item.split(":",1)
		if len(pair)==2:
			pair[0]=pair[0].strip()
			pair[1]=pair[1].strip()
			rpmhdr[pair[0]]=pair[1]
	fullName=rpmhdr['Name']
	version=rpmhdr['Version']
	release=rpmhdr['Release']
	srcrpmformat="-"+version+"-"+release+".src.rpm"
	name=rpmhdr['Source RPM'][:-len(srcrpmformat)]
	return{"name":name,
		"fullName":fullName,
		"version":version,
		"release":release}
#		"arch":rpmhdr['Architecture']}
def parseRequires(PackageName)->list:
	p = Popen("/usr/bin/rpm -qpR '"+PackageName+"'", shell=True, stdout=PIPE, stderr=PIPE)
	stdout, stderr = p.communicate()
	data=stdout.decode().split('\n')
	return RepoFileManager.parseRPMItemInfo(data)
def parseProvides(PackageName)->list:
	p = Popen("/usr/bin/rpm -qpP '"+PackageName+"'", shell=True, stdout=PIPE, stderr=PIPE)
	stdout, stderr = p.communicate()
	data=stdout.decode().split('\n')
	return RepoFileManager.parseRPMItemInfo(data)
def querypackageInfo(filePaths):
	res=[]
	for filePath in filePaths:
		if not os.path.isfile(filePath):
			print("cannot open file: "+filePath)
			return None
		if not os.path.exists("/tmp/aptC/packages"):
			os.makedirs("/tmp/aptC/packages")
		filePath=shutil.copy(filePath,"/tmp/aptC/packages")
		p = subprocess.Popen(f"/usr/bin/rpm -qpi '{filePath}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = p.communicate()
		rpmInfo=parseRPMInfo(stdout.decode().split('\n'))

		requires=parseRequires(filePath)
		provides=parseProvides(filePath)
		
		p=PackageInfo.PackageInfo(osInfo.OSName,osInfo.OSDist,rpmInfo['name'],rpmInfo['version'],rpmInfo['release'],osInfo.arch)
		package=SpecificPackage.SpecificPackage(p,rpmInfo['fullName'],provides,requires,osInfo.arch,"willInstalled",fileName=filePath)
		
		res.append(package)
	return res
	
def scanBin(args):
	binFiles=[]
	genSpdx=False
	spdxPath='.'
	genCyclonedx=False
	cyclonedxPath='.'
	for option in args:
		if option.startswith('--genspdx='):
			genSpdx=True
			spdxPath=option.split('=',1)[1]
		elif option.startswith('--gencyclonedx='):
			genCyclonedx=True
			cyclonedxPath=option.split('=',1)[1]
		elif option=="scansrc":
			continue
		else:
			binFiles.append(option)
	if genSpdx is False and genCyclonedx is False:
		genSpdx=True
	
	packages=querypackageInfo(binFiles)

	sourcesListManager=SourcesListManager.SourcesListManager()
	repoPackages=sourcesListManager.getAllPackages()
	repoPackages.extend(scanSrc.setInstalledPackagesStatus(sourcesListManager))
	entryMap=SpecificPackage.EntryMap()
	skipPackages=set()
	for package in packages:
		package.registerProvides(entryMap)
		skipPackages.add(package.fullName)
	for package in repoPackages:
		if package.fullName in skipPackages:
			continue
		package.registerProvides(entryMap)

	
	for package in packages:
		SpecificPackage.getDependsPrepare(entryMap,package)
	for package in packages:
		depset=SpecificPackage.getDepends(entryMap,package,set())
		depends=dict()
		for p in depset:
			depends[p.packageInfo.name+'@'+p.packageInfo.version]=p.packageInfo.dumpAsDict()
		dependsList=list(depends.values())
		if genSpdx is True:
			spdxmain.spdxmain(normalize.normalReplace(package.fullName),package.fileName,dependsList,'spdx',spdxPath)
		if genCyclonedx is True:
			spdxmain.spdxmain(normalize.normalReplace(package.fullName),package.fileName,dependsList,'cyclonedx',cyclonedxPath)
		
		print("generate SBOM for "+package.fullName)
	return 0
