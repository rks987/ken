import typing
import collections.abc as ca

def die(s:str,fn:str,lineNum:int,pos:int)->typing.NoReturn:
    raise Exception(s+" in "+fn+"("+str(lineNum)+"/"+str(pos)+")")
    #breakpoint
    #pass

X = typing.TypeVar("X") 
def notNone(x:X|None)->X:
    assert x
    return x
A = typing.TypeVar("A")
B = typing.TypeVar("B")
#def notB(x:A|B|None)->A|None:
#    assert isinstance(x,A) or 
#    return x
Z = typing.TypeVar("Z")
def noNones(lz:list[Z|None])->list[Z]:
    return [notNone(lz[i]) for i in range(len(lz))]

import re

def unquote(s:str|None)->str|None: # remove leading/trailing " and convert \\ to \ and \" to "
    if s==None: 
        return None
    assert isinstance(s,str)
    if s=='""': return '' # special case doesn't match following sanity check
    assert s[0]=='"' and s[-1]=='"' and s[1]!='"' and s[-2]!='\\' and re.search(r'[^\\]"',s[1:-1])==None
    return re.sub(r'\\(.)',r'\1',s[1:-1])

def findDeep(x:typing.Any,it:typing.Any)->bool:
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

def evalCallable(s:str|None) -> ca.Callable[[typing.Any],typing.Any] | None:
    if s==None: return None
    assert isinstance(s,str)
    rslt = eval(s)
    assert callable(rslt) # still needed I think ??
    return rslt

# to type this need the tricky stuff FIXME
Y = typing.TypeVar('Y')
def prependGen(hd:Y,tl:ca.Generator[Y,None,None])->ca.Generator[Y,None,None]:
    yield hd
    yield from tl

if __name__=="__main__":
    h = (x for x in range(1,3))
    h = prependGen(0,h)
    print(*h)
 
