# cttypes.py -- compile time types

import typing
#import khierarchy as H
import lenses as L
import collections.abc as ca
#import kast as A
import kprimitive as P
#import interp as I
import decimal as D
import utility as U

# We treat base types as if families but with index set to None.
# so these are :Type, families are :IndxType=>Type

# The types and parameters are:
#    Decimal  (None)              type of numeric constant e.g. 3.14
#    Nat      (None)              unlimited positive integers
#    Tuple    (List Type)
#    Proc     (Tuple(Type,Type))  X=>Y
#    Union    (Set Type)
#    Set      (Type)
#    Option   (Type)              Option(X)=DisjointUnion`[Unit Tuple(X)]
#    List     (Type)              List(X)=Option(Tuple[X List(X)]) ???

# A lot of this should be separated out into a general types module

# For the moment a base type is just a family with index set to None
# And all types/families are primitive

from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class Mfamily:
    txt : str
    famObj : P.TFam
    indxType : 'MtVal'|None #could use Unit=Tuple() for base types??

# tMindx is None (for base type) or some value of type .tMfamily.indxType
@dataclass(frozen=True,slots=True)
class MtVal: 
    tMfamily:Mfamily
    tMindx:'MtVal'|tuple['MtVal',...]|None # should use Unit for index if base type ??? FIXME
    tMsubset: tuple[typing.Any,...]|None # a .value for types

def getMtMiTuple(tmi:MtVal|tuple[MtVal,...]|None)->tuple[MtVal,...]:
    assert tmi
    assert not isinstance(tmi,MtVal)
    return tmi

# sometimes we want the type without any subset
def tNoSub(t:MtVal)->MtVal:
    if t.tMsubset==None: return t
    #if t.tMfamily==mfTuple: return MtVal(mfTuple,tuple(tNoSub(tt) for tt in t.tMindx),None)
    return MtVal(t.tMfamily,t.tMindx,None)

# A value OR might be unknown with type saying what we do know.
# Note .tMindx and .value should not be of this form unless type is Any
@dataclass(frozen=True,slots=True)
class Mval:
    mtVal: MtVal # mtVal is the type, an MtVal
    value: T.Any|None #????

@dataclass(frozen=True,slots=True)
class Mprim:
    txt : str
    runner : T.Any #FIXME

def ppT(x:T.Any,xs:tuple[T.Any,...]=())->str:
    if x in xs:
        return "...."
    #if isinstance(x,I.Et):
    #    return type(x).__name__
    if isinstance(x,Mval):
        return ppT(x.mtVal,xs+(x,))+':'+ppT(x.value,xs+(x,))
    elif isinstance(x,Mfamily):
        return x.txt
    elif isinstance(x,MtVal):
        return ppT(x.tMfamily,xs+(x,))+'('+ppT(x.tMindx,xs+(x,))+')'+ \
                ("" if x.tMsubset==None else ('/'+ppT(x.tMsubset,xs+(x,))))
    elif isinstance(x,ca.Sequence):
        return '['+(','.join(ppT(xi,xs+(x,)) for xi in x))+']'
    elif isinstance(x,Mprim):
        return x.txt
    else: return str(x)

def valToType(v:Mval)->MtVal: # v is an Mval
    valList = (v.value,) if v.value != None else None
    return L.bind(v.mtVal).tMsubset.set(valList) # MtVal(v.mtVal.famObj,v.mtVal.indxType,(v.value,))
def typeWithVal(t:MtVal,v:T.Any|None)->MtVal:
    assert v==None or t.tMsubset==None or (len(t.tMsubset)==1 and vEqual(t,v,t.tMsubset[0]))
    return L.bind(t).tMsubset.set((v,)) if v!=None else t
#def typeToVal(t:MtVal)->Mval:
#    return Mval(t,t.tMsubset[0] if t.tMsubset!=None else None)

# Note that types are values of type Type. So in mfList below, the 2nd
# parameter is mvType meaning that the List family of types is indexed
# by type. In mvListOfType the mvType in the 2nd parameter means that
# the specific Type that this is a list of, is Type.

# there is a type Type, whose values are types 
mfType = Mfamily(txt='Type',famObj=P.mType, indxType=None)
mvtType = MtVal(mfType,None,None)
mvType = typeWithVal(mvtType,mvtType) # Type:Type (missing universe level FIXME)
# mvtType is a type, and other types belong to it, mvType is a specific value
mfList = Mfamily('List',P.mList,indxType=mvtType)
mvtListOfType = MtVal(mfList,mvtType,None)
mfTuple = Mfamily('Tuple',P.mTuple,mvtListOfType)

