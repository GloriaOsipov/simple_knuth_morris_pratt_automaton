# simple_knuth_morris_pratt_automaton

A deterministic string-matching automaton that precomputes the KMP failure
function into a full transition table, so scanning a text costs exactly one
table lookup per input symbol with no backtracking.

```python
from simple_knuth_morris_pratt_automaton import Automaton

automaton = Automaton("abab")

automaton.find_all("xxabababxx")   # [2, 4]
automaton.contains("xxababxx")     # True
automaton.run("abab")              # 4
automaton.next_state(2, "a")       # 3
automaton.state_count              # 5
automaton.pattern                  # 'abab'
```

## Why this exists

The textbook KMP algorithm stores a failure function and consults it during the
scan, which means the inner loop still branches and can walk the failure chain.
That is fine for most uses, but it makes the per-symbol work data-dependent and
hard to reason about if you want a fixed cost per byte.

This library takes the other common formulation: build the deterministic
automaton whose transition function is the KMP failure function applied
repeatedly. The preprocessing cost is O(m * |sigma|) where m is the pattern
length and sigma is the set of characters that actually occur in the pattern.
The payoff is that ``run``, ``contains`` and ``find_all`` each do one dictionary
lookup per input symbol and never re-examine a character.

The trade-off is memory: the transition table stores an entry per (state,
symbol-in-pattern) pair, which is m * |sigma| in the worst case. For short
patterns or small alphabets this is negligible; for very long patterns over
Unicode text it is not. If memory matters more than scan speed, use the
failure-function form directly.

## The awkward edge

Transitions are only stored for symbols that occur in the pattern. Every other
symbol drives the automaton back to state 0 — which is exactly what a fully
materialised table would say, so the behaviour is complete. But if you call
``next_state`` with a symbol that is not in the pattern, the lookup goes through
the implicit default and returns 0. That is correct; it is also the reason
``next_state`` validates that the symbol is a single character rather than
silently accepting a longer string.

An empty pattern is allowed. It has one state (state 0), ``run`` always returns
0, ``contains`` always returns ``True``, and ``find_all`` returns every index
from 0 to ``len(text)`` inclusive, since the empty string matches at every
position including the end.

## API

The package exports a single class, ``Automaton``.

- ``Automaton(pattern)`` — build the automaton. ``pattern`` must be a ``str``.
- ``automaton.pattern`` — the pattern the automaton was built for.
- ``automaton.state_count`` — number of states, ``len(pattern) + 1``.
- ``automaton.next_state(state, symbol)`` — next state from ``state`` on
  ``symbol``. ``symbol`` must be a single character; ``state`` must be in range.
  Raises ``ValueError`` otherwise.
- ``automaton.run(text)`` — scan ``text`` and return the final state. The final
  state equals ``len(pattern)`` exactly when the text ends with the pattern.
- ``automaton.find_all(text)`` — list of start indices of every match,
  including overlapping ones, in increasing order.
- ``automaton.contains(text)`` — ``True`` if the pattern occurs in ``text``.
- ``Automaton`` instances compare equal when their patterns are equal, and hash
  accordingly.

## Tests

```
PYTHONPATH=src python -m unittest discover -s tests
```

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

