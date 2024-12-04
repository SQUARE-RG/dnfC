# dnfC.py为程序入口，若想阅读源码，应从此处开始
# 此文件解析用户输入，从而分析命令类型，并根据命令调用对应模块进行处理

# 若命令为install/reinstall/genspdx/gencyclonedx，则调用scanDeb模块处理，模块返回值表示是否要执行安装，有关该模块详细细节详阅scanBin.py
# 若命令为scanbin，则调用scanBin模块处理
# 若命令为scansrc，则调用scanSrc模块处理
# 若命令为querycve，则调用queryCVE模块处理

# 除此之外，项目存在一些重要的底层模块，在此列出简单介绍：
# RepoFileManager: 实现对元数据进行解析的功能
# SourceListManager: 对本地软件源仓库进行管理，自动读取全部元数据，依赖于RepoFileManager
# PackageInfo.py: 一个PackageInfo表示一个项目的信息，一个项目可以对应一个源码包（如果有源码包的话），一个项目可能对应多个软件包。
# SpecificPackage.py 一个SpecificPackage表示一个软件包的信息，它内部包含一个PackageInfo，即包含了对应项目信息。可能存在多个软件包对应完全相同的项目信息。
# SpecificPackage.py内实现了依赖图分析的代码，请有关该模块详细细节详阅SpecificPackage.py


import sys
import os
DIR = os.path.split(os.path.abspath(__file__))[0]
import scanBin
import scanSrc
import scanDnf


def runDnf(args,setyes=False):
	cmd="/usr/bin/dnf"
	for arg in args:
		if arg=='-y':
			setyes=True
		if arg=='-n':
			pass
		elif arg.startswith('--genspdx'):
			pass
		elif arg.startswith('--gencyclonedx'):
			pass
		else:
			cmd+=" '"+arg+"'"
	if setyes is True:
		cmd+=" -y"
	return os.system(cmd)

def user_main(args, exit_code=False):
	errcode=None
	for arg in args:
		if arg=='-y':
			errcode=runDnf(args)
			break
	if errcode is None:
		if len(args)==0:
			errcode=runDnf(args)
		elif args[0]=='install':
			if scanDnf.scanDnf(args) is True:
				errcode=runDnf(args,setyes=True)
			else:
				errcode=0
		elif args[0]=='genspdx':
			if len(args)<3:
				print("unknown usage for apt genspdx")
				return 1
			scanDnf.scanDnf(args[1:-1],genSpdx=True,saveSpdxPath=args[-1],genCyclonedx=False,saveCyclonedxPath=None,dumpFileOnly=True)
			return 0
		elif args[0]=='gencyclonedx':
			if len(args)<3:
				print("unknown usage for apt gencyclonedx")
				return 1
			scanDnf.scanDnf(args[1:-1],genSpdx=False,saveSpdxPath=None,genCyclonedx=True,saveCyclonedxPath=args[-1],dumpFileOnly=True)
			return 0
		elif args[0]=='scanbin':
			errcode=scanBin.scanBin(args[1:])
		elif args[0]=='scansrc':
			errcode=scanSrc.scanSrc(args[1:])
		elif args[0]=='queryCVE':
			errcode=scanSrc.scanSrc(args[1:])
	if errcode is None:
		errcode=runDnf(args)

	if exit_code:
		sys.exit(errcode)
	return errcode

#if __name__ == '__main__':
#	user_main(sys.argv[1:],True)