mfSet = Mfamily('Set',P.mSet,mvtType)
#aSetOfNats = Mval(mfSet,mvDecimal,{Decimal(33),Decimal(77)})
mvtSetOfType = MtVal(mfSet,mvtType,None)
mfUnion = Mfamily('Union',P.mUnion,mvtSetOfType)
#
mfDecimal = Mfamily('Decimal',P.mDecimal,None)
mvtDecimal = MtVal(mfDecimal,None,None)
mfNat = Mfamily('Nat',P.mNat,None)
mvtNat = MtVal(mfNat,None,None)
#mvTtypeNat = MtVal(mfType,None,(mvtNat,))
mVnat = typeWithVal(mvtType,mvtNat)
mfAny = Mfamily('Any',P.mAny,None)
mvtAny = MtVal(mfAny,None,None)
mfEmpty = Mfamily('Empty',P.mEmpty,None)
mvtEmpty = MtVal(mfEmpty,None,None)

# ClosureType = Proc((Any,Any):Tuple([Any Any]:List(Type))
#mvListTwoTypes = Mval(mvtListOfType,(mvtType,mvtType)) # [Type Type] : List Type 
mvtTupleTwoTypes = MtVal(mfTuple,(mvtType,mvtType),None)
mvtUnit = MtVal(mfTuple,(),((),)) # only one value, so set it.
#mvTupleTwoAnys = Mval(mvtTupleTwoTypes,(mvtAny,mvtAny)) # (Any,Any) : Tuple[Any Any]
mfProc = Mfamily('Proc',P.mProc,mvtTupleTwoTypes)
mvtProcAnyAny = MtVal(mfProc,(mvtAny,mvtAny),None)
#mvtProcAnyAny = MtVal(mfProc,mvTupleTwoAnys,None)
mvtClosureT = mvtProcAnyAny

# Any=>Empty isA P=>Q isA Empty=>Any
mvtTopProc = mvtEmptyAny = MtVal(mfProc,(mvtEmpty,mvtAny),None)
mvtBottomProc = mvtAnyEmpty = MtVal(mfProc,(mvtAny,mvtEmpty),None)

#mvListProcAnyAnyAndAny = Mval(mvtTupleTwoTypes,(mvtProcAnyAny,mvtAny))
mvtTupleProcAnyAnyAndAny = MtVal(mfTuple,(mvtProcAnyAny,mvtAny),None)
mvtGenProcParam = mvtTupleProcAnyAnyAndAny

def mvMakeDecimal(d:D.Decimal)->Mval:
    return Mval(typeWithVal(mvtDecimal,d),d)

## statements : Tuple[Discard Any] => Any
#mfDiscard = Mfamily(P.mDiscard,None)
#mvtDiscard = MtVal(mfDiscard,None,None)
#mvListDiscardAny = Mval(mvtListOfType,(mvtDiscard,mvtAny))
#mvtTupleDiscardAny = MtVal(mfTuple,mvListDiscardAny,None)
#mvListTupleDiscardAnyAndAny = Mval(mvtListOfType,(mvtTupleDiscardAny,mvtAny))
#mvTstatements = MtVal(mfProc,mvListTupleDiscardAnyAndAny,None)
#mVstatements = Mval(mvTstatements,P.PvRstatements)

#mVdiscard = Mval(mvtDiscard,P.mDiscard) # value of type Discard -- should it just be unit?

# equal -- _X x _Y => Intersection[_X _Y] -- just Tuple[Any Any]=>Any for moment
#mvListAnyAny = Mval(mvtListOfType,(mvtAny,mvtAny))
mvtTupleTwoAnys = MtVal(mfTuple,(mvtAny,mvtAny),None)
#mvListTwoAnyAndAny = Mval(mvtListOfType,(mvtTupleTwoAnys,mvtAny))
#mvTupleTwoAnyAndAny = Mval(MtVal(mfTuple,mvListTwoAnyAndAny,None),((mvtAny,mvtAny),mvtAny))
mvtProcTwoAnyToAny = MtVal(mfProc,(mvtTupleTwoAnys,mvtAny),None)
mPequal = Mprim('(=)',P.PvRequal)
mvTequal = typeWithVal(mvtProcTwoAnyToAny,mPequal)
mVequal = Mval(mvTequal,mPequal)

# statements : Tuple[Any Any] => Any
mPstatements = Mprim('(;)',P.PvRstatements)
mvTstatements = typeWithVal(mvtProcTwoAnyToAny,mPstatements)
mVstatements = Mval(mvTstatements,mPstatements)

