# SpecificPackage对象表示一个软件包，其中包含了元数据信息
# PackageEntry对象表示一个“条目”，在元数据中，软件包会声明所“依赖”的条目或“提供”的条目。若软件包A依赖于软件包B，则要求软件包A依赖的条目可以和软件包B提供的条目匹配
# 条目包含名称和可选的版本约束信息
# 一个软件包无需声明，会默认提供一个以软件包为名，约束条件为等于软件包版本的条目。且此条目在匹配时优先级更高。
# compareEntry函数用于判断条目版本号的大小关系
# EntryMap是条目的索引，当已知一些软件包的元数据，希望对上述软件包分析依赖关系时，应首先生成一个EntryMap，将所有参与分析的软件包“注册”到EntryMap，从而可以通过条目名查找到所有提供该条目名称的软件包
# EntryMap的queryRequires函数用于根据给定的依赖信息确定合适的软件包
# SpecificPackage的findRequires函数依赖于EntryMap的queryRequires函数，依靠一定的策略查找该软件包依赖的所有软件包
# getDependes_dfs将对SpecificPackage对象调用findRequires函数，确定一个软件包依赖的软件包后，递归地确定依赖软件包的软件包
# getDependsPrepare和getDepends是封装好的函数，用于被外部调用，提供尽可能简洁的功能

# 综上，假设希望安装一些软件包(以下用packages表示，其为一个列表，列表中的元素是SpecificPackage对象)
# 目前已知仓库中的软件包(以下用repoPackages表示，结构同上)
# 基于仓库软件包的信息，分析出希望安装的软件包的外部依赖的参考代码如下
# entryMap=SpecificPackage.EntryMap()
# 将参与分析的软件包注册到entryMap
# skipPackages=dict()
# for package in packages:
# 	package.status="willInstalled"
# 	package.registerProvides(entryMap)
# 	skipPackages[package.fullName]=package
# for package in repoPackages:
# 	if package.fullName in skipPackages: #若已指定安装此软件包，则使用packages列表中的信息，而非仓库中的信息
# 		continue
# 	package.registerProvides(entryMap)
# 
# 确定外部依赖时，安装的多个软件包会互相影响。需要分析两遍，先对所有参与安装的软件包执行一次getDependsPrepare
# for package in packages:
# 	SpecificPackage.getDependsPrepare(entryMap,package)
# 最后逐个确认外部依赖
# for package in packages:
# 	depset=SpecificPackage.getDepends(entryMap,package,set())
# 	depset即为该软件包的外部依赖列表(set形式)

import sys
import os
import traceback
DIR = os.path.split(os.path.abspath(__file__))[0]
sys.path.append(os.path.join(DIR,"lib"))
from collections import defaultdict
from loguru import logger as log
from PackageInfo import PackageInfo
def splitDigitAndChar(rawstr)->list:
	res=[]
	if len(rawstr)==0:
		return res
	r=rawstr[0]
	if r.isdigit() is True:
		t="digit"
	else:
		t='char'
	for i in range(1,len(rawstr)):
		c=rawstr[i]
		if c.isdigit() is True:
			t2="digit"
		else:
			t2='char'
		if t!=t2:
			if t=='digit':
				res.append(int(r))
			else:
				res.append(r)
			r=""
			t=t2
		r+=c
	if t=='digit':
		res.append(int(r))
	else:
		res.append(r)
	return res
def compareVersion(version1,version2):
	# -1: version1<version2 0:version1==version2 1:version1>version2
	v1=version1.split('.')
	v2=version2.split('.')
	for i in range(min(len(v1),len(v2))):
		v1l=splitDigitAndChar(v1[i])
		v2l=splitDigitAndChar(v2[i])
		for j in range(min(len(v1l),len(v2l))):
			v1i=v1l[j]
			v2i=v2l[j]
			if type(v1i)!=type(v2i):
				return 0
			if v1i<v2i:
				return -1
			if v1i>v2i:
				return 1
		# if len(v1l)<len(v2l):
		# 	return -1
		# if len(v1l)>len(v2l):
		# 	return 1
	# if len(v1)<len(v2):
	# 	return -1
	# if len(v1)>len(v2):
	# 	return 1
	return 0
