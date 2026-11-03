"""A deterministic string-matching automaton built from the KMP failure function.

The classic Knuth-Morris-Pratt algorithm precomputes a failure function and
uses it during scanning to decide how far to shift the pattern.  That version
needs an amortised constant number of comparisons per input symbol, but it still
branches on the failure function at scan time.

This module instead materialises the full transition table: for every state
(0..m) and every symbol in the alphabet, ``delta[state][symbol]`` is the next
state.  Building that table costs O(m * |sigma|) time and memory, and in return
scanning is a plain table lookup with exactly one comparison per input symbol
and no backtracking at all.

We only build transitions for symbols that actually occur in the pattern.  Any
other symbol always drives the automaton back to state 0, which is the same
answer the full table would give, so we do not spend memory on it.  Looking up
an unknown symbol therefore has to be handled explicitly by ``next_state``.
"""

from __future__ import annotations

from typing import Dict, Iterable, List


class Automaton:
    """A deterministic automaton that recognises occurrences of a pattern.

    The automaton has ``len(pattern) + 1`` states.  State ``k`` means "the last
    ``k`` characters read match the first ``k`` characters of the pattern".
    State ``m`` (the pattern length) is the accepting state.

    Transitions are precomputed for every symbol that occurs in the pattern.
    For any other symbol the automaton returns to state 0, which is exactly
    what the full transition table would contain, so the table is complete in
    behaviour even though it is sparse in storage.
    """

    __slots__ = ("_pattern", "_transitions")

    def __init__(self, pattern: str) -> None:
        if not isinstance(pattern, str):
            raise TypeError("pattern must be a str")
        self._pattern = pattern
        self._transitions: List[Dict[str, int]] = self._build_transitions(pattern)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @staticmethod
    def _build_transitions(pattern: str) -> List[Dict[str, int]]:
        """Build the transition table by simulating the failure function.

        For each state ``k`` we know the failure link ``pi[k]``: the length of
        the longest proper suffix of ``pattern[:k]`` that is also a prefix of
        the pattern.  Given a symbol ``c``:

        * if ``c`` matches ``pattern[k]`` we advance to ``k + 1``;
        * otherwise we fall back to ``pi[k]`` and try again.

        Doing that fallback at build time is what lets scanning be a single
        lookup.  Only symbols present in the pattern are stored; the rest are
        implicitly state 0.
        """
        m = len(pattern)
        # Failure function: pi[k] is the length of the longest proper prefix of
        # pattern[:k] that is also a suffix of pattern[:k].
        pi: List[int] = [0] * (m + 1)
        if m > 0:
            k = 0
            for i in range(1, m):
                while k > 0 and pattern[i] != pattern[k]:
                    k = pi[k]
                if pattern[i] == pattern[k]:
                    k += 1
                pi[i + 1] = k

        symbols = set(pattern)
        transitions: List[Dict[str, int]] = [dict() for _ in range(m + 1)]
        for state in range(m + 1):
            row = transitions[state]
            for symbol in symbols:
                if state < m and pattern[state] == symbol:
                    row[symbol] = state + 1
                else:
                    # Fall back along the failure chain until we either match
                    # or hit state 0.  pi[0] is 0 by definition, so the loop
                    # terminates.
                    k = state
                    while k > 0 and (k >= m or pattern[k] != symbol):
                        k = pi[k]
                    if k < m and pattern[k] == symbol:
                        k += 1
                    row[symbol] = k
        return transitions

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def pattern(self) -> str:
        """The pattern this automaton was built for."""
        return self._pattern

    @property
    def state_count(self) -> int:
        """Number of states, i.e. ``len(pattern) + 1``."""
        return len(self._transitions)

    def next_state(self, state: int, symbol: str) -> int:
        """Return the state reached from ``state`` on ``symbol``.

        ``symbol`` must be a single character.  Symbols that never appear in
        the pattern always lead back to state 0; that case is not stored in the
        table and is handled here.
        """
        if not isinstance(symbol, str) or len(symbol) != 1:
            raise ValueError("symbol must be a single character")
        if not 0 <= state < len(self._transitions):
            raise ValueError("state out of range")
        return self._transitions[state].get(symbol, 0)

    def run(self, text: str) -> int:
        """Scan ``text`` and return the final state.

        The final state is ``m`` exactly when the text ends with the pattern.
        """
        if not isinstance(text, str):
            raise TypeError("text must be a str")
        state = 0
        for ch in text:
            state = self._transitions[state].get(ch, 0)
        return state

    def find_all(self, text: str) -> List[int]:
        """Return the start indices of every (possibly overlapping) match.

        Matches are reported in increasing order of start index.  Overlapping
        matches are included: ``find_all`` on ``"aaa"`` with pattern ``"aa"``
        returns ``[0, 1]``.
        """
        if not isinstance(text, str):
            raise TypeError("text must be a str")
        m = len(self._pattern)
        if m == 0:
            # An empty pattern matches at every position, including the end.
            return list(range(len(text) + 1))
        state = 0
        hits: List[int] = []
        for i, ch in enumerate(text):
            state = self._transitions[state].get(ch, 0)
            if state == m:
                hits.append(i - m + 1)
        return hits

    def contains(self, text: str) -> bool:
        """Return ``True`` if ``text`` contains the pattern."""
        if not isinstance(text, str):
            raise TypeError("text must be a str")
        m = len(self._pattern)
        if m == 0:
            return True
        state = 0
        for ch in text:
            state = self._transitions[state].get(ch, 0)
            if state == m:
                return True
        return False

    def __repr__(self) -> str:
        return f"Automaton(pattern={self._pattern!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Automaton):
            return NotImplemented
        return self._pattern == other._pattern

    def __hash__(self) -> int:
        return hash((Automaton, self._pattern))