# casePswap -- _X x SemiSet(_X=>_Y) => _Y, but just Tuple[Any List(Proc(Any,Any))]=>Any here
# CHECK THIS FIXME
mvtListProcAnyAny = MtVal(mfList,mvtProcAnyAny,None)
mvtTupleAnyListProcAnyAny = MtVal(mfTuple,(mvtAny,mvtListProcAnyAny),None)
#mvtTupleTupleAnyListProcAnyAnyAndAny = MtVal(mfTuple,(mvtTupleAnyListProcAnyAny,mvtAny),None)
#mvtProc4casePswap = MtVal(mfProc,mvtTupleTupleAnyListProcAnyAnyAndAny,None)
#mvListAnyClosureT = Mval(mvtListOfType,(mvtAny,mvtClosureT))
#mvtTupleAnyClosureT = MtVal(mfTuple,mvListAnyClosureT,None)
#mvListTupleAnyClosureTAndAny = Mval(mvtListOfType,(mvtTupleAnyClosureT,mvtAny))
#mvtTupleTupleAnyClosureTAny = MtVal(mfTuple,mvListTupleAnyClosureTAndAny,None)
#mvTupleTupleAnyClosureTAny = Mval(mvtTupleTupleAnyClosureTAny,(mvtAny,mvtTupleAnyClosureT))
#mvTcasePswap = MtVal(mfProc,mvTupleTupleAnyClosureTAny,None)
mPcasePswap = Mprim('(case)',P.PvRcasePswap)
mvTcasePswap = MtVal(mfProc,(mvtTupleAnyListProcAnyAny,mvtAny),(mPcasePswap,))
mVcasePswap = Mval(mvTcasePswap,mPcasePswap)

# toType -- Any x t:Type => t (t is the Type parameter), but just Tuple[Any Type]=>Any here
# but the Mval will have the required type after. Cf isType
#mvListAnyType = Mval(mvtListOfType,(mvtAny,mvtType))
mvtTupleAnyType = MtVal(mfTuple,(mvtAny,mvtType),None)
#mvListTupleAnyTypeAny = Mval(mvtListOfType,(mvtTupleAnyType,mvtAny))
#mvtTupleTupleAnyTypeAny = MtVal(mfTuple,(mvtTupleAnyType,mvtAny),None)
mvtProcAnyTypeToAny = MtVal(mfProc,(mvtTupleAnyType,mvtAny),None)
mPtoType = Mprim('(:)',P.PvRtoType)
mvTtoType = typeWithVal(mvtProcAnyTypeToAny,mPtoType)
mVtoType = Mval(mvTtoType,mPtoType)

# isType -- Any x t:Type => t (t is the Type parameter), but just Tuple[Any Type]=>Any here
# but the Mval will have the required type after. Cf toType
#mvListAnyType = Mval(mvtListOfType,(mvtAny,mvtType))
#mvtTupleAnyType = MtVal(mfTuple,(mvtAny,mvtType),None)
#mvListTupleAnyTypeAny = Mval(mvtListOfType,(mvtTupleAnyType,mvtAny))
#mvtTupleTupleAnyTypeAny = MtVal(mfTuple,(mvtTupleAnyType,mvtAny),None)
mPisType = Mprim('(::)',P.PvRisType)
mvTisType = typeWithVal(mvtProcAnyTypeToAny,mPisType)
mVisType = Mval(mvTisType,mPisType)

# tuple2list -- Tuple[lt:List(Type)] => List(Union(lt)) // Any => Any
mPtuple2list = Mprim('(t2l)',P.PvRtuple2list)
mvTtuple2list = MtVal(mfProc,(mvtAny,mvtAny),(mPtuple2list,))
mVtuple2list = Mval(mvTtuple2list,mPtuple2list)

# consTuple2list -- Tuple[hd,Tuple[lt:List(Type)]] => List(Union(hd,lt)) // Any => Any
mPconsTuple2list = Mprim('(ct2l)',P.PvRconsTuple2list)
mvTconsTuple2list = MtVal(mfProc,(mvtAny,mvtAny),(mPconsTuple2list,))
mVconsTuple2list = Mval(mvTconsTuple2list,mPconsTuple2list)

# geOrFail -- Nat x Nat => Nat
#mvListTwoNats = Mval(mvtListOfType,(mvtNat,mvtNat))
mvtTupleTwoNats = MtVal(mfTuple,(mvtNat,mvtNat),None)
#mvListTupleTwoNatsNat = Mval(mvtListOfType,(mvtTupleTwoNats,mvtNat))
#mvtTupleTupleTwoNatsNat = MtVal(mfTuple,mvListTupleTwoNatsNat,None)
#mvTupleTupleTwoNatsNat = Mval(mvtTupleTupleTwoNatsNat,((mvtNat,mvtNat),mvtNat))
mPgeOrFail = Mprim('(>=?)',P.PvRgeOrFail)
mvTgeOrFail = MtVal(mfProc,(mvtTupleTwoNats,mvtNat),(mPgeOrFail,))
mVgeOrFail = Mval(mvTgeOrFail,mPgeOrFail)

