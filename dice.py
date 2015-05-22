#!/usr/bin/env python3

import abc
import functools
import operator
import random
import collections.abc


def standard_die(value):
    return value


def standard_dice(values):
    return sum(values)


@functools.total_ordering
class Rollable(collections.abc.Hashable, collections.abc.Callable, metaclass=abc.ABCMeta):
    @property
    def last(self):
        try:
            return self.__last

        except AttributeError:
            return self()

    def __call__(self):
        self.__last = self._roll()
        return self.last

    def __int__(self):
        return self.last

    def __float__(self):
        return float(self.last)

    def __complex__(self):
        return complex(self.last)

    def __round__(self):
        return round(self.last)

    def __eq__(self, other):
        return self.last == other

    def __ne__(self, other):
        return self.last != other

    def __gt__(self, other):
        return self.last > other

    @abc.abstractmethod
    def __str__(self):
        pass

    @abc.abstractmethod
    def __repr__(self):
        pass

    @abc.abstractmethod
    def _roll(self):
        pass

    @abc.abstractmethod
    def copy(self):
        pass


class Die(Rollable):
    def __init__(self, sides, convention=standard_die):
        sides = int(sides)
        if sides < 2:
            raise ValueError('There must be at least two sides.')

        self.__sides = sides
        self.__convention = convention

    @property
    def sides(self):
        return self.__sides

    def _roll(self):
        return self.__convention(random.randrange(1, self.sides + 1))

    def copy(self):
        return Die(self.sides)

    def __hash__(self):
        return hash((type(Die), self.sides))

    def __str__(self):
        return ''.join(['d', str(self.sides)])

    def __repr__(self):
        return ''.join(['Die(', str(self.sides), ')'])

class RollableSequence(collections.abc.Sequence, Rollable):
    def __init__(self, group=[]):
        self.__group = tuple(group)

    @property
    def _group(self):
        return self.__group

    def __getitem__(self, index):
        self._group[index]

    def __len__(self):
        return len(self._group)

class Dice(RollableSequence):
    def __init__(self, num, rollable, convention=standard_dice):
        num = int(num)
        if num < 1:
            raise ValueError('There must be at least one rollable.')

        if isinstance(rollable, Dice):
            num = num * len(rollable)
            rollable = rollable.group[0].copy()

        super().__init__((rollable.copy() for i in range(num)))
        self.__convention = convention

    def _roll(self):
        return self.__convention(item() for item in self._group)

    def copy(self):
        return Dice(len(self), self.group[0])

    def __hash__(self):
        return hash((type(self), ) + tuple(self._group))

    def __str__(self):
        return ''.join([str(len(self)), str(self._group[0])])

    def __repr__(self):
        return ''.join(['Dice(', str(len(self)), ', ', repr(self._group[0]), ')'])