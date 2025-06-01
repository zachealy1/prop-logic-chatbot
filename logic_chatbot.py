import re
import itertools
from sympy.logic.inference import satisfiable
from sympy import to_cnf as sympy_to_cnf
from sympy.logic.boolalg import And, Or, Not, false
from sympy.parsing.sympy_parser import parse_expr
from sympy import Implies, Equivalent

# the global knowledge base: a list of Sympy expressions
knowledge_base = []


def parse_formula(text: str):
    """
    Parse a propositional‐logic string into a Sympy Boolean expression,
    mapping our keywords to the right Sympy constructors.
    """
    t = text.strip()

    # map infix keywords to symbols/operators
    t = re.sub(r'\bimplies\b', '>>', t)
    t = re.sub(r'\band\b', '&', t)
    t = re.sub(r'\bor\b', '|', t)
    t = re.sub(r'\bnot\s+', '~', t)

    # handle “iff” by turning it into an Explicit call
    if 'iff' in t:
        left, right = t.split('iff', 1)
        t = f"Equivalent({left.strip()}, {right.strip()})"
    # now parse a valid Python expression
    return parse_expr(
        t,
        local_dict={'Implies': Implies, 'Equivalent': Equivalent}
    )


def format_formula(expr) -> str:
    """
    Recursively turn a Sympy BoolExpr into a nicely spaced infix string:
      - uses => for Implies, <=> for Equivalent
      - & for And, | for Or
      - ~ for Not, with a space before.
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

    # list_kb
    if msg.startswith('list_kb'):
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
    Process a new statement for the knowledge base
    and immediately draw any obvious consequences
    using Modus Ponens and Resolution.

    Args:
        formula_str: A string representation of a logical formula.

    Returns:
        - "I already know that" if the formula follows from what’s already stored.
        - "I do not believe that" if adding the formula would create a contradiction.
        - "I've learned something new" if the formula is novel and consistent.
    """
    # turn the user’s text into a Sympy formula
    p = parse_formula(formula_str)

    # bundle up everything we believe so far (True if nothing in KB)
    kb_conj = And(*knowledge_base) if knowledge_base else True

    # if KB already entails it, no need to add
    if not satisfiable(And(kb_conj, Not(p))):
        return "I already know that"

    # if it clashes with what we’ve got, reject it
    if not satisfiable(And(kb_conj, p)):
        return "I do not believe that"

    # otherwise, accept the new fact
    knowledge_base.append(p)

    # forward chaining: look for any immediate Modus Ponens inferences
    for imp in list(knowledge_base):
        if imp.func is Implies:
            ante, cons = imp.args
            # if we’ve just added the antecedent, we can learn the consequent
            if p == ante:
                _ = modus_ponens(formula_str, str(imp))

    # resolution with the new clause against all others
    for clause in list(knowledge_base):
        _ = resolution(formula_str, str(clause))
        _ = resolution(str(clause), formula_str)

    return "I've learned something new"


def ask(formula_str: str) -> str:
    """
    Answer a query by checking the KB directly
    and by trying Modus Ponens or a one–step resolution refutation.

    Returns:
      - "Yes" if we can derive the formula
      - "No" if it contradicts what we believe
      - "I do not know" otherwise
    """
    p = parse_formula(formula_str)
    kb_conj = And(*knowledge_base) if knowledge_base else True

    # full entailment check
    if not satisfiable(And(kb_conj, Not(p))):
        return "Yes"

    # full contradiction check
    if not satisfiable(And(kb_conj, p)):
        return "No"

    # try one‐step Modus Ponens
    for imp in knowledge_base:
        if imp.func is Implies:
            antecedent, consequent = imp.args
            if consequent == p:
                # does KB entail the antecedent?
                if not satisfiable(And(kb_conj, Not(antecedent))):
                    return "Yes"

    # try one‐step Resolution
    neg_p_str = f"not {formula_str}"
    for clause in knowledge_base:
        res = resolution(neg_p_str, str(clause))
        if "learned: False" in res:
            return "Yes"

    # if none of the above conditions triggered, we cannot decide
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
    else:
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

    literal1 = literals(c1)
    literal2 = literals(c2)

    for e1 in literal1:
        for e2 in literal2:
            if e1 == Not(e2) or Not(e1) == e2:
                # form the union of the remaining literals
                new_list = [x for x in literal1 if x != e1] + [x for x in literal2 if x != e2]

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
    # parse the user’s input into a Sympy expression
    p = parse_formula(formula_str)

    # convert it into conjunctive normal form
    # simplify=True applies basic simplifications like flattening
    cnf_form = sympy_to_cnf(p, simplify=True)

    orig_str = format_formula(p)
    cnf_str = format_formula(cnf_form)

    # format the two‐line response
    return f"original formula : {orig_str}\nconverted to CNF : {cnf_str}"


def truth_table(formula_str: str) -> str:
    """
    Generate a truth table for the propositional formula, formatting the
    formula itself with format_formula for consistent spacing and operators.
    """
    p = parse_formula(formula_str)
    # get the propositional symbols, sorted by name
    symbols = sorted(p.free_symbols, key=lambda s: s.name)

    # format the full formula once
    fmt_formula = format_formula(p)

    # build header: each variable, then the nicely formatted formula
    header_cells = [str(v) for v in symbols] + [fmt_formula]
    header = " | ".join(header_cells)

    lines = [header]

    # iterate over all 2^n assignments
    for assignment in itertools.product([False, True], repeat=len(symbols)):
        env = dict(zip(symbols, assignment))
        val = bool(p.subs(env))
        # row: 0/1 for each var, then for the formula
        row = " | ".join(str(int(env[v])) for v in symbols) + " | " + str(int(val))
        lines.append(row)

    return "\n".join(lines)
