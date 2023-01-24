# koperator.py

# build operator datastructure from operator commands
# support getExpr with operator related code

# We allow overlap between operators as long as they can be read from
# left to right: we don't have to go back and reparse what we've seen.
# Brackets are an example. We want 3 operators defined:
# %^operator ("[",None,"]") "..." ["["] ["]"]
# %^operator ("[","]") "..." ["["] () [" ",repeating] () ["]"]
# %^operator ("[","|","]") "..." ["["] () ["|"] () ["]"]

#
from dataclasses import dataclass
import utility as U
import kast as A
import re
import decimal as D
import collections.abc as ca

# we have 2 dicts, noLeft and withLeft. The same operator can appear in both.
# If the operator is only in withLeft, and it gets there with no left argument
# then defaultOperand is inserted: Unit.unit in wombat.
# For each operand we have a priority (if it is left, or if it might be the last
# right sop) or we have the next mandatory sop. We also hold the list of
# expected sops (ie optional or repeating sops up to and including the next
# mandatory one).
# Operators can be defined for " " and "". These come into play when a subop
# with no right is followed by an op with no left. " " can also be used as
# a proper subop, but "" (which occurs when lexer puts in a break, but there are
# no spaces) cannot.

# FIXME: there should be severe restrictions on what subops can be used in subsubs.
# Probably shouldn't allow any that are used (active?) in the parent(etc).

# Note, when a subop has subsubs then: (a) it must be in again as the first subsub,
# but set as mandatory (whatever it is at a higher level). The adjust ast in
# the subsub applies to the immediately following param, but the adjust param
# at the higher level applies to the subop combined with all the subsubs
 
#OpInfo = C.namedtuple('OpInfo','left,astFun,paramLen,subops') # if left!=None it has pos==0
@dataclass(frozen=True,slots=True)
class OpInfo:
    left:'SSparam'|None # None if no left
    astFun:ca.Callable[[A.AstNode],A.AstNode]|A.AstNode|None
    paramLen:int
    subops:list['SSsubop'] # 1st one is initial sop

#SSparam = C.namedtuple('SSparam','precedence,pos,oneAdjust,ssParamLen,subsubs')
@dataclass(frozen=True,slots=True)
class SSparam:
    precedence:D.Decimal|None # non-None if left, or has no following mandatory
    pos:int
    oneAdjust:A.AstNode|ca.Callable[[A.AstNode],A.AstNode]|None
    ssParamLen:int
    subsubs:list['SSsubop']

#SSsubop = C.namedtuple('SSsubop','subop,occur,allAdjust,v')
                       # v a dict with param,nextMandatory,nextPossibles
@dataclass(frozen=False,slots=True)
class SSsubop:
    subop:str
    occur:str # mandatory, or ...
    allAdjust:ca.Callable[[A.AstNode],A.AstNode]|A.AstNode|None
    param:SSparam|None
    nextMandatory:str|None
    nextPossibles:list[str]

# OpKey is the key for dictionaries noLeft and withLeft. 
# the key is the mandatory subops, plus None added after subops with no param
# However strip a trailing None, since can't have withRight and noRight variants
OpKey = tuple[(str|None),...]
OpDict = dict[OpKey|str,OpInfo|list[OpKey]]
noLeft:OpDict = {}
withLeft:OpDict = {}

# Really the keys should be based on text,tokenType pairs. This would require
# some interaction with the lexer. At the moment there is a danger of mistaking
# an atom or string for an operator by looking at the text and not checking
# the tokenType. FIXME (big job)
def getKeyTuple(subops:list[SSsubop])->OpKey:
    if subops==[]:
        return () # empty tuple if no more
    kt0 = () # zero tuple
    if subops[0].occur=="mandatory":
        if subops[0].param!=None: # funny place to put this check
            assert subops[0].param.subsubs==None
        kt0 = (subops[0].subop,) # 1-tuple
        if len(subops)>1 and subops[0].param==None:
            kt0 = (subops[0].subop,None)
    return kt0+getKeyTuple(subops[1:]) # + is tuple concat