def compareEntry(a,b):
	r=compareVersion(a.version,b.version)
	if r!=0:
		return r
	if a.release is None or b.release is None:
		return 0
	return compareVersion(a.release,b.release)
class PackageEntry:
	def __init__(self,name:str,flags:str,version:str,release:str):
		self.name=name
		self.flags=flags
		if version is not None:
			version=version.split(':')[-1]
		self.version=version
		self.release=release
	def checkMatch(self,dist):
		if self.flags is None or dist.flags is None:
			return True
		if dist.version is None:
			log.warning(self.name+" have problem: dist version is None")
			return True
		flags=self.flags
		if self.flags=='EQ' and dist.flags!='EQ':
			if dist.flags=='LE':
				flags='GE'
			elif dist.flags=='LT':
				flags='GT'
			elif dist.flags=='GE':
				flags='LE'
			elif dist.flags=='GT':
				flags='LT'
		if flags=='EQ':
			if compareVersion(dist.version,self.version)==0 and (self.release is None or dist.release is None or dist.release==self.release):
				return True
			else:
				return False
		elif flags=='LE':
			if compareEntry(dist,self)<=0:
				return True
			else:
				return False
		elif flags=='LT':
			if compareEntry(dist,self)==-1:
				return True
			else:
				return False
		elif flags=='GE':
			if compareEntry(dist,self)>=0:
				return True
			else:
				return False
		elif flags=='GT':
			if compareEntry(dist,self)==1:
				return True
			else:
				return False
	def dump(self):
		res=self.name
		if self.flags=='EQ':
			res+=' = '
		elif self.flags=='LE':
			res+=' <= '
		elif self.flags=='LT':
			res+=' < '
		elif self.flags=='GE':
			res+=' >= '
		elif self.flags=='GT':
			res+=' > '
		
		if self.version is not None:
			res+=self.version
		if self.release is not None:
			res+='-'+self.release
		return res
def defaultNoneList():
	return []
class EntryMap:
	def __init__(self):
		self.provideEntryPackages=defaultdict(defaultNoneList)
	def registerEntry(self,entry:PackageEntry,package):
		self.provideEntryPackages[entry.name].append((package,entry))
	def queryRequires(self,packageName,requireName:str,entrys:list,mustInstalled:bool,tag:int):
		# requireName==entrys[i].name
		infoList=self.provideEntryPackages[requireName]
		res=[]
		for info in infoList:
			package=info[0]
			if mustInstalled is True:
				if package.status=='uninstalled':
					continue
			provideEntry=info[1]
			isMatch=True
			for entry in entrys:
				if entry.checkMatch(provideEntry):
					continue
				else:
					isMatch=False
			if isMatch is True:
				res.append(package)
		#print(" "+entry.name)
		#for r in res:
			#print("  "+r[0].fullName)
		if len(res)==0:
			return []
		name_versionEntry=dict()
		for r in res:
			name=r.fullName
			if name not in name_versionEntry:
				name_versionEntry[name]=(r.getSelfEntry(),r)
			else:
				if compareEntry(name_versionEntry[name][0],r.getSelfEntry())==-1:
					name_versionEntry[name]=(r.getSelfEntry(),r)
		if len(name_versionEntry)<=1:
			return [name_versionEntry[res[0].fullName][1]]
		if packageName in name_versionEntry:
			return []
		if mustInstalled is True:
			return res
		if requireName in name_versionEntry:
			return [name_versionEntry[requireName][1]]
		if tag==1:
			return []
		log.warning("failed to decide require package for: "+requireName+" in pacakge: "+packageName)
		for r1 in res:
			log.info(" one of provider is: "+r1.fullName)
		log.info(" select: "+name_versionEntry[res[0].fullName][1].fullName)
		return [name_versionEntry[res[0].fullName][1]]

debugMode=False

