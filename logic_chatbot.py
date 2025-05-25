from sympy.logic.boolalg import And, Or, Not
from sympy.logic.inference import satisfiable
from sympy.parsing.sympy_parser import parse_expr
from sympy import Implies, Equivalent

# our global knowledge base: a list of Sympy expressions
knowledge_base = []

def parse_formula(text: str):
    """
    Parse a propositional‐logic string into a Sympy Boolean expression,
    mapping our keywords to the right Sympy constructors.
    """
    return parse_expr(
        text,
        local_dict={
            'and':     And,
            'or':      Or,
            'not':     Not,
            'implies': Implies,
            'iff':     Equivalent
        }
    )

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