def getZeroOpInfo(whichDict:OpDict,partkey:OpKey)->OpInfo: # usually just first
    whichDictOfpartkey:OpInfo|list[OpKey] = whichDict[partkey]
    if isinstance(whichDictOfpartkey,OpInfo):
        return whichDictOfpartkey
    else:
        # If a list[OpKey] then all elements in the list point to OpInfo
        #assert whichDictOfpartkey is list[OpKey]
        w:OpInfo|list[OpKey] = whichDict[whichDictOfpartkey[0]]
        assert isinstance(w,OpInfo)
        return w # return first #type FIXME

def subsubEqual(ss1:list[SSsubop],ss2:list[SSsubop]): # just a recursive assert
    if ss1==ss2: return
    assert ss1[0].subop == ss2[0].subop
    assert ss1[0].occur == ss2[0].occur
    match ss1[0].param:
        case None:
            assert ss2[0].param==None
        case SSparam() as ss1p:
            ss2p = ss2[0].param
            assert ss2p
            subsubEqual(ss1p.subsubs,ss2p.subsubs)
        case _:
            assert False
    subsubEqual(ss1[1:],ss2[1:])

def subOpCompat(so1:list[SSsubop],so2:list[SSsubop]):
    assert len(so1)!=0 and len(so2)!=0 # would be overlap (and not got here)
    if so1[0].occur=="mandatory" and so2[0].occur=="mandatory":
        if so1[0].subop != so2[0].subop: # good distinguisher
            return # we are compat
        if so1[0].param==None and so2[0].param!=None:
            return # one has param, one doesn't, that distinguishes
        if so1[0].param!=None and so2[0].param==None:
            return # one has param, one doesn't, that distinguishes
        # else: # actually nothing to do - we will go deeper
    else: # if not both mandatory then they need to be the same, same subsubs
        assert so1[0].occur==so2[0].occur # equal and not mandatory
        assert so1[0].subop==so2[0].subop
        match so1[0].param:
            case None:
                assert so2[0].param is None
            case _:
                assert so2[0].param
                subsubEqual(so1[0].param.subsubs,so2[0].param.subsubs)
    subOpCompat(so1[1:],so2[1:])

def checkCompat(oi1:OpInfo,oi2:OpInfo): # 2 OpInfo
    if oi1.left!=None:
        assert oi2.left!=None and oi1.left.precedence==oi2.left.precedence
    else:
        assert oi2.left==None
    subOpCompat(oi1.subops,oi2.subops)

def insertOp(whichDict:OpDict, opInfo:OpInfo):
    opKey = getKeyTuple(opInfo.subops)
    assert opKey not in whichDict # not overlap
    whichDict[opKey] = opInfo
    if len(opKey)==1:
        opk0 = opKey[0]
        assert isinstance(opk0,str)
        whichDict[opk0] = opInfo # pylance fails to typecheck FIXME
        return
    # now we must work backwards, creating links and checking compatibility
    # We only need to check compatibility once, since existing operators
    # are compatible with each other.
    curKey = opKey[:-1]
    compatChecked = False
    while len(curKey)>0:
        if curKey not in whichDict: # can just put a point to ourself
            whichDict[curKey] = [opKey] # start a new list of opKeys
        else:
            wc = whichDict[curKey]
            assert not isinstance(wc, OpInfo) # would be overlap
            #assert isinstance(wc,list[OpKey])
            # so we have a list of potential overlaps
            if not compatChecked: # check against first one
                wo = whichDict[opKey]
                assert isinstance(wo,OpInfo)
                wwc0 =whichDict[wc[0]]
                assert isinstance(wwc0,OpInfo)
                checkCompat(wo,wwc0)
                compatChecked = True
            wc.append(opKey) # add ourselves to list
        if len(curKey)==1:
            whichDict[U.notNone(curKey[0])] = whichDict[curKey] # HACK
        curKey = curKey[:-1] # truncate

