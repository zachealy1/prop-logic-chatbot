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
    input_str = text.strip()

    # map infix keywords to symbols/operators
    input_str = re.sub(r'\bimplies\b', '>>', input_str)
    input_str = re.sub(r'\band\b', '&', input_str)
    input_str = re.sub(r'\bor\b', '|', input_str)
    input_str = re.sub(r'\bnot\s+', '~', input_str)

    # handle “iff” by turning it into an Explicit call
    if 'iff' in input_str:
        left_part, right_part = input_str.split('iff', 1)
        input_str = f"Equivalent({left_part.strip()}, {right_part.strip()})"
    # now parse a valid Python expression
    return parse_expr(
        input_str,
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
        inner_str = format_formula(expr.args[0])
        # if inner is compound, keep its parentheses
        return f"~{inner_str}"

    # implication
    if expr.func is Implies:
        antecedent_expr, consequent_expr = expr.args
        left_str = format_formula(antecedent_expr)
        right_str = format_formula(consequent_expr)
        # wrap right in parens if it's compound
        if not consequent_expr.is_Symbol and consequent_expr.func is not Not:
            right_str = f"( {right_str} )"
        return f"{left_str} => {right_str}"

    # biconditional
    if expr.func is Equivalent:
        left_expr, right_expr = expr.args
        left_str = format_formula(left_expr)
        right_str = format_formula(right_expr)
        if not right_expr.is_Symbol and right_expr.func is not Not:
            right_str = f"( {right_str} )"
        return f"{left_str} <=> {right_str}"

    # conjunction/disjunction
    if expr.func is And or expr.func is Or:
        operator_str = " & " if expr.func is And else " | "
        parts = []
        for subexpr in expr.args:
            sub_str = format_formula(subexpr)
            if subexpr.func in (And, Or, Implies, Equivalent) and len(subexpr.args) > 1:
                parts.append(f"( {sub_str} )")
            else:
                parts.append(sub_str)
        return operator_str.join(parts)

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

    # truth_table: <formula>
    if msg.startswith('truth_table:'):
        formula_part = msg[len('truth_table:'):].strip()
        return truth_table(formula_part)

    # tell: <formula>
    if msg.startswith('tell:'):
        formula_part = msg[len('tell:'):].strip()
        return tell(formula_part)

    # ask: <formula>
    if msg.startswith('ask:'):
        formula_part = msg[len('ask:'):].strip()
        return ask(formula_part)

    # list_kb
    if msg.startswith('list_kb'):
        return list_kb()

    # modus_ponens: <premise>; <implication>
    if msg.startswith('modus_ponens:'):
        rest = msg[len('modus_ponens:'):].strip()
        parts = rest.split(';')
        if len(parts) != 2:
            return "Invalid syntax. Use: modus_ponens: <premise>; <implication>"
        premise_expr_str, implication_expr_str = parts[0].strip(), parts[1].strip()
        return modus_ponens(premise_expr_str, implication_expr_str)

    # resolution: <clause1>; <clause2>
    if msg.startswith('resolution:'):
        rest = msg[len('resolution:'):].strip()
        parts = rest.split(';')
        if len(parts) != 2:
            return "Invalid syntax. Use: resolution: <clause1>; <clause2>"
        clause1_str, clause2_str = parts[0].strip(), parts[1].strip()
        return resolution(clause1_str, clause2_str)

    # to_cnf: <formula>
    if msg.startswith('to_cnf:'):
        formula_part = msg[len('to_cnf:'):].strip()
        return convert_to_cnf(formula_part)

    # nothing matched
    return "Unknown command. Please use tell:, ask:, list_kb, modus_ponens:, resolution:, to_cnf: or exit."


def tell(formula_str: str) -> str:
    """
    Process a new statement for the knowledge base
    and immediately draw any obvious consequences
    using Modus Ponens and Resolution.

    Returns:
        - "I already know that" if the formula follows from what’s already stored.
        - "I do not believe that" if adding the formula would create a contradiction.
        - "I've learned something new" if the formula is novel and consistent.
    """
    # turn the user’s text into a Sympy formula
    new_expr = parse_formula(formula_str)

    # bundle up everything we believe so far (True if nothing in KB)
    kb_conjunction = And(*knowledge_base) if knowledge_base else True

    # if KB already entails new_expr, no need to add
    if not satisfiable(And(kb_conjunction, Not(new_expr))):
        return "I already know that"

    # if it clashes with what we’ve got, reject it
    if not satisfiable(And(kb_conjunction, new_expr)):
        return "I do not believe that"

    # otherwise, accept the new fact
    knowledge_base.append(new_expr)

    # forward chaining: look for any immediate Modus Ponens inferences
    for fact in list(knowledge_base):
        if fact.func is Implies:
            antecedent_expr, consequent_expr = fact.args
            if new_expr == antecedent_expr:
                _ = modus_ponens(formula_str, str(fact))

    # resolution with the new clause against all others
    for clause_expr in list(knowledge_base):
        _ = resolution(formula_str, str(clause_expr))
        _ = resolution(str(clause_expr), formula_str)

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
    query_expr = parse_formula(formula_str)
    kb_conjunction = And(*knowledge_base) if knowledge_base else True

    # full entailment check
    if not satisfiable(And(kb_conjunction, Not(query_expr))):
        return "Yes"

    # full contradiction check
    if not satisfiable(And(kb_conjunction, query_expr)):
        return "No"

    # try one‐step Modus Ponens
    for fact in knowledge_base:
        if fact.func is Implies:
            antecedent_expr, consequent_expr = fact.args
            if consequent_expr == query_expr:
                if not satisfiable(And(kb_conjunction, Not(antecedent_expr))):
                    return "Yes"

    # try one‐step Resolution
    negated_query_str = f"not {formula_str}"
    for clause_expr in knowledge_base:
        result_str = resolution(negated_query_str, str(clause_expr))
        if "learned: False" in result_str:
            return "Yes"

    return "I do not know"


def list_kb() -> str:
    """
    Implements the `list_kb` command.
    Returns a numbered list of all formulas in the KB.
    """
    if not knowledge_base:
        return "Knowledge base is empty."

    lines = []
    for index, formula_expr in enumerate(knowledge_base, start=1):
        if formula_expr.func is Implies:
            antecedent_expr, consequent_expr = formula_expr.args
            representation = f"{antecedent_expr} => {consequent_expr}"
        elif formula_expr.func is Equivalent:
            left_expr, right_expr = formula_expr.args
            representation = f"{left_expr} <=> {right_expr}"
        else:
            representation = str(formula_expr)
        lines.append(f"{index}. {representation}")

    return "\n".join(lines)


def modus_ponens(premise_str: str, implication_str: str) -> str:
    """
    modus_ponens: <premise>; <implication>
    e.g. modus_ponens("p", "p implies q") -> "applied modus ponens and learned: q"
    """
    premise_expr = parse_formula(premise_str)
    implication_expr = parse_formula(implication_str)

    # ensure implication_expr is an implication
    if implication_expr.func is not Implies:
        return "Error: second argument must be an implication."

    antecedent_expr, consequent_expr = implication_expr.args

    # ensure the premise matches the antecedent
    if premise_expr != antecedent_expr:
        return f"Error: premise {premise_expr!s} does not match implication antecedent {antecedent_expr!s}."

    # now learn the consequent
    response_str = tell(str(consequent_expr))
    if response_str == "I've learned something new":
        return f"applied modus ponens and learned: {consequent_expr}"
    elif response_str == "I already know that":
        return f"applied modus ponens but I already know that: {consequent_expr}"
    else:
        return f"I do not believe that: {consequent_expr}"


def resolution(clause1_str: str, clause2_str: str) -> str:
    """
    resolution: <clause1>; <clause2>
    e.g., resolution("p or r", "not p or s") -> "applied resolution and learned: r | s"
    """
    clause1_expr = parse_formula(clause1_str)
    clause2_expr = parse_formula(clause2_str)

    def get_literals(expr):
        return list(expr.args) if expr.func is Or else [expr]

    literals1 = get_literals(clause1_expr)
    literals2 = get_literals(clause2_expr)

    for lit1 in literals1:
        for lit2 in literals2:
            if lit1 == Not(lit2) or Not(lit1) == lit2:
                remaining_literals = [x for x in literals1 if x != lit1] + [x for x in literals2 if x != lit2]

                # dedupe while preserving order
                unique_literals = []
                for lit in remaining_literals:
                    if lit not in unique_literals:
                        unique_literals.append(lit)

                # build the resolvent clause
                if not unique_literals:
                    resolvent_expr = false
                elif len(unique_literals) == 1:
                    resolvent_expr = unique_literals[0]
                else:
                    resolvent_expr = Or(*unique_literals)

                # insert into KB if new
                if resolvent_expr not in knowledge_base:
                    knowledge_base.append(resolvent_expr)
                    return f"applied resolution and learned: {resolvent_expr}"
                else:
                    return f"applied resolution but it's already in the KB: {resolvent_expr}"

    return "No complementary literals found; resolution not applicable."


def convert_to_cnf(formula_str: str) -> str:
    """
    Implements the `to_cnf:` command.
    Returns two lines:
      original formula: <parsed>
      converted to CNF: <cnf form>
    """
    # parse the user’s input into a Sympy expression
    formula_expr = parse_formula(formula_str)

    # convert it into conjunctive normal form
    # simplify=True applies basic simplifications like flattening
    cnf_expr = sympy_to_cnf(formula_expr, simplify=True)

    orig_str = format_formula(formula_expr)
    cnf_str = format_formula(cnf_expr)

    return f"original formula : {orig_str}\nconverted to CNF : {cnf_str}"


def truth_table(formula_str: str) -> str:
    """
    Generate a truth table for the propositional formula, formatting the
    formula itself with format_formula for consistent spacing and operators.
    """
    formula_expr = parse_formula(formula_str)
    # get the propositional symbols, sorted by name
    vars_list = sorted(formula_expr.free_symbols, key=lambda s: s.name)

    # format the full formula once
    fmt_formula_str = format_formula(formula_expr)

    header_cells = [str(v) for v in vars_list] + [fmt_formula_str]
    header = " | ".join(header_cells)

    lines = [header]

    for assignment in itertools.product([False, True], repeat=len(vars_list)):
        env = dict(zip(vars_list, assignment))
        value = bool(formula_expr.subs(env))
        row = " | ".join(str(int(env[v])) for v in vars_list) + " | " + str(int(value))
        lines.append(row)

    return "\n".join(lines)
