import typing as T

def die(s,fn,lineNum,pos):
    #raise Exception(s+" in "+fn+"("+str(lineNum)+"/"+str(pos)+")")
    breakpoint()
    pass

import re

def unquote(s:str)->str: # remove leading/trailing " and convert \\ to \ and \" to "
    if s==None: return None
    if s=='""': return '' # special case doesn't match following sanity check
    assert s[0]=='"' and s[-1]=='"' and s[1]!='"' and s[-2]!='\\' and re.search(r'[^\\]"',s[1:-1])==None
    return re.sub(r'\\(.)',r'\1',s[1:-1])

def findDeep(x,it)->bool:
    if x==it: 
        return True
    else:
        try:
            for lower in it:
                if findDeep(x,lower):
                    return True
            return False
        except: # should check for TypeError only? FIXME
            return False

def evalCallable(s:str) -> T.Callable[[T.Any],T.Any]: # string s should give a callable, for None return None
    if s==None: return None
    rslt = eval(s)
    assert callable(rslt) # still needed I think ??
    return rslt

# to type this need the tricky stuff FIXME
def prependGen(hd,tl):
    yield hd
    yield from tl

if __name__=="__main__":
    h = (x for x in range(1,3))
    h = prependGen(0,h)
    print(*h)
 
