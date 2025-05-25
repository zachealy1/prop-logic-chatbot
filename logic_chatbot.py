from sympy.logic.boolalg import And, Or, Not
from sympy.parsing.sympy_parser import parse_expr
from sympy import Implies, Equivalent

from commands import ask, tell, list_kb, modus_ponens, resolution, convert_to_cnf

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
    if msg.startswith('convert_to_cnf:'):
        formula = msg[len('convert_to_cnf:'):].strip()
        return convert_to_cnf(formula)

    # nothing matched
    return "Unknown command. Please use tell:, ask:, list_kb, modus_ponens:, resolution:, to_cnf: or exit."

