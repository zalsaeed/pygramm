"""'Stackless' implementation of a sentence generator.
You could call it 'stackless' (there is no explicit stack of
non-terminal symbols in progress) or 'unified stack'
(the "to be expanded" list is manipulated in a FIFO
order, with no boundaries between symbols from expanding
different non-terminals).
"""

import grammar
from typing import List

import random

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Gen_State:
    """The state of sentence generation.  Each step of the
    generator transforms the state.
    """

    def __init__(self, gram: grammar.Grammar, budget: int):
        self.text = ""
        # Note 'remainder' is in reverse order, so that
        # we can push and pop symbols
        self.rest: List[grammar.RHSItem] = [gram.start]
        # Budget is always an available budget for the next
        # item, after reserving adequate resource for
        # subsequent items
        self.budget = budget

    def __str__(self) -> str:
        """Looks like foobar @ A(B|C)*Dx,8"""
        suffix = "".join([str(sym) for sym in reversed(self.rest)])
        return f"{self.text} @ {suffix}"


    # A single step has two parts, because we need to let a
    # an external agent control the expansion.  For
    # alternatives and symbols, part 1 is to
    # generate a set of choices, presented to the external
    # agent.  In part 2 the external agent presents the choice
    # to be taken.  If the first element of the suffix is a
    # terminal symbol, the only operation is to shift it to
    # the end of the prefix.
    #

    # Call has_more before attempting a move
    def has_more(self) -> bool:
        # We must expand BEFORE checking length,
        # because we could have a sequence of empty sequences
        while len(self.rest) > 0 and \
                isinstance(self.rest[-1], grammar._Seq):
            sym = self.rest.pop()
            log.debug(f"Expanding sequence '{sym}'")
            # FIFO access order --- reversed on rest
            for el in reversed(sym.items):
                self.rest.append(el)
        return len(self.rest) > 0


    # Terminal symbols can only be shifted to prefix
    def is_terminal(self) -> bool:
        sym = self.rest[-1] # FIFO access order
        return isinstance(sym, grammar._Literal)

    def shift(self):
        sym = self.rest.pop()
        assert isinstance(sym, grammar._Literal)
        self.text += sym.text

    # Non-terminal symbols, including kleene star and choices,
    # provide an opportunity for external control of options.
    # Each such element has a method to present a set of
    # choices within budget.
    def choices(self) -> List[grammar.RHSItem]:
        """The RHS elements that can be chosen
        for the next step.  (Possibly just one.)
        """
        element = self.rest[-1]  # FIFO access
        return element.choices(self.budget)

    # External agent can pick one of the choices to replace
    # the current symbol.  Budget will be adjusted by minimum
    # cost of that expansion.
    def expand(self, expansion: grammar.RHSItem):
        sym = self.rest.pop()
        log.debug(f"{sym} -> {expansion}")
        self.rest.append(expansion)
        self.budget -= expansion.min_tokens()


def random_sentence(g: grammar.Grammar, budget: int=20):
    """A generator of random sentences, without external control"""
    random.seed()
    while g.start.min_tokens() > budget:
        log.info(f"Bumping budget by minimum requirement {g.start.min_tokens()}")
        budget += g.start.min_tokens()
    state = Gen_State(g, budget)
    print(f"Initially {state}")
    while state.has_more():
        print(f"=> {state} budget {state.budget}")
        if state.is_terminal():
            state.shift()
        else:
            choices = state.choices()
            choice = random.choice(choices)
            log.debug(f"Choosing {choice}")
            state.expand(choice)
    print(f"Final: \n{state.text}")






