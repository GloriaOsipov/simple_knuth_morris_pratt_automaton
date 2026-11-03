"""Tests for the KMP automaton.

These are deliberately a small, honest set: every assertion matches behaviour
that ``core.py`` actually implements.  No timing, no randomness.
"""

import unittest

from simple_knuth_morris_pratt_automaton import Automaton


class TestConstruction(unittest.TestCase):
    def test_empty_pattern_state_count(self):
        a = Automaton("")
        self.assertEqual(a.state_count, 1)
        self.assertEqual(a.pattern, "")

    def test_nonempty_pattern_state_count(self):
        a = Automaton("abab")
        self.assertEqual(a.state_count, 5)

    def test_type_error_on_non_str_pattern(self):
        with self.assertRaises(TypeError):
            Automaton(b"abc")  # type: ignore[arg-type]

    def test_repr(self):
        self.assertEqual(repr(Automaton("ab")), "Automaton(pattern='ab')")

    def test_equality_and_hash(self):
        self.assertEqual(Automaton("ab"), Automaton("ab"))
        self.assertNotEqual(Automaton("ab"), Automaton("ba"))
        self.assertEqual(hash(Automaton("ab")), hash(Automaton("ab")))


class TestTransitions(unittest.TestCase):
    def test_next_state_advances(self):
        a = Automaton("abab")
        self.assertEqual(a.next_state(0, "a"), 1)
        self.assertEqual(a.next_state(1, "b"), 2)
        self.assertEqual(a.next_state(2, "a"), 3)
        self.assertEqual(a.next_state(3, "b"), 4)

    def test_next_state_falls_back(self):
        a = Automaton("abab")
        # After "ab" we have seen prefix "ab"; another "a" gives "aba",
        # which is a prefix of length 3.
        self.assertEqual(a.next_state(2, "a"), 3)
        # At state 3, symbol "a" restarts the suffix "a" -> state 1.
        self.assertEqual(a.next_state(3, "a"), 1)

    def test_unknown_symbol_returns_to_zero(self):
        a = Automaton("abc")
        self.assertEqual(a.next_state(2, "z"), 0)

    def test_next_state_rejects_bad_symbol(self):
        a = Automaton("abc")
        with self.assertRaises(ValueError):
            a.next_state(0, "ab")
        with self.assertRaises(ValueError):
            a.next_state(0, "")

    def test_next_state_rejects_bad_state(self):
        a = Automaton("abc")
        with self.assertRaises(ValueError):
            a.next_state(-1, "a")
        with self.assertRaises(ValueError):
            a.next_state(4, "a")


class TestRun(unittest.TestCase):
    def test_run_returns_final_state(self):
        a = Automaton("abab")
        self.assertEqual(a.run("ab"), 2)
        self.assertEqual(a.run("abab"), 4)
        self.assertEqual(a.run("xabab"), 4)
        self.assertEqual(a.run("ababx"), 0)

    def test_run_empty_text(self):
        self.assertEqual(Automaton("a").run(""), 0)

    def test_run_empty_pattern(self):
        self.assertEqual(Automaton("").run("anything"), 0)


class TestFindAll(unittest.TestCase):
    def test_simple_matches(self):
        a = Automaton("abc")
        self.assertEqual(a.find_all("xxabcxxabc"), [2, 7])

    def test_overlapping_matches(self):
        a = Automaton("aa")
        self.assertEqual(a.find_all("aaa"), [0, 1])

    def test_no_matches(self):
        a = Automaton("abc")
        self.assertEqual(a.find_all("xyz"), [])

    def test_empty_pattern_matches_everywhere(self):
        a = Automaton("")
        self.assertEqual(a.find_all("ab"), [0, 1, 2])

    def test_find_all_type_error(self):
        with self.assertRaises(TypeError):
            Automaton("a").find_all(123)  # type: ignore[arg-type]


class TestContains(unittest.TestCase):
    def test_contains_true(self):
        self.assertTrue(Automaton("ab").contains("xxabyy"))

    def test_contains_false(self):
        self.assertFalse(Automaton("ab").contains("xxayy"))

    def test_contains_empty_pattern(self):
        self.assertTrue(Automaton("").contains(""))
        self.assertTrue(Automaton("").contains("abc"))

    def test_contains_type_error(self):
        with self.assertRaises(TypeError):
            Automaton("a").contains(None)  # type: ignore[arg-type]


class TestEdgeCases(unittest.TestCase):
    def test_single_character_pattern(self):
        a = Automaton("a")
        self.assertEqual(a.find_all("banana"), [1, 3, 5])

    def test_pattern_longer_than_text(self):
        a = Automaton("abcdef")
        self.assertEqual(a.find_all("abc"), [])
        self.assertFalse(a.contains("abc"))

    def test_self_overlapping_pattern(self):
        # "abababa" over "ababababa" should match at 0 and 2.
        a = Automaton("abababa")
        self.assertEqual(a.find_all("ababababa"), [0, 2])

    def test_repeated_single_symbol(self):
        a = Automaton("aaa")
        self.assertEqual(a.find_all("aaaaa"), [0, 1, 2])
