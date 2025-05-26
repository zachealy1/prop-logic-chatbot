import re
import itertools
from sympy.logic.inference import satisfiable
from sympy import to_cnf as sympy_to_cnf
from sympy.logic.boolalg import And, Or, Not, false
from sympy.parsing.sympy_parser import parse_expr
from sympy import Implies, Equivalent

# our global knowledge base: a list of Sympy expressions
knowledge_base = []

def parse_formula(text: str):
    """
    Parse a propositional‐logic string into a Sympy Boolean expression,
    mapping our keywords to the right Sympy constructors.
    """
    t = text.strip()

    # map infix keywords to symbols/operators
    t = re.sub(r'\bimplies\b',    '>>',  t)
    t = re.sub(r'\band\b',        '&',   t)
    t = re.sub(r'\bor\b',         '|',   t)
    t = re.sub(r'\bnot\s+',       '~',   t)

    # handle “iff” by turning it into an Explicit call
    if 'iff' in t:
        left, right = t.split('iff', 1)
        t = f"Equivalent({left.strip()}, {right.strip()})"
    # now parse a valid Python expression
    return parse_expr(
        t,
        local_dict={ 'Implies': Implies, 'Equivalent': Equivalent }
    )

def format_formula(expr) -> str:
    """
    Recursively turn a Sympy BoolExpr into a nicely spaced infix string:
      - uses => for Implies, <=> for Equivalent
      - & for And, | for Or
      - ~ for Not (unary), with a space before.
      - wraps non-atomic args in parentheses with spaces.
    """
    # atomic symbol
    if expr.is_Symbol:
        return expr.name

    # negation
    if expr.func is Not:
        inner = format_formula(expr.args[0])
        # if inner is compound, keep its parentheses
        return f"~{inner}"

    # binary connectors
    if expr.func is Implies:
        a, b = expr.args
        left = format_formula(a)
        right = format_formula(b)
        # wrap right in parens if it's compound
        if not b.is_Symbol and b.func is not Not:
            right = f"( {right} )"
        return f"{left} => {right}"

    if expr.func is Equivalent:
        a, b = expr.args
        left = format_formula(a)
        right = format_formula(b)
        if not b.is_Symbol and b.func is not Not:
            right = f"( {right} )"
        return f"{left} <=> {right}"

    if expr.func is And or expr.func is Or:
        op = " & " if expr.func is And else " | "
        parts = []
        for arg in expr.args:
            s = format_formula(arg)
            # if the arg is itself an And/Or of multiple terms, or an implication, wrap it
            if arg.func in (And, Or, Implies, Equivalent) and len(arg.args) > 1:
                parts.append(f"( {s} )")
            else:
                parts.append(s)
        return op.join(parts)

    # fallback
    return str(expr)

def handle_message(message: str):
    """
    Parse a single line of user input and call the appropriate chatbot function.
    Returns:
      - A string response to print, or
      - None if the user typed 'exit' (so the main loop can quit).
    """
    msg = message.strip()

    # exit
    if msg.lower() == 'exit':
        return None

    # truth table: <formula>
    if msg.startswith('truth_table:'):
        formula = msg[len('truth_table:'):].strip()
        return truth_table(formula)

    # tell: <formula>
    if msg.startswith('tell:'):
        formula = msg[len('tell:'):].strip()
        return tell(formula)

    # ask: <formula>
    if msg.startswith('ask:'):
        formula = msg[len('ask:'):].strip()
        return ask(formula)

    # list_kb or list kb
    if msg in ('list_kb', 'list kb'):
        return list_kb()

    # modus_ponens: <premise>; <implication>
    if msg.startswith('modus_ponens:'):
        rest = msg[len('modus_ponens:'):].strip()
        parts = rest.split(';')
        if len(parts) != 2:
            return "Invalid syntax. Use: modus_ponens: <premise>; <implication>"
        premise, implication = parts[0].strip(), parts[1].strip()
        return modus_ponens(premise, implication)

    # resolution: <clause1>; <clause2>
    if msg.startswith('resolution:'):
        rest = msg[len('resolution:'):].strip()
        parts = rest.split(';')
        if len(parts) != 2:
            return "Invalid syntax. Use: resolution: <clause1>; <clause2>"
        c1, c2 = parts[0].strip(), parts[1].strip()
        return resolution(c1, c2)

    # convert_to_cnf: <formula>
    if msg.startswith('to_cnf:'):
        formula = msg[len('to_cnf:'):].strip()
        return convert_to_cnf(formula)

    # nothing matched
    return "Unknown command. Please use tell:, ask:, list_kb, modus_ponens:, resolution:, to_cnf: or exit."

def tell(formula_str: str) -> str:
    """
    Implements the `tell:` command.
    Returns:
     - "I already know that"
     - "I do not believe that"
     - "I've learned something new"
    """
    p = parse_formula(formula_str)
    # make a single conjunction of everything in the KB (True if empty)
    kb_conj = And(*knowledge_base) if knowledge_base else True

    # 1) already entails p?
    #    KB entails p  <=>  KB ∧ ¬p is unsatisfiable
    if not satisfiable(And(kb_conj, Not(p))):
        return "I already know that"

    # 2) would contradict: KB ∧ p unsatisfiable?
    if not satisfiable(And(kb_conj, p)):
        return "I do not believe that"

    # 3) otherwise it’s new and consistent
    knowledge_base.append(p)
    return "I've learned something new"