def mctlEval(s:str|None)->ca.Callable[[A.AstNode],A.AstNode]|A.AstNode|None: # typing FIXME
    if s==None: return None
    rslt = eval(s)
    assert rslt==None or callable(rslt) or isinstance(rslt,A.AstNode)
    return rslt

# operators are defined by enough mandatory subops (incl op).
# So the key is a list of subop strings. The value is a list of follow 
# on (mandatory) subops, and opInfo which is null when the list of follow ons
# has more than one entry.

# The opInfo entries have: This is WRONG FIXME
#  'opDefine' is the list of mandatory ops that define us
#  'allMandatory' is the complete list of top level mandatory
#  'left' is the operand spec, None if in noLeft
#  'right' is the sops which is the same format as subsubs, None if no right

sopSpecRE:re.Pattern[str] = re.compile(r'''
    (?: # we have subops in []s and params in ()s. This covers the [] case
        \[ 
            \s*(?P<subop>"(?:[^\\"]|\\.)*") # the subop is in "s
            (?:\s*(?P<occur>mandatory|optional|repeating))? # occur optional
            (?:\s*(?P<allAdjust>"(?:[^\\"]|\\.)+"))? # adjust optional
        \s*\] # maybe whitespace before ]
    ) | # end of [], alternativel ()
    (?: # here begins the (), parameter, case
        \s*\( 
            (?:\s*(?P<precedence>\d+\.?\d*))? # optional precedence
            (?:\s*(?P<oneAdjust>"(?:[^\\"]|\\.)+"))? # optional adjust
            (?:\s*(?P<FIXME>\W)(?P<subsubs>.+)(?P=FIXME))? # opt subsubs
        \s*\)
    ) 
    ''',re.VERBOSE)
def genSopSpec(fromRE:ca.Iterator[re.Match[str]])->ca.Generator[SSsubop|SSparam,None,None]:
    # should check there is no bad stuff: end of each should go with 
    # start of next FIXME
    pos = 0
    for mss in fromRE:
        #assert mss.group('badSpec')==None # should die FIXME
        if mss.group("subop"):
            assert mss[0][0]=='['
            occur = "mandatory"
            if mss.group("occur"): occur = mss.group("occur")
            yield SSsubop(subop=U.notNone(U.unquote(mss.group("subop"))),
                          occur=occur,
                          allAdjust=mctlEval(U.notNone(U.unquote(mss.group("allAdjust")))),
                          param=None,
                          nextMandatory=None,
                          nextPossibles=[]
                        ) # param will later be set to the next SSparam
        else:
            assert re.match(r'\s*\(',mss[0])!=None
            pT:str|None = mss.group("precedence")
            _dummyLeft,subsubs,ssParamLen=getSopSpec(mss.group("subsubs"))
            yield SSparam(precedence=D.Decimal(pT) if isinstance(pT,str) else None,
                          pos=pos,
                          oneAdjust=mctlEval(U.unquote(mss.group("oneAdjust"))),
                          ssParamLen=ssParamLen,
                          subsubs=subsubs)
            pos = pos+1

# ssPair takes a iter of sops and operands without repeating operands,
# and generates one yield per sop, with the operand set to None if no
# following operand.
def ssPair(sopAndParam:ca.Iterator[SSsubop|SSparam])->ca.Generator[SSsubop,None,None]:
    sop = next(sopAndParam,None)
    while True:
        assert (sop!=None) and (type(sop) is SSsubop)
        nxt = next(sopAndParam,None)
        if nxt!=None and type(nxt) is SSparam: # normal case
            sop.param = nxt
            yield sop
            sop = next(sopAndParam,None)
            if sop==None: return
        elif nxt==None:
            sop.param = None
            yield sop
            return
        else: # 2 sops in a row
            sop.param = None
            yield sop
            sop = nxt

