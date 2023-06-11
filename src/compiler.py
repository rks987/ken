# compiler.py

# from wombatlang. Add types and kenify.

# A typical token:
#  {'token': 'true', 'tType': 'Identifier', 'indent': -1, 'gotWhite': True, 
#   'location': ('src/wombat.wh', 25, 13)}

# The lexer should returns a token modified from source, e.g. remove the ` from a new identifier).
# So you can get the same token with different token type (tType).
# Operator code should checks for TokenType as Identifier or OperatorOnly.

#import typing as T
import utility as U
import kast as A
import lexer as L
import koperator as op # build and parse operators
import collections.abc as ca
import re
#import regex as re
#import interp as I
import decimal
D = decimal.Decimal

operatorRE:re.Pattern[str] = re.compile(r'\s*("(?:[^\\"]|\\.)+")\s+([^\n]+)\n?$')

def doKCTcmd(cmd:str, tok:L.Token)->A.AstTuple:
    if 'operator '==cmd[0:9]:
        mo:re.Match[str]|None = operatorRE.match(cmd[9:])
        if mo:
            op.doOperatorCmd(U.notNone(U.unquote(mo[1])),mo[2])
        else: 
            U.die("invalid operator decl: "+cmd,*tok.location)
    #elif 'defaultOperand '==cmd[0:15]:
    #    defaultOperand = eval(cmd[15:]) # must be an ASTree
    elif 'import '==cmd[0:7]:
        raise Exception("import not implemented -- FIXME")
    elif 'package '==cmd[0:8]:
        raise Exception("package not implemented -- FIXME")
    elif 'export '==cmd[0:7]:
        raise Exception("export not implemented -- FIXME")
    else:
        U.die("unknown KCTcmd: "+cmd,*tok.location) 
    return A.zeroTuple() #?? defaultOperand

def opFunL(fun:A.AstNode|ca.Callable[[tuple[A.AstNode,...]],A.AstNode], astL:tuple[A.AstNode,...])->A.AstNode:
    #for a in astL: assert isinstance(a,A.AstNode)
    if callable(fun):
        return fun(astL)
    assert isinstance(fun,A.AstNode)
    if len(astL)==0: return fun # operator with no left or right - just return its fun
    return opFunAst(fun, astL[0] if len(astL)==1 else A.AstTuple(members=tuple(astL)))
def opFunAst(fun:A.AstNode|None,pAst:A.AstNode)->A.AstNode:
    #assert isinstance(pAst,A.AstNode)
    if fun==None: 
        return pAst
    return A.AstCall(procParam=A.AstTuple(members=(fun,pAst)))

# At any point we are a hierarchy of operators. For each operator we are in we are
# at a position which is a list of indices into the subops, and subsubs, etc.
# From that position we know (nextPossibles) what the possible proper subops are;
# and if there is no nextMandatory then we need to also consider the nextPossibles
# at one layer up.
# [NB for following sentence: Currently just have one index, not a list, and handle
# subsubs by creating a fake context. No testing of subsubs has been done FIXME]
# opCtx points to current parentCtx and a set of (opInfo, indexList) pairs. If the 
# token is one of the nextPossibles of 1st pair then (a) fill in opt and rept params up 
# to that; (b) adjust indexList; (c) if it was mandatory then it must be same as
# nextMandatory (1st pair), so delete all the others with a different nextMandatory.
# If not in nextPossibles then (a) see if it is nextMandatory of one of other pairs,
# and if so delete all pairs that have a different nextMandatory; (b) otherwise
# it is the operator of some inner expr, so call getExpr recursively to get that.
# Also need to catch the case where there is/isn't an intervening operand.
from dataclasses import dataclass

@dataclass(frozen=True,slots=True)
class OpCtx:
    upOpCtx: 'OpCtx'
    indx: int
    altOpInfos: list[op.OpInfo]
#OpCtx = C.namedtuple('OpCtx','upOpCtx,indx,altOpInfos') # indx is where we are in any
                                                     # of opInfos -- op.OpInfo
#outerOpCtx:OpCtx = OpCtx(upOpCtx=outerOpCtx,indx=0,altOpInfos=[])

def posSubop(tokTT:L.TokTT,opCtx:OpCtx|None)->bool:
    # remember altOpInfos are all the same on optional or repeating, can only differ
    # in nextMandatory (=nextPossibles[-1] if present)
    if tokTT.tType not in ['Identifier','OperatorOnly']: return False # REF-1
    if opCtx is None or len(opCtx.altOpInfos)==0: return False
    if any(tokTT.text in opCtx.altOpInfos[i].subops[opCtx.indx].nextPossibles\
            for i in range(len(opCtx.altOpInfos))):
        return True
    for oi in opCtx.altOpInfos:
        if tokTT.text == oi.subops[opCtx.indx].nextMandatory:
            return True
    # if any of the options has no nextMandatory, then we need to look up
    for oi in opCtx.altOpInfos:
        if oi.subops[opCtx.indx].nextMandatory is None:
            return posSubop(tokTT,opCtx.upOpCtx)
    return False

