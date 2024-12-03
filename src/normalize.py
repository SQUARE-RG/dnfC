#对字符串中的特殊字符进行替换

def normalReplace(s:str)->str:
	s=s.replace('~','-tilde-')
	s=s.replace('+','-plus-')
	s=s.replace('_','-underline-')
	s=s.replace('@','-at-')
	s=s.replace('/','-slash-')
	s=s.replace('(','-leftBracket-')
	s=s.replace(')','-rightBracket-')
	s=s.replace(' ','-space-')
	s=s.replace('%','-percent-')
	return s

def reNormalReplace(s:str)->str:
	s=s.replace('-tilde-','~')
	s=s.replace('-plus-','+')
	s=s.replace('-underline-','_')
	s=s.replace('-at-','@')
	s=s.replace('-slash-','/')
	s=s.replace('-leftBracket-','(')
	s=s.replace('-rightBracket-',')')
	s=s.replace('-space-',' ')
	s=s.replace('-percent-','%')
	return s