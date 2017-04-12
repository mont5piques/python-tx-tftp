'''
@author: shylent
'''
from itertools import count, islice
from random import randint
from tftp.util import CANCELLED, iterlast, timedCaller
from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import Clock
from twisted.trial import unittest


class TimedCaller(unittest.TestCase):

    @staticmethod
    def makeTimedCaller(timings, clock=None):
        record = []
        call = lambda: record.append("call")
        last = lambda: record.append("last")
        if clock is None:
            caller = timedCaller(timings, call, last)
        else:
            caller = timedCaller(timings, call, last, clock)
        return caller, record

    def test_raises_ValueError_with_no_timings(self):
        error = self.assertRaises(ValueError, self.makeTimedCaller, [])
        self.assertEqual("No timings specified.", str(error))

    @inlineCallbacks
    def test_calls_last_with_one_timing(self):
        caller, record = self.makeTimedCaller([0])
        self.assertIs(None, (yield caller))
        self.assertEqual(["last"], record)

    @inlineCallbacks
    def test_calls_both_functions_with_multiple_timings(self):
        caller, record = self.makeTimedCaller([0, 0])
        self.assertIs(None, (yield caller))
        self.assertEqual(["call", "last"], record)

    def test_pauses_between_calls(self):
        clock = Clock()
        caller, record = self.makeTimedCaller([1, 2, 3], clock=clock)
        self.assertEqual([], record)
        clock.advance(1)
        self.assertEqual(["call"], record)
        clock.advance(2)
        self.assertEqual(["call", "call"], record)
        clock.advance(3)
        self.assertEqual(["call", "call", "last"], record)
        self.assertIs(None, caller.result)  # Finished.

    def test_can_be_cancelled(self):
        clock = Clock()
        caller, record = self.makeTimedCaller([1, 2, 3], clock=clock)
        self.assertEqual([], record)
        clock.advance(1)
        self.assertEqual(["call"], record)
        clock.advance(2)
        self.assertEqual(["call", "call"], record)
        caller.cancel()
        self.assertIs(CANCELLED, caller.result)
        # Advancing the clock does not result in more calls.
        clock.advance(3)
        self.assertEqual(["call", "call"], record)


class IterLast(unittest.TestCase):

    def test_yields_nothing_when_no_input(self):
        self.assertEqual([], list(iterlast([])))

    def test_yields_once_for_input_of_one(self):
        thing = object()
        self.assertEqual(
            [(True, thing)],
            list(iterlast([thing])))

    def test_yields_once_for_each_input(self):
        things = [object() for _ in range(1, randint(9, 99))]
        self.assertEqual(
            [(False, thing) for thing in things[:-1]] + [(True, things[-1])],
            list(iterlast(things)))

    def test_works_with_unsized_iterators(self):
        things = [object() for _ in range(1, randint(9, 99))]
        self.assertEqual(
            [(False, thing) for thing in things[:-1]] + [(True, things[-1])],
            list(iterlast(iter(things))))

    def test_works_with_infinite_iterators(self):
        # ... though is_last will never be True.
        self.assertEqual(
            [(False, 1), (False, 2), (False, 3)],
            list(islice(iterlast(count(1)), 3)))