def needNoLeft(tok:L.Token,toks:ca.Generator[L.Token,None,None],opCtx:OpCtx,noneOK:bool)->\
            tuple[L.Token|None,ca.Generator[L.Token,None,None]]:
    if (tok.tT.tType in ['Identifier','OperatorOnly']) and ((posSubop(tok.tT,opCtx)) or \
                         ((tok.tT.text not in op.noLeft) and (tok.tT.text in op.withLeft))):
        # should have had a left or operand preceding subop
        if noneOK: # none it is then
            return None,U.prependGen(tok,toks)
        # better insert defaultOperand
        defOperandTok = L.Token(tT=L.TokTT(text='!!defaultOperand',tType='OperatorOnly'),
                                indent=tok.indent,whiteB4=False,location=tok.location)
        return defOperandTok, U.prependGen(tok,toks) # backup a bit
    return tok,toks

def needLeft(tok:L.Token,toks:ca.Generator[L.Token,None,None])->\
            tuple[L.Token,ca.Generator[L.Token,None,None]]:
    if (tok.tT.tType not in ['Identifier','OperatorOnly']) or (tok.tT.text not in op.withLeft):
        # insert space or adjacency subop
        return L.Token(tT=L.TokTT(text=(" " if tok.whiteB4 else ""),tType='OperatorOnly'),
                          indent=tok.indent,whiteB4=False,location=tok.location),\
               U.prependGen(tok,toks)
    return tok,toks

# We only call getExpr with left==None if we know the next token is an op
# with no left (includes identifiers and constants). We don't call getExpr with a 
# left unless the following token is an
# operator that takes a left. However whether we give it to that operator
# depends on precedence. 
def getExpr(toks:ca.Generator[L.Token,None,None],left:A.AstNode|None,prio:D|None,opCtx:OpCtx,noneOK:bool) \
           ->tuple[A.AstNode|None,ca.Generator[L.Token,None,None]]:
    # toks is the token generator. Can push tokens back using prependGen
    # left is the left parameter if there is one
    # prio is the right priority if the caller has gone past mandatory subops
    # opCtx
    # noneOK -- true if we might have no expr (returning None)
    #
    # return an ast, and the token generator as possibly modified
    tok = next(toks)
    #assert tok is not None

    while (tok.tT.tType=='Comment') or (tok.tT.tType=='MCTcmd'):
        if tok.tT.tType=='MCTcmd':
            doKCTcmd(tok.tT.text,tok)
        tok = next(toks)
        #assert tok is not None

    # we're at the start here - get the relevant opInfo
    #
    # In the following: operators last forever and aren't superceded by identifers FIXME
    #
    opDict = None
    if left==None:
        tok,toks = needNoLeft(tok,toks,opCtx,noneOK) # defaultOperand comes back if needed
        if tok==None: return None,toks
    else: # need something with a left
        tok,toks = needLeft(tok,toks)
        if posSubop(tok.tT,opCtx): # this can happen if tok is insert " ", but maybe else
            return left,U.prependGen(tok,toks) # put space subop into toks
        assert (tok.tT.tType in ['Identifier','OperatorOnly']) and (tok.tT.text in op.withLeft)
        if (prio!=None) and (U.notNone(U.notNone(op.getZeroOpInfo(op.withLeft,(tok.tT.text,)).left).precedence) < prio) :
            # push the tok back and just return the left to go with the source of prio
            return left,U.prependGen(tok,toks)

    opDict = op.withLeft if left!=None else op.noLeft
    if tok.tT.text not in opDict:
        assert left==None and tok.tT.text not in op.noLeft
        # must be an identifier or constant
        opDict = None
        if tok.tT.tType in ['String','Number','Atom']:
            ast = A.AstConstant(const=tok.tT.text,constType=tok.tT.tType)
        else:
            IdClasses = {'Identifier': A.AstIdentifier, 'NewIdentifier':A.AstNewIdentifier,
                     'FreeVariable':A.AstFreeVariable, 'NewFreeVariable':A.AstNewFreeVariable}
            ast = IdClasses[tok.tT.tType](identifier=tok.tT.text)
    # here ends interlude of special cases: back to operators
    else:
        # at this point we are ready to start chewing up subops. It's exactly like subsubs,
        # except that ...
        if isinstance(opDict[tok.tT.text],op.OpInfo):
            oiL = [opDict[tok.tT.text]]
        else:
            x = opDict[tok.tT.text]
            assert isinstance(x,str)
            oiL = opDict[x]
        assert isinstance(oiL,op.OpInfo)
                                #[opDict[t] for t in opDict[tok.tT.text]]
        # in next line, want to reprocess op = 1st subop
        opInfo,pAsts,toks = getSubops(toks=U.prependGen(tok,toks),\
                                  opCtx=OpCtx(upOpCtx=opCtx,indx=0,altOpInfos=[oiL]))
        if opInfo.left!=None: # pAsts is a list of multiple params
            pAsts[0] = U.notNone(left) # add in left param
        assert opInfo.astFun is not None
        ast = opFunL(opInfo.astFun,tuple(pAsts)) # type: ignore
    # at this point the next tok might be a nextPos for our parent, otherwise we've
    # got a left and we should keep looking
    tok = next(toks)
    if posSubop(tok.tT,opCtx):
        return ast,U.prependGen(tok,toks)
    # only option now is that what we have is a left operand for what follows. 
    # Don't need to insert a space/adjacent (sub)op -- needLeft will fix it
    expr,toks = getExpr(toks=U.prependGen(tok,toks),left=ast,prio=prio,opCtx=opCtx,noneOK=False)
    return expr,toks

