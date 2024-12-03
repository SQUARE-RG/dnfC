#获取操作系统信息


from subprocess import PIPE, Popen
import json
OSName=""
OSDist=""
arch=""
def removeQuotationMark(s:str)->str:
	if s.startswith('\"'):
		s=s[1:]
	if s.endswith('\"'):
		s=s[:-1]
	return s
def queryDnfContext():
	cmd="python3 -c 'import dnf, json; db = dnf.dnf.Base(); print(db.conf.substitutions)'"
	p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
	stdout, stderr = p.communicate()
	raw_data=stdout.decode()
	raw_data=raw_data.replace("\'","\"")
	try:
		data=json.loads(raw_data)
	except Exception:
		return None
	return data

with open("/etc/os-release") as f:
	data=f.readlines()
	for info in data:
		if info.startswith('ID='):
			OSName=removeQuotationMark(info.strip().split('=')[1])
		if info.startswith('VERSION_ID'):
			OSDist=removeQuotationMark(info.strip().split('=')[1])
		#if info.startswith('VERSION_ID'):
		#	OSDist=info.strip()[12:-1]
conf=queryDnfContext()
if conf is not None:
	arch=conf['arch']