def getDependes_dfs(package,dependesSet:set,entryMap,includeInstalled):
	if package in dependesSet:
		return
	if includeInstalled is False and package.status=='installed':
		return
	if package.status=='uninstalled':
		package.status='willInstalled'
	dependesSet.add(package)
	tag=1
	if includeInstalled is True:
		tag=2
	package.findRequires(entryMap,tag)
	if debugMode is True and includeInstalled is True:
		print("%"+package.fullName,package.packageInfo.version,package.packageInfo.release,package.status)
		print("%",end="")
		for p in package.requirePointers:
			print(" "+p.fullName,end="")
		print("")
	for p in package.requirePointers:
		getDependes_dfs(p,dependesSet,entryMap,includeInstalled)	
def getDependsPrepare(entryMap,package):
	depset=set()
	getDependes_dfs(package,depset,entryMap,False)
	return depset
def getDepends(entryMap,package,depset):
	getDependes_dfs(package,depset,entryMap,True)
	return depset
		
def defaultCVEList():
	return 0
class Counter:
	def __init__(self):
		self.cnt=0
	def getId(self)->int:
		self.cnt+=1
		return self.cnt
class SpecificPackage:
	def __init__(self,packageInfo:PackageInfo,fullName:str,provides:list,requires:list,arch:str,status="uninstalled",repoURL=None,fileName=""):
		provides.append(PackageEntry(fullName,"EQ",packageInfo.version,packageInfo.release))
		# if fullName=='indent':
		# 	for r in requires:
		# 		print(r.dump())
		# 	print(traceback.format_stack())
		self.packageInfo=packageInfo
		self.fullName=fullName
		self.providesInfo=provides
		self.requiresInfo=requires
		self.status=status
		self.arch=arch
		#self.providesPointers=[] # need not this feature
		self.requirePointers=[]
		self.repoURL=repoURL
		self.fileName=fileName
		self.getGitLinked=False
		self.registerProvided=False
		self.foundRequiresTag=0
	# def addProvidesPointer(self,package):
	# 	#无需手动调用，addRequirePointer自动处理
	# 	self.providesPointers.append(package)
	def addRequirePointer(self,package):
		self.requirePointers.append(package)
		#package.addProvidesPointer(self)
	def registerProvides(self,entryMap:EntryMap)->None:
		if self.registerProvided is True:
			return
		self.registerProvided=True
		for provide in self.providesInfo:
			entryMap.registerEntry(provide,self)
	def findRequires(self,entryMap:EntryMap,tag:int)->None:
		if self.foundRequiresTag==tag:
			return
		self.foundRequiresTag=tag
		self.clearRequires()
		requirePackageSet=set()
		requires=dict()
		for require in self.requiresInfo:
			if require.name not in requires:
				requires[require.name]=[]
			requires[require.name].append(require)
		solvedRequire=set()
		for requireName,requireList in requires.items():
			res=entryMap.queryRequires(self.fullName,requireName,requireList,True,tag)
			# if self.fullName=="indent":
			# 	print("-----")
			# 	print(requireName)
			# 	for r in res:
			# 		r.dump()
			# 	print("--")
			for r in res:
				if r not in requirePackageSet:
					self.addRequirePointer(r)
					requirePackageSet.add(r)
			if len(res)>0:
				solvedRequire.add(requireName)
		if self.status=="installed":
			return
		for requireName,requireList in requires.items():
			if requireName in solvedRequire:
				continue
			# if self.fullName=="indent":
			# 	print("-----")
			# 	print(requireName)
			# 	for r in res:
			# 		r.dump()
			res=entryMap.queryRequires(self.fullName,requireName,requireList,False,tag)
			for r in res:
				if r not in requirePackageSet:
					self.addRequirePointer(r)
					requirePackageSet.add(r)
			if len(res)>0:
				solvedRequire.add(requireName)
	def clearRequires(self):
		self.haveFoundRequires=False
		self.requirePointers=[]
	def dump(self):
		print(self.fullName,self.packageInfo.version,self.packageInfo.release,self.status)
		for p in self.requirePointers:
			print(" "+p.fullName,end="")
		print("")
	def getSelfEntry(self):
		return self.providesInfo[-1]
	def getNameVersion(self):
		res=self.fullName+"-"+self.packageInfo.version
		if self.packageInfo.release is not None:
			res+="-"+self.packageInfo.release
		return res