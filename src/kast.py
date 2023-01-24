# kast.py supports the Ken ast
#
#import typing as T
#import abc # abstract base class
import operator, functools
import kprimitive as P

def ppFix(lines:list[str],indent:int)->list[str]: # squeeze to one line if convenient
    if sum((len(l)-indent) for l in lines) < 40:
        return [' '*indent+functools.reduce(operator.add,(l.lstrip().rstrip()+' ' for l in lines))]
    return lines

class AstNode:
    def __init__(self,parent:'AstNode'|None=None,closure:'AstClosure'|None=None):
        self.parent = parent   # up a level
        self.closure = closure # closure we're in (None for top level)
        self.fixed:bool = False
    def fixUp(self,parent:'AstNode'|None,closure:'AstClosure'|None,upChain:tuple['AstNode',...])->None:
        # override fixUp if have subexpressions
        if self.fixed:
            pass #assert False
        self.fixed = True
        self.parent = parent
        self.closure = closure
        assert self not in upChain
        self.upChain:tuple[AstNode,...] = upChain
        #return self
    def gotClRslt(self)->bool:
        return False # default
    def __str__(self)->str:
        assert False # must be overridden
    def pp(self,indent:int=1): # return a list of strings
        return [(' '*indent) + self.__str__()] # default

class AstTuple(AstNode):
    def __init__(self,members:tuple[AstNode,...],parent:AstNode|None=None,closure:'AstClosure'|None=None):
        #self.members = (members,) if isinstance(members,AstNode) else members
        self.members = members
        #assert isinstance(members,tuple)
        super().__init__(parent,closure)
    def __str__(self)->str:
        if self.members==(): return '()'
        rslt = '('
        for x in self.members: rslt = rslt+x.__str__()+','
        return rslt[:-1]+')'
    def gotClRslt(self)->bool:
        return any(e.gotClRslt() for e in self.members)
    def pp(self,indent:int=1): 
        if self.members==():
            return [(' '*indent)+'()']
        elif len(self.members)==1:
            return ppFix([(' '*indent)+'BOX('] + \
            self.members[0].pp(2+indent) + \
            [(' '*indent)+')' ],indent)
        else:
            mppl = [m.pp(indent+1) for m in self.members]
            for i in range(len(mppl)-1): mppl[i][-1] += ' ,'
            return ppFix([(' '*indent)+'('] + \
            functools.reduce(operator.add, mppl) + \
            [(' '*indent)+')'],indent)
            def fixUp(self,parent:Opt[AstNode],closure:Opt[AstClosure],upChain:List[AstNode])->None:
                super().fixUp(parent,closure,upChain)
            for x in self.members: x.fixUp(self,closure,self.upChain+(self,))
        #return self

def zeroTuple()->AstTuple:  # is Unit.unit = defaultOperand in wombat
    return AstTuple(members=()) 

#class AstDiscard(AstNode):
#    def __init__(self,parent=None,closure=None):
#        super().__init__(parent,closure)
#    def __str__(self):
#        print('_')

#def toDiscard(x):
#    return AstDiscard()

def toClosure(exprL:list[AstNode])->'AstClosure': # param is 1-elt list with closure expr as the 1 elt
    assert len(exprL)==1 and isinstance(exprL[0],AstNode)
    return AstClosure(expr=exprL[0])

class AstClosure(AstNode):
    def __init__(self,expr:AstNode,parent:AstNode|None=None,closure:'AstClosure'|None=None):
        super().__init__(parent,closure)
        self.expr = expr
        self.myIds:dict[str,list['AstIdentifier']] = {}
        self.extIds:dict[str,list[AstClosure]] = {}
        # need to make sure there is an AstClRslt
        if not self.expr.gotClRslt():
            # FIXME not the right way to do this, but ok for interp where equal is builtin
            eqProcParam = AstTuple((AstIdentifier("equal"),AstTuple((AstClRslt(),self.expr))))
            self.expr = AstCall(eqProcParam)
    def __str__(self)->str:
        return '{'+self.expr.__str__()+'}'
    def pp(self,indent:int=1):
        return ppFix([' '*indent+'{'] + self.expr.pp(indent+2) + [(' '*indent)+'}'], indent)
    def fixUp(self,parent:AstNode|None,closure:'AstClosure'|None,upChain:tuple[AstNode,...])->None:
        super().fixUp(parent,closure,upChain)
        self.expr.fixUp(self,self,upChain+(self,)) # I am up and closure
        for idn in self.extIds:
            assert closure
            if idn not in closure.extIds and idn not in closure.myIds:
                closure.extIds[idn] = [self]
            elif idn in closure.extIds:
                closure.extIds[idn].append(self)
            else:
                closure.myIds[idn].append(self) #???
        pass #return self

