#对本地源码包进行分析

import os
import SourcesListManager
import RepoFileManager
import PackageInfo
from subprocess import PIPE, Popen
import SpecificPackage
import PackageInfo
import normalize
import shutil
import requests
import loadConfig
import osInfo
import io
from spdx.srcmain import srcmain
DIR = os.path.split(os.path.abspath(__file__))[0]

def postFile(file,dnfConfigure:loadConfig.dnfcConfigure):
	try:
		files = {'file': open(file, 'rb')}
		response = requests.post(dnfConfigure.postfileURL,files=files)
	except requests.exceptions.ConnectionError as e:
		print("failed to upload file: Unable to connect: "+dnfConfigure.postfileURL)
		return None
	except Exception as e:
		print(f'failed to upload file: {e}')
		return None
	if response.status_code == 200:
		data=response.json()
		if data['error']==0:
			return data['token']
		else:
			print("failed to upload file: failinfo: "+data['errorMessage'])
			return None
	else:
		print(f'failed to upload file: Request failed with status code {response.status_code}')
		return None
	
def queryBuildInfo(srcFile,osType,osDist,arch,dnfConfigure:loadConfig.dnfcConfigure):
	src1token=postFile(srcFile,dnfConfigure)
	if src1token is None:
		return None
	try:
		data={"srcFile":src1token,"osType":osType,"osDist":osDist,"arch":arch}
		print("waiting build from server... It may take some time.")
		response = requests.post(dnfConfigure.querybuildinfoURL, json=data)
	except requests.exceptions.ConnectionError as e:
		print("failed to query buildInfo: Unable to connect: "+dnfConfigure.querybuildinfoURL)
		return None
	except Exception as e:
		print(f'failed to query buildInfo: {e}')
	if response.status_code == 200:
		data=response.json()
		if data['error']==0:
			return data['buildinfo']
		else:
			print("failed to query package info: failinfo: "+data['errorMessage'])
			return None
	else:
		print(f'failed to query buildInfo: Request failed with status code {response.status_code}')
		return None


def getSrcPackageInfo(srcPath):
	dnfConfigure=loadConfig.loadConfig()
	if dnfConfigure is None:
		print('ERROR: cannot load config file in /etc/dnfC/config.json, please check config file ')
		return None
	buildInfo=queryBuildInfo(srcPath,osInfo.OSName,osInfo.OSDist,osInfo.arch,dnfConfigure)
	if buildInfo is None:
		return None
	packages=RepoFileManager.parseRPMFiles(buildInfo,osInfo.OSName,osInfo.OSDist,None)
	for p in packages:
		p.status="willInstalled"
	return packages
def readStr(f):
	res=""
	while True:
		c=f.read(1)
		if not c:
			break
		if c==' ' or c=='\n':
			if res=="":
				continue
			else:
				break
		res=res+c
	return res
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
def setInstalledPackagesStatus(sourcesListManager:SourcesListManager.SourcesListManager):
	res=list()
	p = Popen("/usr/bin/dnf list --installed", shell=True, stdout=PIPE, stderr=PIPE)
	stdout, stderr = p.communicate()
	f=io.StringIO(stdout.decode())
	while readStr(f)!="Installed":
		#ignore Waiting for process with pid xxx to finish.
		pass
	readStr(f)		#ignore [Installed,Packages]
	while True:
		name_arch=readStr(f)
		if name_arch=="":
			break
		fullName=name_arch.split('.')[0]
		arch=name_arch.split('.')[-1]
		if len(name_arch.split('.'))!=2:
			raise Exception("unexpected format: "+name_arch)
		version_release=readStr(f)
		version,release=RepoFileManager.splitVersionRelease(version_release)
		dist=release.rsplit('.',1)[1]
		channel=readStr(f)[1:]
		#if channel=="system":
		#	continue
		#print(osType,dist,name,version,release)
		package=sourcesListManager.getSpecificPackage(fullName,channel,version,release,arch)
		if package is not None:
			package.status="installed"
		else:
			packageInfo=PackageInfo.PackageInfo(osInfo.OSName,osInfo.OSDist,fullName,version,release,arch)
			provides=parseProvides(fullName)
			requires=parseRequires(fullName)
			res.append(SpecificPackage.SpecificPackage(packageInfo,fullName,provides,requires,arch,"installed"))
	return res

def scanSrc(args):
	srcFile=None
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
			srcFile=option
	if genSpdx is False and genCyclonedx is False:
		genSpdx=True
	srcPath=os.path.join("/tmp/dnfC/",normalize.normalReplace(os.path.abspath(srcFile)))
	if not os.path.isdir("/tmp/dnfC/"):
		os.makedirs("/tmp/dnfC/")
	shutil.copyfile(srcFile,srcPath)
	packagesInSrc=getSrcPackageInfo(srcPath)
	if packagesInSrc is None:
		return 1
	sourcesListManager=SourcesListManager.SourcesListManager()
	repoPackages=sourcesListManager.getAllPackages()
	repoPackages.extend(setInstalledPackagesStatus(sourcesListManager))
	entryMap=SpecificPackage.EntryMap()
	skipPackages=set()
	for package in packagesInSrc:
		package.registerProvides(entryMap)
		skipPackages.add(package.fullName)
	for package in repoPackages:
		if package.fullName in skipPackages:
			continue
		package.registerProvides(entryMap)

	
	for package in packagesInSrc:
		SpecificPackage.getDependsPrepare(entryMap,package)
	for package in packagesInSrc:
		depset=SpecificPackage.getDepends(entryMap,package,set())
		depends=dict()
		for p in depset:
			depends[p.packageInfo.name+'@'+p.packageInfo.version]=p.packageInfo.dumpAsDict()
		dependsList=list(depends.values())
		if genSpdx is True:
			srcmain(normalize.normalReplace(package.fullName),srcPath,dependsList,'spdx',spdxPath)
		if genCyclonedx is True:
			srcmain(normalize.normalReplace(package.fullName),srcPath,dependsList,'cyclonedx',cyclonedxPath)
		print("generate SBOM for "+package.fullName)
	return 0
