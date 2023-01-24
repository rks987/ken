# lexer.py -- turn file into iterator of tokens

import typing
import collections.abc as ca
from dataclasses import dataclass

@dataclass(frozen=True,slots=True)
class TokTT:
    text:str
    tType:str

@dataclass(frozen=True,slots=True)
class Token:
    tT:TokTT
    indent:int
    whiteB4:bool
    location:tuple[str,int,int] # file, line, char

import utility as U
import re
#import regex as re
white: re.Pattern[str] = re.compile(r"\s*") # always matches
def whiteMatch(s:str, pos:int=0)->re.Match[str] :
    m:re.Match[str]|None = white.match(s,pos)
    assert m
    return m
upSlash: re.Pattern[str] = re.compile(r"\%\/")

import decimal
D = decimal.Decimal
@dataclass(frozen=True,slots=True)
class TokenClass:
    tokRE:re.Pattern[str]
    adjust:ca.Callable[[typing.Any],typing.Any] | None
    tType:str
    tComment:str
tokenClassByPrio:dict[D,list[TokenClass]] = {}  # value for each TokenClass: list of (pattern,adjustment,tType)
tokenClassPrios:list[D] = []   # keep descending sorted list of Prios
def insertTokenClass(prio:D, tokenClass:TokenClass):
    global tokenClassPrios
    if prio in tokenClassByPrio:
        tokenClassByPrio[prio].append(tokenClass)
    else:
        tokenClassByPrio[prio] = [tokenClass]
        tokenClassPrios = sorted([*iter(tokenClassByPrio.keys())],reverse=True)
    return

def lexer(fileName:str)->ca.Iterator[Token]:
    lineNum:int = 0
    yield Token(tT=TokTT(text="!!SOF",tType="OperatorOnly"),indent=0,whiteB4=False,
               location=(fileName,0,0))
    # should allow %\ at end of line to split long lines (or %+ at start of next ?)
    for line in open(fileName, "r", encoding="utf-8"):
        whiteB4:bool = True # at a new line
        lineNum += 1
        indentM:re.Match[str] = whiteMatch(line)
        indent:int = len(indentM[0]) # set to -1 after 1st token
        pos:int = indent
        if upSlash.match(line,indent):
            # lex command
            m:re.Match[str]|None = re.compile(r"include\s+(\S+)\n?").fullmatch(line,indent+2)
            if m:
                yield from lexer(m[1])  # recurse
            else:
                #e.g. %/token String 100 "U.unquote" (?P<token>"(\\"|\\\\|[^"\\])*")
                n = re.compile(r'token\s+(\w+)\s+("[^"]+")\s+(\d+\.?\d*)\s+("(?:[^\\"]|\\.)*")?\s*([^\n]+)')\
                      .match(line,indent+2)
                if n:
                    #print(n[5])
                    tokenClass = TokenClass(tType=n[1], tComment=n[2], tokRE=re.compile(n[5]),
                                            adjust=U.evalCallable(U.unquote(n[4])))
                    insertTokenClass(D(n[3]), tokenClass)
                else:
                    raise Exception("unknown %/ cmd:"+line)
        else: # multiple ordinary tokens
            while pos!=len(line):
                @dataclass(frozen=True,slots=True)
                class Found:
                    tokTT:TokTT
                    length:int
                #Found = C.namedtuple('Found',['tokTT','length'])    
                found:Found|None = None
                for p in tokenClassPrios:
                    if found!=None:
                        break # must have found one at higher priority
                    for tc in tokenClassByPrio[p]:
                        tm:re.Match[str]|None = tc.tokRE.match(line,pos)
                        if tm:
                            tt:str = tm['token'] if tc.adjust is None else tc.adjust(tm['token'])
                            tokTT = TokTT(text=tt,tType=tc.tType)
                            if found!=None:
                                if found!=Found(tokTT=tokTT,length=len(tm[0])):
                                    U.die(f"conflicting tokens: {found.tokTT.text} {tm['token']}",
                                        fileName,lineNum,pos)
                            else:
                                found = Found(tokTT=tokTT,length=len(tm[0]))
                assert found # hack FIXME
                wm:re.Match[str] = whiteMatch(line, pos+found.length)
                gotWhite:bool = pos+found.length==len(line) or len(wm[0])>0
                if found.tokTT.tType!='Comment':
                    yield Token(tT=found.tokTT,indent=indent,
                                whiteB4=whiteB4, location=(fileName,lineNum,pos))
                whiteB4 = gotWhite
                indent = -1
                pos += found.length+len(wm[0])
    yield Token(tT=TokTT(text="!!EOF",tType="OperatorOnly"),indent=0,whiteB4=True,
               location=(fileName,lineNum+1,0))
    return
# above is too complicated...FIXME

if __name__ == "__main__":
    # execute only if run as a script
    import sys 
    for tok in lexer(sys.argv[1]):
        print(tok)
