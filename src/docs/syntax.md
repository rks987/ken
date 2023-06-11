I plan to separate out the operator system so others can use it. This is mostly
taken from the README of that project. 
# Super Simple Syntax
The objective of SSS (super simple syntax) was to allow, in a programming language, 
user defined operators that were sufficiently powerful that the programming 
language would not need much builtin syntax at all. So this includes multi token 
operators such as if-then-else, and includes optional and repeating subgroups and 
subsub groups.

## Overview
Suppose we want a standard notation for lists: square brackets with
- either a comma separated sequence of values, or
- `[ hd | tl ]` to represent prepending `hd` to `tl` (commonly used to unpack a list).

In SSS we need to define 3 operators:
- `[ ]` for the empty list;
- `[ 1, 2, 3 ]` has a required operand, then a "`, x`" repeating group;
- `[ 1 | [2,3] ]` defines a different operator because the `|` is not `,` or `]`. 

In SSS terminology: `[`, `,`, `|` and `]` are called suboperators. Suboperators 
are one of: mandatory, optional, or repeating (0 or more times). If you want 
repeating one or more times then just have the first occurrence as mandatory 
then a repeating group. The first suboperator is, of course, mandatory. 

Before the first suboperator, and then after each suboperator, there is a 
slot for an operand. Before the first suboperator and after each mandatory 
suboperator we can specify that an operand is required or not permitted, 
and we can distinguish operators based on this. In the simplest case, the 
minus in `( - 3 )` is a different operator from the minus in `( 7 - 3 )`. We 
saw above that `[ ]` is a different operator from `[ 1 ]`.

So our operator is defined by the sequence of `n` mandatory suboperators, 
plus the boolean for each of the `n+1` operand positions saying whether an 
operand is required or forbidden in that position for that operator.
### Precedence
A left operand and any operand which might be rightmost (since there is 
no following mandatory suboperator) will have a precedence. A precedence 
is just a decimal number that is only used for its ordering, as with the 
Dewey decimal library system. In the expression `1 + 2 * 3` the right 
precedence of `+` and the left precedence of `*` will determine which 
gets the `2` and which has to wait. But this also applies with just one 
operator: `1 * 2 * 3` will associate to left or right depending on whether 
the left precedence of `*` is higher or lower than the right.

If a left precedence is omitted then it is taken as minimum and if a
right precedence is omitted it is taken as maximum. This gives a default
of associating to the left.
### Subsubs
A common convention in programming languages is to write `i,j,k:Int`. 
This is something you can't do with SSS because you don't know what 
comma means till you get to the `:`. Backtracking is not allowed. So, 
in my language, I have to write `i:,j:,k:Int`. What's happening here is 
that the `:` operator has a (0 or more) repeating group: `, operand :`. 
This is called a subsub.

