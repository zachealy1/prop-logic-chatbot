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
git clone https://github.com/your-username/logic-chatbot.git
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
- “I already know that”  
- “I do not believe that”  
- “I’ve learned something new”

### `ask: <formula>`
Query the KB.  
**Replies:**  
- “Yes” (entails)  
- “No” (contradicts)  
- “I do not know” (undecided)

### `list_kb`
Show all formulas currently in the KB, numbered in insertion order.

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
> to_cnf: p implies (q and r)
original formula : p => ( q & r )
converted to CNF : ( q | ~p ) & ( r | ~p )
> to_cnf: (p or q) implies (r and s)
original formula : p | q => ( r & s )
converted to CNF : ( r | ~p ) & ( r | ~q ) & ( s | ~p ) & ( s | ~q )
> to_cnf: p iff q
original formula : p <=> q
converted to CNF : ( p | ~q ) & ( q | ~p )
> to_cnf: not (p and (q or not r))
original formula : ~p & ( q | ~r )
converted to CNF : ( r | ~p ) & ( ~p | ~q )
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