# starOp -- Nat x Nat => Nat
mPstarOp = Mprim('(*)',P.PvRstarOp)
mvTstarOp = MtVal(mfProc,(mvtTupleTwoNats,mvtNat),(mPstarOp,))
mVstarOp = Mval(mvTstarOp,mPstarOp)

# subtract -- Nat x Nat => Nat
mPsubtract = Mprim('(-)',P.PvRsubtract)
mvTsubtract = MtVal(mfProc,(mvtTupleTwoNats,mvtNat),(mPsubtract,))
mVsubtract = Mval(mvTsubtract,mPsubtract)

# print -- _X => _X
mPprint = Mprim('(print)',P.PvRprint)
mvTprint = MtVal(mfProc,(mvtAny,mvtAny),(mPprint,))
mvTprintDecimal = MtVal(mfProc,(mvtDecimal,mvtDecimal),(mPprint,))
mVprint = Mval(mvTprint,mPprint)


#def unknownAny():
#    return Mval(mfAny,None,None)

# the famAst will mostly be an identifier that is hacked for the moment
#
# 'Decimal'  Decimal
# 'Nat'      Int (? just a value)
# 'Tuple'    ptuple - include unit=0-tuple=() in python
# 'Proc'     EtClosure or ???
# 'Union'    mtype with value
# 'SemiSet'  ?? maybe just a ptuple?
# 'Option'   0 or 1 ptuple
# 'List'     ptuple
# 'Type'     (Mfamily,indx,restrict) # indx==None if Mfamily is base
             # restrict is None, or a list of values

# We also need some isA relations:
# Nat isA Decimal
# A isA B ==> List A isA List B
# Tuple lt1 isA Tuple lt2 whenever all (zip ...) etc
# etc

#  an MtVal is immutable...
def tupleFixUp(t:MtVal)->tuple[bool,MtVal]: # t:MtVal
    if t==mvtEmpty: return False,t
    assert t.tMfamily.famObj == P.mTuple
    subs = tuple(fixIfTuple(getMtMiTuple(t.tMindx)[i]) for i in range(len(getMtMiTuple(t.tMindx))))
    if t.tMsubset!=None:
        tupv = t.tMsubset[0] # only single elt subsets allowed
        if all(subs[i].tMsubset!=None and U.notNone(subs[i].tMsubset)[0]==tupv[i]
                for i in range(len(subs))):
            return False,t
        assert all(subs[i].tMsubset==None or U.notNone(subs[i].tMsubset)[0]==tupv[i]\
                for i in range(len(subs)))
        return True,L.bind(t).tMindx.set(tuple(
            typeWithVal(subs[i],tupv[i]) for i in range(len(subs))))
    # Only handle case where tMsubset has 1 element FIXME
    # t.tMindx is an MVal for List(Type).
    for tt in subs:
        if tt.tMsubset==None: return False,t
    #if all (tt.tMsubset!=None for tt in subs):
    newtMsubset = (tuple(U.notNone(tt.tMsubset)[0] for tt in subs),)
    return True,L.bind(t).tMsubset.set(newtMsubset) # MtVal(t.tMfamily,t.tMindx,newtMsubset)

def fixIfTuple(t:MtVal)->MtVal:
    if t.tMfamily.famObj!=P.mTuple: return t
    return tupleFixUp(t)[1]

def vEqual(t:MtVal,v1:T.Any,v2:T.Any)->bool: # check equality of .value for type t
    if v1==v2: return True
    if t in [mvtDecimal,mvtNat]: return v1==v2 # only False, because of previus line
    # probably there aren't any Any values actually
    if t==mvtAny: return v1.mtVal==v2.mtVal and vEqual(v1.mtVal,v1.value,v2.value)
    if t.tMfamily==mfList:
        assert isinstance(t.tMindx, MtVal)
        return len(v1)==len(v2) and all(vEqual(t.tMindx,v1[i],v2[i]) for i in range(len(v1)))
    if t.tMfamily==mfTuple: # .tMindx is List Type
        assert t.tMindx is not None and not isinstance(t.tMindx,MtVal)
        return len(t.tMindx)==len(v1)==len(v2) and all(vEqual(t.tMindx[i],v1[i],v2[i]) 
                                                       for i in range(len(v1)))
    assert False # don't think we need other cases yet FIXME

if __name__=="__main__":
    pass