The main use of subsubs is when you have an optional (or repeated) 
suboperator, and there are other things that must or might go along 
with it when it is present. In the case above the subsub only adds 
the `:`s that are there for syntactic reasons. In the operator spec, 
if the subsub comes before the operand (or there's no operand) then 
its spec goes in with the suboperator, if after the operand it goes in 
with the operand spec.

Of course subsubs can have subsubsubs ...
### Identifiers and constants
As we saw with brackets, `[ ]`, an operator might have no left or 
right operand. Identifiers and constants fit into this operator 
scheme as just operators with no left or right. They don't need special 
handling.
### Special suboperators
When an operator with no right is followed by one with no left then a 
special suboperator is created. It will be "juxtaposition" is there is 
no whitespace, as in `f(x)`, or "space" is there is an actual gap. 
In my language procedure calls use either of 
these as infix operators: `f(x)` or `f x`.

To keep track of indentation for use as suboperators, the lexical scan
that delivers the tokens can generate special tokens representing
changes in indentation. If there is a reduction in indentation by two
levels then this should be delivered as two separate tokens.
### Default operand
When an operand is required but not found then a default operand can 
be inserted. Typically, in modern programming languages, this will be `unit`, 
which is a 0-tuple, which can thus be written `()`.
### Adjacent suboperators
The left suboperator might have: (1) only a no-right; (2) only a with-right;
(3) 2 operators matching to that point, one with-right and one no-right.
Similarly the right suboperator might have: (1) only a no-left; (2) only a 
with-left; (3) 2 operators starting that way, one with-left and one no-left.
- If no-right meets no-left then we insert a space or juxtaposition operator.
- If with-right meets with-left then precedence decides.
- If one is with- and the other no-, then the one that wants a
partner takes the other. This applies when one has 2 options and the
other only has 1 option. The one with 1 option forces the other to
be the opposite.
- When both have 2 options then the left gets the with-right and the
right is forced into the no-left option. A warning should perhaps be
issued and there should be some way for the library to suggest this to the
using code.
## The Gory Details
Operator declarations occur, hopefully before they are needed, then 
a stream of tokens is processed according to the operator specifications, 
building an AST, Abstract Syntax Tree. Your program will then do something 
useful with that.

The tokens are just text in SSS. If you want tokens with more complex 
structure then you could modify the code, but the easy answer is to just 
encode the structure in text, as I do. I prefix the text with a single 
character saying what sort of token it is, which is good enough for my 
application. However, for clarity, in the examples here I will just 
show incoming text. Also, any token that is not on the current list of 
possible suboperators will be treated as an identifier or constant, 
which is an operator with no left or right for syntactic purposes.
### Specifying operators
In all the following, when I say "quoted text" I mean: in double 
quotes and, if `"` or backslash is required in the text then precede 
it with a backslash.

An operator specification consists of:
1. A value to tell the AST building code what to do with the operands. 
For example it might say what function to apply to them.
2. A text specification of the sequence of suboperators and operands.

The latter specification consists of suboperator and operand information, 
with no consecutive operand specifications:
1. An operand spec is in parentheses (`()`) and has the following:
- Optional precedence decimal number. Required for a left operand or 
an operand with no following mandatory suboperator.
- Optional subsub, which is just the same as our operator spec, except 
that it has to start with a suboperator spec (in `[]`s). This can only 
occur if the prior (controlling) suboperator is optional or repeating.
2. A suboperator spec is in square brackets (`[]`) and has the following:
- The quoted text of the suboperator. If the text is `""` it is the juxtaposition 
suboperator, and if it is `" "` it is the whitespace suboperator.
- Optional occurrence specification: mandatory|optional|repeating. Default 
is mandatory.
- Optional subsub. Normally subsubs would go in the operand spec and
specify what may or must follow that operand. A subsub in the suboperator
spec is for suboperators and operands that go between the suboperator
and its associated operand. This can only be used when the suboperator has
a following operand, and all options in the subsub must end in a suboperator
with no following operand.

There are compatibility constraints. 
- If multiple operators start with the same suboperator, and they have a 
left, then those lefts have to have the same precedence.
- More generally operators are determined by their mandatory suboperators 
and associated operands, and until those diverge they have to agree.
- ...

### Example Operators
`(999) [":" mandatory ["," repeating] () [":"]] (50)` matches `i:Int` or 
`i:,j:,k:Int`.  Note that we have 
a high precedence on the left which will capture single identifiers, but a
low precedence on the right to allow type specifications without putting them
in parentheses.

`(200) [","] (200) ["," repeating] (200)` matches `1,2,3`. The second comma comes 
from a repeating group. Because that is a defined possibility, the parser 
doesn't consider the possibility of it being an initial comma of this operator.

`["("] () [")"]` matches `(anyexpression)` and, of course, just returns its
inner expression unchanged.

`(10) [";"] (9)` matches `statement ; expression`. It doesn't matter in this case
if we make it associate to right or left, but it has to do one or other.

### API
`sssInit(tokenStream,astCallback,errorCallback)` to start:
- `tokenStream` is a generator of tuples consisting of:
  - a token (just text);
  - a whitespace boolean, being true if there is whitespace after this token
and false if the lexical scan has found a token break without whitespace; 
  - an opaque value that will be passed to the errorCallback, and might 
contain information like the filename, line number and character position.
- `astCallback(operator,operands)` is a routine that will be called whenever
an operator instance is complete. It will return an opaque value (presumably 
an ast tree) that will be
the data when that bit of ast is an operand in an outer operator instance. The 
operands come in a list as described later.
- `errorCallback(msg,partAst,token)` will be called when an error 
occurs, providing an error
message, the partial ast that can't be finished, the current token. If the
error callback returns then it will return a tuple of: a possibly modified
partial AST, plus a new token generator. E.g. it could prepend some tokens
as well as the token that annoyed SSS.

`doOperatorCmd(operator,specification)` is called to define operators. The 
`operator` parameter is an opaque value that is passed to `astCallback`. The
`specification` is text defining the operator syntax, as described previously.

The `doOperatorCmd` can be called before ever calling `sssInit`. However
if you want to have user defined operators then you can call `doOperatorCmd`
at any time. It will, of course, only apply to following tokens. Behaviour
is currently undefined if the operator being defined partially overlaps with an
existing operator whose operand is being processed. This is avoided by
only allowing operator definitions at "statement level" in some sense, e.g.
after a semicolon (`;`) operator in traditional style programming languages.
### Operands
The `operands` parameter to `astCallback` is simple:
- The operands form a list, even if there is one or zero operands. The list 
is in the order of the operands in the specification. This includes dummy operands, 
represented by an empty list, for suboperators other than mandatory that have 
no following operand.
- Mandatory operands (either left, or following a mandatory suboperator) are 
just in the list as is.
- Repeating operands are in a list or zero or more.
- Optional operands are in a list of zero or one.
- Subsubs are a list, being the same as the operands list.