class AstClParam(AstNode): # i.e. $
    def __init__(self,parent:AstNode|None=None,closure:AstClosure|None=None):
        super().__init__(parent,closure)
    def __str__(self)->str:
        return '$'

class AstClRslt(AstNode): # i.e. `$
    def __init__(self,parent:AstNode|None=None,closure:AstClosure|None=None):
        super().__init__(parent,closure)
    def gotClRslt(self)->bool:
        return True
    def __str__(self)->str:
        return '`$'

class AstIdentifier(AstNode):
    def __init__(self,identifier:str,parent:AstNode|None=None,closure:AstClosure|None=None):
        super().__init__(parent,closure)
        self.identifier = identifier
    def fixUp(self,parent:AstNode|None,closure:AstClosure|None,upChain:tuple[AstNode,...])->None:
        super().fixUp(parent,closure,upChain)
        idn = self.identifier
        if idn in closure.myIds:
            closure.myIds[idn].append(self) # no known use of this?
        else:
            if idn not in closure.extIds:
                closure.extIds[idn] = [self]
            else:
                closure.extIds[idn].append(self)
    def __str__(self)->str:
        return self.identifier+' '

class AstNewIdentifier(AstNode):
    def __init__(self,identifier:str,parent:Opt[AstNode]=None,closure:Opt[AstClosure]=None)->None:
        super().__init__(parent,closure)
        self.identifier = identifier
    def fixUp(self,parent:Opt[AstNode],closure:Opt[AstClosure],upChain:List[AstNode])->None:
        super().fixUp(parent,closure,upChain)
        idn = self.identifier
        assert idn not in closure.myIds #and idn not in closure.extIds
        closure.myIds[idn] = [self] # defining use is first in list
    def __str__(self)->str: 
        return '`'+self.identifier+' '

class AstFreeVariable(AstNode):
    def __init__(self,identifier:str,parent:Opt[AstNode]=None,closure:Opt[AstClosure]=None)->None:
        super().__init__(parent,closure)
        self.identifier = identifier
    def __str__(self)->str: 
        return '_'+self.identifier+' '

class AstNewFreeVariable(AstNode):
    def __init__(self,identifier:str,parent:Opt[AstNode]=None,closure:Opt[AstClosure]=None)->None:
        super().__init__(parent,closure)
        self.identifier = identifier
    def __str__(self)->str:
        return '`_'+self.identifier+' '

class AstCall(AstNode):
    def __init__(self,procParam:AstTuple,parent:Opt[AstNode]=None,closure:Opt[AstClosure]=None)->None:
        super().__init__(parent,closure)
        self.procParam = procParam
    def __str__(self)->str:
        return 'CALL'+self.procParam.__str__() # ugly
    def funct(self)->AstNode:
        return self.procParam.members[0]
    def param(self)->AstNode:
        return self.procParam.members[1]
    def pp(self,indent=1):
        f = self.funct().pp(indent)
        f[-1] += '('
        return ppFix(f+self.param().pp(indent+2)+[(' '*indent)+')'], indent)
    def fixUp(self,parent:Opt[AstNode],closure:Opt[AstClosure],upChain:List[AstNode])->None:
        super().fixUp(parent,closure,upChain)
        self.procParam.fixUp(self,closure,self.upChain+(self,))
    def gotClRslt(self)->bool:
        return self.procParam.gotClRslt()

def callOp(procAndParam:tuple[AstNode,AstNode])->AstCall:
    return AstCall(procParam=AstTuple(members=procAndParam))

# These constants are really wombat not marsupial. FIXME
# maybe can be Mct"ConstType".fromString(const)
class AstConstant(AstNode):
    def __init__(self,const:str,constType:str,paren:Opt[AstNode]=None,closure:Opt[AstClosure]=None)->None:
        super().__init__(parent,closure)
        self.const = const
        self.constType = constType
    def __str__(self):
        return self.const+' ' # FIXME - only right for numbers

class AstPrim(AstNode):
    def __init__(self,primVal:P.PvRun,parent:Opt[AstNode]=None,closure:Opt[AstClosure]=None)->None:
        super().__init__(parent,closure)
        self.primVal = primVal
    def __str__(self):
        return self.primVal.__str__()

def first2rest(tupNodeOrList): #typing???
    if tupNodeOrList == None: return None # for luck
    # commonly we have the 1st param seperated where it logically
    # belongs in with the list of following ones (e.g. comma operator)
    if isinstance(tupNodeOrList, AstTuple):
        return AstTuple(members=first2rest(tupNodeOrList.members))
    # assume is a 2 entry list whose 2nd entry is a list or AstTuple
    if isinstance(tupNodeOrList[1], AstTuple):
        return (tupNodeOrList[0],)+tupNodeOrList[1].members
    return (tupNodeOrList[0],)+tupNodeOrList[1]


if __name__=="__main__":
    pass
