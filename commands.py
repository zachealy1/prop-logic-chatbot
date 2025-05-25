from sympy.logic.boolalg import And, Or, Not
from sympy.logic.inference import satisfiable
from sympy import Implies, Equivalent
from sympy import to_cnf as sympy_to_cnf
from logic_chatbot import knowledge_base, parse_formula

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

    # helper: extract the list of literals from a clause
    def literals(cl):
        return list(cl.args) if cl.func is Or else [cl]

    lits1 = literals(c1)
    lits2 = literals(c2)

    # look for a complementary pair
    for e1 in lits1:
        for e2 in lits2:
            if e1 == Not(e2) or Not(e1) == e2:
                # remove e1 and e2, then union the rest
                new_list = [x for x in lits1 if x != e1] + [x for x in lits2 if x != e2]
                # dedupe
                uniq = []
                for x in new_list:
                    if x not in uniq:
                        uniq.append(x)
                # build the resolvent
                if not uniq:
                    resolvent = False  # the empty clause
                elif len(uniq) == 1:
                    resolvent = uniq[0]
                else:
                    resolvent = Or(*uniq)

                # delegate to tell(...) to handle KB insertion
                res = tell(str(resolvent))
                if res == "I've learned something new":
                    return f"applied resolution and learned: {resolvent}"
                elif res == "I already know that":
                    return f"applied resolution but I already know that: {resolvent}"
                else:
                    return f"I do not believe that: {resolvent}"

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

    # 3. format the two‐line response
    return f"original formula: {p}\nconverted to CNF: {cnf_form}"