# for each position that you can be in within an operator, we need to
# know 2 things, so we calculate them here. They are: (1) the next 
# mandatory we'll come to within this operator, or the right precedence 
# if none; and (2) the list of all possible subops that might come up
# next (since these override operator declarations) [the last of these
# will be the next mandatory if there is one].
def getMandPoss(sopSpec:list[SSsubop],i:int,pLen:int)->tuple[str|None,list[str],int]:
    if i==len(sopSpec):
        return None,[],pLen # nextMandatory,possibles
    nextNextMan,nextPoss,pLen = getMandPoss(sopSpec,i+1,pLen)
    assert sopSpec[i]
    p = sopSpec[i].param
    if p!=None: pLen = max(p.pos+1,pLen)
    if p!=None and p.subsubs: # have subsubs
        subNextMan,subPoss,_ssParamLen = getMandPoss(p.subsubs,0,0) # hmm, doing twice
        sopSpec[i].nextMandatory = subNextMan if subNextMan!=None else nextNextMan
        #sopSpec[i].v['nextPossibles'] = subPoss + nextPoss
        sopSpec[i].nextPossibles = subPoss if subNextMan!=None else subPoss + nextPoss
    else:
        sopSpec[i].nextMandatory = nextNextMan
        sopSpec[i].nextPossibles = nextPoss
    if sopSpec[i].occur=='mandatory':
        return sopSpec[i].subop,[sopSpec[i].subop],pLen # just me
    else:
        return sopSpec[i].nextMandatory, \
           [sopSpec[i].subop]+sopSpec[i].nextPossibles,pLen

# the syntax defining and operator alternates operands in ()s [with precedence
# if left or right], and (sub)operators in []s which is the operator text in "s,
# followed by some extra stuff [adjustment code, mandatory/repreating/...]
def getSopSpec(sopSpecText:str|None)->tuple[SSparam|None,list[SSsubop],int]:
    if sopSpecText==None: return None,[],0 # for subsubs only
    sopSpecUnpaired:list[SSsubop|SSparam] = [*genSopSpec(re.finditer(sopSpecRE,sopSpecText))]
    if sopSpecText[0]=='(': # never for subsub
        assert isinstance(sopSpecUnpaired[0],SSparam)
        left:SSparam|None = sopSpecUnpaired[0]
        sopSpec = [*ssPair(iter(sopSpecUnpaired[1:]))]
    else:
        left = None
        sopSpec = [*ssPair(iter(sopSpecUnpaired))]
    # now need to add to each parameter, the list of possible nextSop
    # and the next mandatory if there is no precedence.
    # [the following is done for side effects and pLen]
    _nextMandatory,_possibles,pLen = getMandPoss(sopSpec,0,(1 if left!=None else 0))
    for i in range(len(sopSpec)):
        if sopSpec[i].occur=='repeating': # if repeating then we need to be in nextPossibles
            sopSpec[i].nextPossibles.append(sopSpec[i].subop) 
    return left,sopSpec,pLen

def doOperatorCmd(astFun:str,sopSpecText:str):
    # op is the operator being defined = first sop
    # astFun is compile time code (python3) generating an AST for the procedure
    # sopSpec: see compiler.md
    left,sopSpec,pCnt = getSopSpec(sopSpecText)
    insertOp((withLeft if left else noLeft),
             OpInfo(left=left,astFun=mctlEval(astFun),paramLen=pCnt,subops=sopSpec))

# first2rest is a common allAdjust parameter, used where we put the first part
# of a tuple operand, then have the rest as a repeating operand.
def first2rest(tup:A.AstTuple)->A.AstTuple:
    assert isinstance(tup,A.AstTuple)
    if len(tup.members)<2: 
        return tup
    else:
        assert len(tup.members) == 2

    tm1:A.AstNode = tup.members[1]
    assert isinstance(tm1,A.AstTuple)
    return A.AstTuple(members=(tup.members[0],*(tm1.members))) # called be parent/closure set

if __name__=="__main__":
    #import lexer
    doOperatorCmd( "A.callOp", '(100) [" "] (100)')
    doOperatorCmd("A.zeroTuple",'["["] ["]"]')
    doOperatorCmd("A.zeroTuple",'["["] () [" " repeating] () ["]"]')
    doOperatorCmd("A.zeroTuple",'["["] () ["|"] () ["]"]')
    print(noLeft)