def ask(formula_str: str) -> str:
    """
    Implements the `ask:` command.
    Returns:
      - "Yes" if the KB entails the formula
      - "No" if the formula contradicts the KB
      - "I do not know" otherwise
    """
    # parse the user’s input into a Sympy expression
    p = parse_formula(formula_str)

    # build a single conjunction of all known facts (True if KB is empty)
    kb_conj = And(*knowledge_base) if knowledge_base else True

    # 1) KB entails p  <=>  KB ∧ ¬p is unsatisfiable
    if not satisfiable(And(kb_conj, Not(p))):
        return "Yes"

    # 2) p contradicts KB  <=>  KB ∧ p is unsatisfiable
    if not satisfiable(And(kb_conj, p)):
        return "No"

    # 3) otherwise we can’t decide
    return "I do not know"

def list_kb() -> str:
    """
    Implements the `list_kb` (or `list kb`) command.
    Returns a numbered list of all formulas in the KB,
    e.g.,
      1. p => q
      2. p
      3. r & s
    """
    if not knowledge_base:
        return "Knowledge base is empty."

    lines = []
    for i, expr in enumerate(knowledge_base, start=1):
        # special‐case the two‐argument operators for nicer infix
        if expr.func is Implies:
            a, b = expr.args
            rep = f"{a} => {b}"
        elif expr.func is Equivalent:
            a, b = expr.args
            rep = f"{a} <=> {b}"
        else:
            # default sympy pretty‐printing for And, Or, Not, etc.
            rep = str(expr)
        lines.append(f"{i}. {rep}")

    return "\n".join(lines)

def modus_ponens(premise_str: str, implication_str: str) -> str:
    """
    modus_ponens: <premise>; <implication>
    e.g. modus_ponens("p", "p implies q") -> "applied modus ponens and learned: q"
    """
    p = parse_formula(premise_str)
    q = parse_formula(implication_str)

    # ensure q is an implication
    if q.func is not Implies:
        return "Error: second argument must be an implication."

    antecedent, consequent = q.args

    # ensure the premise matches the antecedent
    if p != antecedent:
        return f"Error: premise {p!s} does not match implication antecedent {antecedent!s}."

    # now learn the consequent
    res = tell(str(consequent))
    if res == "I've learned something new":
        return f"applied modus ponens and learned: {consequent}"
    elif res == "I already know that":
        return f"applied modus ponens but I already know that: {consequent}"
    else:  # "I do not believe that"
        return f"I do not believe that: {consequent}"


def resolution(clause1_str: str, clause2_str: str) -> str:
    """
    resolution: <clause1>; <clause2>
    e.g., resolution("p or r", "not p or s") -> "applied resolution and learned: r | s"
    """
    c1 = parse_formula(clause1_str)
    c2 = parse_formula(clause2_str)

    def literals(cl):
        return list(cl.args) if cl.func is Or else [cl]

    lits1 = literals(c1)
    lits2 = literals(c2)

    for e1 in lits1:
        for e2 in lits2:
            if e1 == Not(e2) or Not(e1) == e2:
                # form the union of the remaining literals
                new_list = [x for x in lits1 if x != e1] + [x for x in lits2 if x != e2]

                # dedupe while preserving order
                uniq = []
                for x in new_list:
                    if x not in uniq:
                        uniq.append(x)

                # build the resolvent clause, using Sympy's false for the empty clause
                if not uniq:
                    resolvent = false
                elif len(uniq) == 1:
                    resolvent = uniq[0]
                else:
                    resolvent = Or(*uniq)

                # direct syntactic insert
                if resolvent not in knowledge_base:
                    knowledge_base.append(resolvent)
                    return f"applied resolution and learned: {resolvent}"
                else:
                    return f"applied resolution but it's already in the KB: {resolvent}"

    return "No complementary literals found; resolution not applicable."

def convert_to_cnf(formula_str: str) -> str:
    """
    Implements the `to_cnf:` command.
    Returns two lines:
      original formula: <parsed>
      converted to CNF: <cnf form>
    """
    # 1. parse the user’s input into a Sympy expression
    p = parse_formula(formula_str)

    # 2. convert it into conjunctive normal form
    #    simplify=True applies basic simplifications like flattening
    cnf_form = sympy_to_cnf(p, simplify=True)

    orig_str = format_formula(p)
    cnf_str = format_formula(cnf_form)

    # 3. format the two‐line response
    return f"original formula : {orig_str}\nconverted to CNF : {cnf_str}"

def truth_table(formula_str: str) -> str:
    """
    Generate a truth table for the propositional formula.
    Returns a multi‐line string like:

      p | q | p & q
      0 | 0 | 0
      0 | 1 | 0
      1 | 0 | 0
      1 | 1 | 1
    """
    p = parse_formula(formula_str)
    # get the propositional symbols, sorted by name for consistency
    symbols = sorted(p.free_symbols, key=lambda s: s.name)

    # build header row
    header = " | ".join(str(v) for v in symbols + [p])
    lines = [header]

    # iterate over all 2^n assignments
    for assignment in itertools.product([False, True], repeat=len(symbols)):
        env = dict(zip(symbols, assignment))
        # evaluate p under this assignment
        val = bool(p.subs(env))
        # build one row: 0/1 for each var, then for p
        row = " | ".join(str(int(env[v])) for v in symbols) + " | " + str(int(val))
        lines.append(row)

    return "\n".join(lines)