# we get a list of possible SSsubop lists, expecting to match one. We return a tuple
# with (1) the one we matched; (2) list of param ASTs; (3) the token generator. We will
# have pushed back the token that has lower left precedence than our right precedence.
def getSubops( toks:ca.Generator[L.Token,None,None],opCtx:OpCtx)-> \
             tuple[op.OpInfo,list[A.AstNode],ca.Generator[L.Token,None,None]]:
    tok:L.Token = next(toks)
    maxPL:int = max((oi.paramLen for oi in opCtx.altOpInfos))
    pAstL:list[A.AstNode|None] = [None]*maxPL # list for param ast (might be truncated at the end)
    indx:int = 0  # this is the index into each list in oiL
    oiL:list[op.OpInfo] = opCtx.altOpInfos[:] # take a copy
    while True:
        # if the next sop is mandatory in any of oiL then we must have it, or we can
        # delete the entries in oiL that do. Of course for the start of a top level
        # we will have it because that's how we got here at all.
        oiL = [oiL[i] for i in range(len(oiL)) if oiL[i].subops[indx].occur!='mandatory' or \
                                                  oiL[i].subops[indx].subop==tok.tT.text]
        assert oiL!=[]
        if len(oiL[0].subops)-1==indx and oiL[0].subops[indx].param==None:
            # note: this special case shouldn't be needed check/FIXME.
            # the trailing subop has no right
            assert len(oiL)==1 # can't have a competitor for this!
            assert oiL[0].subops[indx].occur=='mandatory'
            return oiL[0],U.noNones(pAstL[:oiL[0].paramLen]),toks
        # A tricky point is that mandatory might have no following value -- its only
        # role is to pick the oiL. Optional and repeating always have a value param,
        # though sometimes no values.
        numMandatory = sum((1 for i in range(len(oiL)) \
                                if oiL[i].subops[indx].occur=='mandatory'))
        # can you have the same token as optional/repeating in one possible subops match
        # while it is mandatory in a competing one? For the moment say no. Doc it FIXME
        assert numMandatory==0 or numMandatory==len(oiL) # all in sync.
        # They all have to agree on optional and repeat params, so we can just advance
        # indx till we hit tok
        sopPs:list[A.AstNode] = [] # put values for next sop here (might be repeating)
        while True:
            # come back here till past this sop (token != sop, or got 1 and not repeating)
            nextSopText = oiL[0].subops[indx].subop
            nextSopOccurs = [oiL[i].subops[indx].occur for i in range(len(oiL))]
            nextSopvparams = [oiL[i].subops[indx].param for i in range(len(oiL))]
            # If we have an operand, but the sop can't be repeating then this is a new sop even
            # if text the same. This happens when you want a sop to occur 1 or more times.
            if nextSopText!=tok.tT.text or (len(sopPs)==1 and 'repeating' not in nextSopOccurs):
                if len(sopPs)==0 and None in nextSopvparams:
                    oiL = [oiL[i] for i in range(len(oiL)) \
                            if oiL[i].subops[indx].param==None]
                    # nothing to do
                    break
                elif 'mandatory' in nextSopOccurs: # must all be mandatory, see numMandatory
                    assert len(sopPs)==1 and all(oc=='mandatory' for oc in nextSopOccurs)
                    x = U.notNone(oiL[0].subops[indx].param)
                    #assert isinstance(x,op.SSparam)
                    #assert isinstance(x.pos,int)
                    pAstL[x.pos] = sopPs[0] # un tuple it
                else: 
                    if 'repeating' not in nextSopOccurs: # must be optional
                        assert len(sopPs)<2 and all(nso=='optional' for nso in nextSopOccurs)
                    else:
                        assert all(nso in ['optional','repeating'] for nso in nextSopOccurs)
                    pAstL[U.notNone(oiL[0].subops[indx].param).pos] = A.AstTuple(members=tuple(sopPs))
                break # will loop on outer 'while True' - get more missing/optional tokens
            # If we come here then not past the current sop
            # We match the current token. If mandatory then we might have some with a
            # following parameter, and some without. Let's count
            numWithoutParam = sum((1 for i in range(len(oiL))\
                                              if oiL[i].subops[indx].param==None))
            noneOK = numWithoutParam > 0 # we'll disable defaultOperand
            # can't have both noneOK and a param with precedence, because noneOK requires
            # a following subop to demonstrate it, or it is a trailing mandatory.
            precedence = None if noneOK else U.notNone(oiL[0].subops[indx].param).precedence #all same
            p = None # not needed
            # Note that a subop with no parameter must be mandatory and have no subsubs.
            # [check doc FIXME].
            curOpCtx = OpCtx(upOpCtx=opCtx.upOpCtx, indx=indx, altOpInfos=oiL)
            if noneOK or (U.notNone(oiL[0].subops[indx].param).subsubs==None):
                # subsubs absent in one then absent in all
                assert all(oiL[i].subops[indx].param==None or\
                        U.notNone(oiL[i].subops[indx].param).subsubs==None for i in range(len(oiL)))
                p,toks = getExpr(toks=toks,left=None,prio=precedence,opCtx=curOpCtx,noneOK=noneOK)
                if p!=None:
                    oiL = [oiL[i] for i in range(len(oiL)) if oiL[i].subops[indx].param!=None]
                    myAdjust = U.notNone(oiL[0].subops[indx].param).oneAdjust
                    assert myAdjust is None or isinstance(myAdjust,A.AstNode)
                    p = opFunAst(myAdjust, p) # ??
                else:
                    # we assume that a param with no operand can't have subsubs -- document FIXME
                    oiL = [oiL[i] for i in range(len(oiL)) if oiL[i].subops[indx].param==None]
            else: # get subsubs, which must be all the same
                #oiL = [oiL[i] for i in range(len(oiL)) if oiL[i].subops[indx].param!=None]
                assert len(oiL)==1 or all(U.notNone(oiL[0].subops[indx].param).subsubs==\
                        U.notNone(oiL[i].subops[indx].param).subsubs for i in range(1,len(oiL)))
                ssOpInfo = op.OpInfo(p, oiL[0].subops[indx].allAdjust, \
                                     oiL[0].subops[indx].param.ssParamLen, \
                                     oiL[0].subops[indx].param.subsubs ) # faked up OpInfo
                ssOpCtx = OpCtx(upOpCtx=opCtx, indx=0 ,altOpInfos=[ssOpInfo]) # only 1 OpInfo
                oi,pl,toks = getSubops(toks,ssOpCtx) # looks wrong???
                assert oi==ssOpInfo # what else?
                myAAdjust = U.notNone(oiL[0].subops[indx]).allAdjust
                assert myAAdjust is None or isinstance(myAAdjust,A.AstNode)
                p = opFunAst(myAAdjust,A.AstTuple(members=pl))
            if p!=None: 
                sopPs.append(p)
            tok = next(toks)
            # end inner while True
        indx = indx+1
        if indx==len(oiL[0].subops): # at end
            assert len(oiL)==1
            return oiL[0],U.noNones(pAstL[:oiL[0].paramLen]),U.prependGen(tok,toks)
        # end outer while True

