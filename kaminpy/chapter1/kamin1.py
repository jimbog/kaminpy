#!/usr/bin/env python
# coding: utf-8

'''
This interpreter implements the language described in Chapter 1 of Samuel 
Kamin's Programming Languages book [1]. This implementation is based on
Peter Norvig's lis.py [2]. 

[1] Samuel Kamin, "Programming Languages, An Interpreter-Based Approach",
    Addison-Wesley, Reading, MA, 1990. ISBN 0-201-06824-9.
[2] http://norvig.com/lispy.html

BNF of this mini-language (so far):

<expression> ::= <integer>
               | `(` <value-op> <expression1>  <expression2> `)`
               | `(` `if` <expression1>  <expression2> <expression3> `)`
               | `(` `print` <expression> `)`
               | `(` `begin` <expression>+ `)`
<value-op>   ::= `+` | `-` | `*` | `/` | `=` | `<` | `>`
<integer>    ::= sequence of digits, possibly preceded by minus sign

'''

import re
import sys
import inspect

REGEX_INTEGER = re.compile(r'-?\d+$')

class InterpreterError(StandardError):
    """generic interpreter error"""
    def __init__(self, value=None):
        self.value = value
    def __str__(self):
        msg = self.__class__.__doc__
        if self.value is not None:
            return msg + ': ' + repr(self.value)
        return msg

class UnexpectedEndOfInput(InterpreterError):
    """unexpected end of input"""

class UnexpectedRightParen(InterpreterError):
    """unexpected )"""

class InvalidOperator(InterpreterError):
    """invalid operator"""

class NullExpression(InterpreterError):
    """null expression"""

class MissingArguments(InterpreterError):
    """missing arguments"""

class TooManyArguments(InterpreterError):
    """too many arguments"""

def tokenize(source_code):
    """Convert a string into a list of tokens"""
    return source_code.replace('(',' ( ').replace(')',' ) ').split()

def parse(source_code):
    """Convert source code into syntax tree"""
    tokens = tokenize(source_code)
    return read(tokens)

def read(tokens):
    """Read tokens building a syntax tree of nested lists of expressions"""
    if len(tokens) == 0:
        raise UnexpectedEndOfInput()
    token = tokens.pop(0)

    if token == '(':
        parsed = []
        if len(tokens) == 0:
            raise UnexpectedEndOfInput()
        while tokens[0] != ')':
            parsed.append(read(tokens))
            if len(tokens) == 0:
                raise UnexpectedEndOfInput()
        tokens.pop(0) # pop off ')'
        return parsed
    elif token == ')':
        raise UnexpectedRightParen()
    else:
        return atom(token)

def atom(token):
    """Return integers as integers, everything else as symbols"""
    if REGEX_INTEGER.match(token): # -1 is an int, +1 is a symbol
        return int(token)
    else:
        return token

# cannot use the operator module because inspect.getargspec only 
# works with functions defined in Python
operators = { 
    '+': lambda a, b: a + b, 
    '-': lambda a, b: a - b, 
    '*': lambda a, b: a * b, 
    '/': lambda a, b: a / b, 
    '=': lambda a, b: 1 if a == b else 0,
    '<': lambda a, b: 1 if a < b else 0,
    '>': lambda a, b: 1 if a > b else 0,
}

def check_args(function, args):
    """Compare arguments with parameters expected by funcion"""
    fixed_args, var_args = inspect.getargspec(function)[:2]
    min_args = max_args = len(fixed_args)
    if len(args) < min_args:
        raise MissingArguments()
    elif len(args) > max_args and var_args is None:
        raise TooManyArguments()

def if_cmd(test, conseq, alt):
    result = conseq if evaluate(test) else alt
    return evaluate(result)

def print_cmd(arg):
    result = evaluate(arg)
    print(result)
    return result

def begin_cmd(first, *rest):
    for exp in (first,)+rest:
        result = evaluate(exp)
    return result

commands = {
    'if': if_cmd,
    'print': print_cmd,
    'begin': begin_cmd,
}

def evaluate(expression):
    """Calculate the value of an expression"""
    if isinstance(expression, int):
        return expression
    elif isinstance(expression, str): # operator
        try:
            return operators[expression]
        except KeyError:
            raise InvalidOperator(expression)
    elif expression[0] in commands:
        # special forms evaluate (or not) their args
        command = commands[expression.pop(0)]
        check_args(command, expression)
        return command(*expression)
    else: 
        # evaluate operator and args
        exps = [evaluate(exp) for exp in expression]
        if len(exps) == 0:
            raise NullExpression()
        operator = exps.pop(0)
        if callable(operator):
            check_args(operator, exps)
            return operator(*exps) # apply operator to args
        else:
            raise InvalidOperator(operator)

def repl(prompt='> '):
    """A read-eval-print loop"""
    while True:
        try:
            value = evaluate(parse(raw_input(prompt)))
        except (InterpreterError, ZeroDivisionError) as exc:
            print('! ' + str(exc))
        except KeyboardInterrupt:
            print()
            raise SystemExit
        else:
            print(value)

if __name__=='__main__':
    repl()
