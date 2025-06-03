# Logic Chatbot

Logic Chatbot is a simple command-line tool for working with propositional logic. You can:

- **Tell** it facts (with consistency and novelty checking).
- **Ask** whether a formula follows from or contradicts what’s known.
- **List** the contents of the knowledge base.
- **Convert** formulas to Conjunctive Normal Form (CNF).
- **Generate** truth tables for formulas.

---

## Requirements

- Python 3.7 or higher
- [Sympy](https://www.sympy.org/)

---

## Installation

```bash
git clone git@github.com:zachealy1/prop-logic-chatbot.git
cd logic-chatbot
pip install sympy
```

## Usage

Start the chatbot:

```bash
python main.py
```

You’ll see a prompt:

```bash
Logic Chatbot
Type 'exit' to quit
>
```

## Commands

### `tell: <formula>`  
Add `<formula>` to the KB if it’s new and consistent.  
**Replies:**  
- "I already know that"  
- "I do not believe that"  
- "I’ve learned something new"

### `ask: <formula>`  
Query the KB.  
**Replies:**  
- "Yes" (entails)  
- "No" (contradicts)  
- "I do not know" (undecided) 

### `list_kb`  
Show all formulas currently in the KB, numbered in insertion order. 

### `modus_ponens: <premise>; <implication>`  
Apply Modus Ponens: if `<premise>` matches the antecedent of `<implication>` (which must be of the form `p implies q`), learn `q`.  
**Replies:**  
- "applied modus ponens and learned: <consequent>"  
- "applied modus ponens, but I already know that: <consequent>"  
- "I do not believe that: <consequent>"  
- "Error: second argument must be an implication."  
- "Error: premise `<premise>` does not match implication antecedent `<antecedent>`." 

### `resolution: <clause1>; <clause2>`  
Apply one‐step resolution between two clauses (each a disjunction of literals). If a complementary pair is found, learn the resolvent.  
**Replies:**  
- "applied resolution and learned: <resolvent>"  
- "applied resolution, but it’s already in the KB: <resolvent>"  
- "No complementary literals found; resolution not applicable."  
- "Invalid syntax. Use: resolution: <clause1>; <clause2>" 

### `to_cnf: <formula>`  
Display the original formula and its CNF equivalent.

### `truth_table: <formula>`  
Print the complete truth table for `<formula>`.

### `exit`  
Quit the chatbot.


## Example Sessions

### Tell

```bash
Logic Chatbot
Type 'exit' to quit
> tell: p implies q
I've learned something new
> tell: p implies q
I already know that
> tell: p
I've learned something new
> tell: not p
I do not believe that
> exit
Goodbye!
```

### Ask

```bash
Logic Chatbot
Type 'exit' to quit
> tell: p implies q
I've learned something new
> tell: p
I've learned something new
> ask: q
Yes
> ask: not p
No
> ask: r
I do not know
> exit
Goodbye!
```

### list_kb

```bash
Logic Chatbot
Type 'exit' to quit
> list_kb
Knowledge base is empty.
> tell: p implies q
I've learned something new
> tell: p
I've learned something new
> list_kb
1. p => q
2. p
> exit
Goodbye!
```

### to_cnf

```bash
$ python main.py
Logic Chatbot
Type 'exit' to quit
> to_cnf: r implies w
original formula : r => w
converted to CNF : w | ~r
> to_cnf: (w and b) implies s
original formula : b & w => s
converted to CNF : s | ~b | ~w
> to_cnf: (not r or c) implies not s
original formula : c | ~r => ~s
converted to CNF : ( r | ~s ) & ( ~c | ~s )
> to_cnf: c iff not r
original formula : c <=> ~r
converted to CNF : ( c | r ) & ( ~c | ~r )
> exit
Goodbye!
```

### truth_table

```bash
$ python main.py
Logic Chatbot
Type 'exit' to quit
> truth_table: p and q
p | q | p & q
0 | 0 | 0
0 | 1 | 0
1 | 0 | 0
1 | 1 | 1
> truth_table: p implies q
p | q | p => q
0 | 0 | 1
0 | 1 | 1
1 | 0 | 0
1 | 1 | 1
> truth_table: p iff q
p | q | p <=> q
0 | 0 | 1
0 | 1 | 0
1 | 0 | 0
1 | 1 | 1
> exit
Goodbye!
```

## Logical Laws

Here are some useful propositional‐logic equivalences ("laws") that you can test or illustrate with the chatbot. Feel
free to experiment by using `tell:` and `ask:` on either side of each equality.

1. **Commutative laws**
    1. `p or q = q or p`
    2. `p and q = q and p`

2. **Associative laws**
    1. `(p or q) or r = p or (q or r)`
    2. `(p and q) and r = p and (q and r)`

3. **De Morgan’s laws**
    1. `not (p or q) = (not p) and (not q)`
    2. `not (p and q) = (not p) or (not q)`

4. **Distributive laws**
    1. `p and (q or r) = (p and q) or (p and r)`
    2. `p or (q and r) = (p or q) and (p or r)`

5. **Negation law**
    1. `not (not p) = p`

6. **Absorption laws**
    1. `p and (p or q) = p`
    2. `p or (p and q) = p`

7. **Implication**
    1. `p implies q = (not p) or q`
    2. `p implies q = (not q) implies (not p)`
    3. `not (p implies q) = p and (not q)`
   
8. **Double Implication (Biconditional)**
    1. `p iff q = (p implies q) and (q implies p)`