#class FakeAstClosure(A.AstClosure):
#    def __init__(self,builtins:dict[str,A.AstIdentifier]):
#        self.myIds = {k:[] for k,_ in builtins.items()}
#        self.extIds = {}

import interp as I
# Since we call getExpr with no left, must start with a noLeft op, presumably !!SOF
def compiler(toks:ca.Generator[L.Token,None,None])->A.AstClosure:
    doKCTcmd('operator "A.AstTuple" ["!!defaultOperand"]',L.delimToken)
    doKCTcmd('operator "None" ["!!SOF"] ["!!EOF"]',L.delimToken)
    doKCTcmd('operator "None" ["!!SOF"] () ["!!EOF"]',L.delimToken)
    #opCtx = OpCtx(upOpCtx=None,indx=0,altOpInfos=[])
    e,toks = getExpr(toks=toks,left=None,prio=None,opCtx=None,noneOK=False) # type: ignore
    assert e is not None
    c = A.AstClosure(e)
    #c.fixUp(parent=None,closure=I.FakeClosure,upChain=()) # will fixup e as well
    return c

import sys

if __name__=="__main__":
    #import lexer
    global ast
    global debug
    debug = len(sys.argv)>2
    ast = compiler(L.lexer(sys.argv[1])) # type: ignore
    for l in ast.pp(1): print(l)
    #print( I.interp(ast,debug).pp())
