from sympy.logic.boolalg import And, Or, Not
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


