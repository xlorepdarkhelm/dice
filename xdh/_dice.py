#!/usr/bin/env python3

"""
Module designed to provide a new numerical datatype for simulating dice rolls.
The actual rolling mechanic used is to call the object like a function with
parenthesis next to it, like: ``d6()``. This rolls the die and returns the value
of the die.

Standard mathematical operations are possible on dice, however it constructs
the operation into objects that process the operation when rolled. So,
``d6 + 5`` would make a new object, which in turn can be rolled:
``a = dice.Die(6) + 5; a()``.

"""

import abc
import functools
import math
import numbers
import operator
import random
import collections.abc

from xdh import config

def standard_die(value):
    return value


def standard_dice(values):
    return sum(values)


class HasConvention:
    def __init__(self, convention):
        self.__convention = convention

    @property
    def convention(self):
        return self.__convention


class Parenthesize:
    def paren_str(self):
        return ''.join(['(', str(self), ')'])

class Rollable(
    collections.abc.Hashable,
    collections.abc.Callable,
    numbers.Integral,
    metaclass=abc.ABCMeta
):
    """
    The fundamental base class of all rollable/dice objects. This class drives
    all dice capabilities. Every Rollable object is callable, which is how it is
    rolled.  Rollables are essentially treated like integers that the value can
    be fluctuated by rolling. However, they also have a consistant aspect that
    is hashable, that exists apart from their value, representing the components
    that make up the rollable object (like the number of sides of a Die, for
    instance).

    All subclasses must define the _roll() and copy() methods, as well as the
    special methods __str__() and __repr__().
    """

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
        return int(self.last)

    def __index__(self):
        return int(self.last)

    def __round__(self):
        return round(self.last)

    def __eq__(self, other):
        return self.last == other

    def __ne__(self, other):
        return self.last != other

    def __gt__(self, other):
        return self.last > other

    def __ge__(self, other):
        return self.last >= other

    def __lt__(self, other):
        return self.last < other

    def __le__(self, other):
        return self.last <= other

    @abc.abstractmethod
    def __str__(self):
        raise NotImplementedError

    @abc.abstractmethod
    def __repr__(self):
        raise NotImplementedError

    @abc.abstractmethod
    def _roll(self):
        raise NotImplementedError

    @abc.abstractmethod
    def copy(self):
        raise NotImplementedError

    def __add__(self, other):
        return DiceAdder(self, other)

    def __radd__(self, other):
        return DiceAdder(other, self)

    def __mul__(self, other):
        return DiceMultiplier(self, other)

    def __rmul__(self, other):
        return DiceMultiplier(other, self)

    def __truediv__(self, other):
        return DiceTrueDivider(self, other)

    def __rtruediv__(self, other):
        return DiceTrueDivider(other, self)

    def __floordiv__(self, other):
        return DiceFloorDivider(self, other)

    def __rfloordiv__(self, other):
        return DiceFloorDivider(other, self)

    def __pos__(self):
        return self.copy()

    def __neg__(self):
        return DiceMultiplier(self, scalar=-1)

    def __invert__(self):
        return DiceBitwiseInvert(self)

    def __abs__(self):
        return DiceAbs(self)

    def __trunc__(self):
        return DiceTrunc(self)

    def __ceil__(self):
        return DiceCeil(self)

    def __floor__(self):
        return DiceFloor(self)

    def __round__(self, ndigits=0):
        return DiceRound(self, ndigits)

    def __and__(self, other):
        return DiceBitwiseAnd(self, other)

    def __rand__(self, other):
        return DiceBitwiseAnd(other, self)

    def __xor__(self, other):
        return DiceBitwiseXOr(self, other)

    def __rxor__(self, other):
        return DiceBitwiseXOr(other, self)

    def __or__(self, other):
        return DiceBitwiseOr(self, other)

    def __ror__(self, other):
        return DiceBitwiseOr(other, self)

    def __lshift__(self, other):
        return DiceBitwiseShift(self, -other)

    def __rlshift__(self, other):
        return DiceBitwiseShift(other, -self)

    def __rshift__(self, other):
        return DiceBitwiseShift(self, other)

    def __rrshift__(self, other):
        return DiceBitwiseShift(other, self)

    def __mod__(self, other):
        return DiceModulus(self, other)

    def __rmod__(self, other):
        return DiceModulus(other, self)

    def __pow__(self, other):
        return DicePower(self, other)

    def __rpow__(self, other):
        return DicePower(other, self)

    def __divmod__(self, other):
        return DiceDivMod(self, other)

    def __rdivmod__(self, other):
        return DiceDivMod(other, self)

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

class ScalarRollableSequence(RollableSequence):
    def __init__(self, items, *, scalar):
        self.__scalar = scalar
        super().__init__(items)

    @property
    def scalar(self):
        return self.__scalar

class Die(Rollable, HasConvention):
    def __init__(self, sides, convention=standard_die):
        sides = int(sides)
        if sides < 2:
            raise ValueError('There must be at least two sides.')

        self.__sides = sides
        HasConvention.__init__(self, convention)

    @property
    def sides(self):
        return self.__sides

    def _roll(self):
        return self.convention(random.randrange(1, self.sides + 1))

    def copy(self):
        return Die(self.sides)

    def __hash__(self):
        return hash((type(Die), self.convention, self.sides))

    def __str__(self):
        return ''.join(['d', str(self.sides)])

    def __repr__(self):
        return ''.join(['Die(', repr(self.sides), ')'])

class Dice(RollableSequence, HasConvention):
    def __new__(cls, num, rollable, convention=standard_dice):
        num = int(num)
        num = int(num)
        if num < 1:
            raise ValueError('There must be at least one rollable.')

        if isinstance(rollable, Dice):
            num = num * rollable.num
            rollable = rollable.die

        if num == 1:
            return rollable.copy()

        ret = super().__new__(cls)
        RollableSequence.__init__(ret, (rollable.copy() for i in range(num)))
        HasConvention.__init__(ret, convention)
        return ret

    def __init__(self, num, rollable, convention=standard_dice):
        pass

    def _roll(self):
        return self.convention(item() for item in self._group)

    @property
    def die(self):
        try:
            return self.__die

        except AttributeError:
            self.__die = self._group[0].copy()
            return self.__die

    @property
    def num(self):
        try:
            return self.__num

        except AttributeError:
            self.__num = len(self)
            return self.__num

    def copy(self):
        return Dice(self.num, self.die.copy())

    def __hash__(self):
        return hash((type(self), self.convention) + self._group)

    def __str__(self):
        return ''.join([str(self.num), str(self.die)])

    def __repr__(self):
        return ''.join(['Dice(', repr(self.num), ', ', repr(self.die), ')'])

class DiceAdder(ScalarRollableSequence, Parenthesize):
    def __new__(cls, *adders, scalar=0):
        mappings = {
            type_: [item for item in adders if type(item) is type_]
            for type_ in {type(item) for item in adders}
        }
        while DiceAdder in mappings:
            dice_adders = mappings.pop(DiceAdder)
            adder_items, scalars = zip(*[
                (
                    adder._group,
                    adder.scalar
                )
                for adder in dice_adders
            ])
            adder_items = tuple(item for group in adder_items for item in group)
            scalar += sum(item_scalar for item_scalar in scalars)
            for type_, items in (
                (type_, [item for item in adder_items if type(item) is type_])
                for type_ in {type(item) for item in adder_items}
            ):
                if type_ in mappings:
                    mappings[type_].extend(items)

                else:
                    mappings[type_] = items

        merged_adders = []
        if Dice in mappings:
            dice_items = mappings.pop(Dice)
            items = {
                dtype: sum(
                    len(item)
                    for item in dice_items
                    if hash(item.die) == hash(dtype)
                )
                for dtype in {item.die for item in dice_items}
            }
        else:
            items = {}

        if Die in mappings:
            die_items = mappings.pop(Die)

            for dtype, count in (
                (
                    set_item,
                    len([
                        item
                        for item in die_items
                        if hash(item) == hash(set_item)
                    ])
                )
                for set_item in set(die_items)
            ):
                items[dtype] = items.get(dtype, 0) + count

        merged_adders.extend(
            (Dice(count, die) if count > 1 else die)
            for die, count in items.items()
        )

        if DiceMultiplier in mappings:
            multiplier_items = mappings.pop(DiceMultiplier)
            merged_adders.extend([
                DiceMultiplier(
                    DiceAdder(*[
                        elem
                        for item in multiplier_items
                        for group in item._group
                        for elem in group
                        if item.scalar == ms
                    ]),
                    scalar=ms
                )
                for ms in {
                    item.scalar
                    for item in multiplier_items
                }
            ])

        if mappings:
            rollable_items, scalars = zip(*[
                (
                    items if is_rollable else None,
                    sum(items) if not is_rollable else None
                )
                for items, is_rollable in (
                    (
                        items,
                        issubclass(type_, Rollable)
                    )
                    for type_, items in mappings.items()
                )
            ])


            merged_adders.extend(
                item
                for group in (
                    items
                    for items in rollable_items
                    if items is not None
                )
                for item in group
            )
            scalar += sum(item for item in scalars if item is not None)

        if not scalar and len(merged_adders) == 1:
            ret = merged_adders[0]

        else:
            ret = super().__new__(cls)
            ScalarRollableSequence.__init__(
                ret,
                merged_adders,
                scalar=scalar
            )

        return ret

    def __init__(self, *adders, scalar=0):
        pass

    def _roll(self):
        return sum(item() for item in self._group) + self.scalar

    def copy(self):
        return DiceAdder(
            *[item.copy() for item in self._group],
            scalar=self.scalar
        )

    def __hash__(self):
        return hash((type(self), self.scalar) + self._group)

    def __str__(self):
        ret = ' + '.join(
            item.paren_str()
            if isinstance(item, Parenthesize)
            else str(item)
            for item in self._group
        )
        if self.scalar > 0:
            ret = ' + '.join([ret, str(self.scalar)])
        elif self.scalar < 0:
            ret = ' - '.join([ret, str(abs(self.scalar))])

        return ret

    def __repr__(self):
        ret = ', '.join(repr(item) for item in self._group)
        if self.scalar:
            ret = ', '.join([ret, repr(self.scalar)])

        return ''.join(['DiceAdder(', ret, ')'])


class DiceMultiplier(ScalarRollableSequence, Parenthesize):
    def __new__(cls, *multipliers, scalar=1):
        mappings = {
            type_: [item for item in multipliers if type(item) is type_]
            for type_ in {type(item) for item in multipliers}
        }

        while DiceMultiplier in mappings:
            dice_multipliers = mappings.pop(DiceMultiplier)
            multiplier_items, scalars = zip(*[
                (
                    multiplier._group,
                    multiplier.scalar
                )
                for multiplier in dice_multipliers
            ])
            multiplier_items = tuple(
                item
                for group in multiplier_items
                for item in group
            )
            scalar *= functools.reduce(operator.mul, scalars)
            for type_, items in (
                (
                    type_,
                    [
                        item
                        for item in multiplier_items
                        if type(item) is type_
                    ]
                )
                for type_ in {type(item) for item in multiplier_items}
            ):
                if type_ in mappings:
                    mappings[type_].extend(items)

                else:
                    mappings[type_] = items

        merged_multipliers = []

        if mappings:
            rollable_items, scalars = zip(*[
                (
                    items if is_rollable else None,

                    functools.reduce(operator.mul, items)
                    if not is_rollable
                    else None
                )
                for items, is_rollable in (
                    (
                        items,
                        issubclass(type_, Rollable)
                    )
                    for type_, items in mappings.items()
                )
            ])


            merged_multipliers.extend(
                item
                for group in (
                    items
                    for items in rollable_items
                    if items is not None
                )
                for item in group
            )
            scalar *= functools.reduce(
                operator.mul,
                (
                    item
                    for item in scalars
                    if item is not None
                ),
                1
            )

        if scalar == 1 and len(merged_multipliers) == 1:
            ret = merged_multipliers[0]

        else:
            ret = super().__new__(cls)
            ret.__scalar = scalar
            ScalarRollableSequence.__init__(
                ret,
                merged_multipliers,
                scalar=scalar
            )

        return ret

    def __init__(self, *multipliers, scalar=1):
        pass

    def _roll(self):
        return functools.reduce(
            operator.mul,
            (
                item()
                for item in self._group
            )
        ) * self.scalar

    def copy(self):
        return DiceMultiplier(
            *[item.copy() for item in self._group],
            scalar=self.scalar
        )

    def __hash__(self):
        return hash((type(self), self.scalar) + self._group)

    def __str__(self):
        if self.scalar == 0:
            ret = str(self.scalar)
        else:
            ret = ' * '.join(
                item.paren_str()
                if isinstance(item, Parenthesize)
                else str(item)
                for item in self._group
            )
            if self.scalar not in {-1, 0, 1}:
                ret = ' * '.join([ret, str(self.scalar)])
            elif self.scalar == -1:
                ret = ''.join(['-', ret])

        return ret

    def __repr__(self):
        if self.scalar == 0:
            ret = repr(self.scalar)
        else:
            ret = ', '.join(repr(item) for item in self._group)
            if self.scalar not in {0, 1}:
                ret = ', '.join([ret, repr(self.scalar)])

        return ''.join(['DiceMultiplier(', ret, ')'])

    def __abs__(self):
        return DiceMultiplier(*self._group, scalar=abs(self.scalar))


class DiceFloorDivider(Rollable, Parenthesize):
    def __new__(cls, numerator, denominator):
        if not denominator:
            raise ZeroDivisionError

        if isinstance(numerator, DiceFloorDivider):
            new_numerator = numerator.numerator
            new_denominator = numerator.denominator

        else:
            new_numerator = numerator
            new_denominator = 1

        if isinstance(denominator, DiceFloorDivider):
            new_numerator *= denominator.denominator
            new_denominator *= denominator.numerator

        else:
            new_denominator *= denominator

        numerator = new_numerator
        denominator = new_denominator

        if (
            isinstance(numerator, DiceMultiplier) and
            isinstance(denominator, DiceMultiplier)
        ):
            new_scalar = numerator.scalar / denominator.scalar
            numerator = DiceMultiplier(*numerator._group, scalar=new_scalar)
            denominator = DiceMultiplier(*denominator._group)

        elif not isinstance(denominator, Rollable) and denominator == 1:
            ret = numerator

        elif not isinstance(denominator, Rollable):
            ret = DiceMultiplier(numerator, scalar=1 / denominator)

        else:
            ret = super().__new__(cls)
            ret.__numerator = numerator
            ret.__denominator = denominator

        return ret

    def __init__(self, numerator, divisor):
        pass

    @property
    def numerator(self):
        return self.__numerator

    @property
    def denominator(self):
        return self.__denominator

    def _roll(self):
        try:
            numerator = self.numerator()
        except TypeError:
            numerator = self.numerator

        try:
            denominator = self.denominator()
        except TypeError:
            denominator = self.denominator

        return numerator // denominator

    def copy(self):
        try:
            numerator = self.numerator.copy()
        except AttributeError:
            numerator = self.numerator

        try:
            denominator = self.denominator.copy()
        except AttributeError:
            denominator = self.denominator

        return DiceFloorDivider(numerator, denominator)

    def __hash__(self):
        return hash(type(self), self.numerator, self.denominator)

    def __str__(self):
        return ' // '.join([
            self.numerator.paren_str()
            if isinstance(self.numerator, Parenthesize)
            else str(self.numerator),

            self.denominator.paren_str()
            if isinstance(self.denominator, Parenthesize)
            else str(self.denominator)
        ])

    def __repr__(self):
        return ''.join([
            'DiceFloorDivider(',
            ', '.join([
                repr(self.numerator),
                repr(self.denominator)
            ]),
            ')'
        ])


class DiceTrueDivider(Rollable, Parenthesize):
    def __new__(cls, numerator, denominator):
        if not denominator:
            raise ZeroDivisionError

        if isinstance(numerator, DiceTrueDivider):
            new_numerator = numerator.numerator
            new_denominator = numerator.denominator

        else:
            new_numerator = numerator
            new_denominator = 1

        if isinstance(denominator, DiceTrueDivider):
            new_numerator *= denominator.denominator
            new_denominator *= denominator.numerator

        else:
            new_denominator *= denominator

        numerator = new_numerator
        denominator = new_denominator

        if (
            isinstance(numerator, DiceMultiplier) and
            isinstance(denominator, DiceMultiplier)
        ):
            new_scalar = numerator.scalar / denominator.scalar
            numerator = DiceMultiplier(*numerator._group, scalar=new_scalar)
            denominator = DiceMultiplier(*denominator._group)

        elif not isinstance(denominator, Rollable) and denominator == 1:
            ret = numerator

        elif not isinstance(denominator, Rollable):
            ret = DiceMultiplier(numerator, scalar=1 / denominator)

        else:
            ret = super().__new__(cls)
            ret.__numerator = numerator
            ret.__denominator = denominator

        return ret

    def __init__(self, numerator, divisor):
        pass

    @property
    def numerator(self):
        return self.__numerator

    @property
    def denominator(self):
        return self.__denominator

    def _roll(self):
        try:
            numerator = self.numerator()
        except TypeError:
            numerator = self.numerator

        try:
            denominator = self.denominator()
        except TypeError:
            denominator = self.denominator

        return numerator / denominator

    def copy(self):
        try:
            numerator = self.numerator.copy()
        except AttributeError:
            numerator = self.numerator

        try:
            denominator = self.denominator.copy()
        except AttributeError:
            denominator = self.denominator

        return DiceTrueDivider(numerator, denominator)

    def __hash__(self):
        return hash(type(self), self.numerator, self.denominator)

    def __str__(self):
        return ' / '.join([
            self.numerator.paren_str()
            if isinstance(self.numerator, Parenthesize)
            else str(self.numerator),

            self.denominator.paren_str()
            if isinstance(self.denominator, Parenthesize)
            else str(self.denominator)
        ])

    def __repr__(self):
        return ''.join([
            'DiceTrueDivider(',
            ', '.join([
                repr(self.numerator),
                repr(self.denominator)
            ]),
            ')'
        ])


class DiceDivMod(Rollable):
    def __new__(cls, numerator, denominator):
        if not denominator:
            raise ZeroDivisionError

        if isinstance(numerator, DiceDivMod):
            new_numerator = numerator.numerator
            new_denominator = numerator.denominator

        else:
            new_numerator = numerator
            new_denominator = 1

        if isinstance(denominator, DiceDivMod):
            new_numerator *= denominator.denominator
            new_denominator *= denominator.numerator

        else:
            new_denominator *= denominator

        numerator = new_numerator
        denominator = new_denominator

        if (
            isinstance(numerator, DiceMultiplier) and
            isinstance(denominator, DiceMultiplier)
        ):
            new_scalar = numerator.scalar / denominator.scalar
            numerator = DiceMultiplier(*numerator._group, scalar=new_scalar)
            denominator = DiceMultiplier(*denominator._group)

        elif not isinstance(denominator, Rollable) and denominator == 1:
            ret = numerator

        elif not isinstance(denominator, Rollable):
            ret = DiceMultiplier(numerator, scalar=1 / denominator)

        else:
            ret = super().__new__(cls)
            ret.__numerator = numerator
            ret.__denominator = denominator

        return ret

    def __init__(self, numerator, divisor):
        pass

    @property
    def numerator(self):
        return self.__numerator

    @property
    def denominator(self):
        return self.__denominator

    def _roll(self):
        try:
            numerator = self.numerator()
        except TypeError:
            numerator = self.numerator

        try:
            denominator = self.denominator()
        except TypeError:
            denominator = self.denominator

        return divmod(numerator, denominator)

    def copy(self):
        try:
            numerator = self.numerator.copy()
        except AttributeError:
            numerator = self.numerator

        try:
            denominator = self.denominator.copy()
        except AttributeError:
            denominator = self.denominator

        return DiceDivMod(numerator, denominator)

    def __hash__(self):
        return hash(type(self), self.numerator, self.denominator)

    def __str__(self):
        return ''.join([
            'divmod(',
            ', '.join([
                self.numerator.paren_str()
                if isinstance(self.numerator, Parenthesize)
                else str(self.numerator),

                self.denominator.paren_str()
                if isinstance(self.denominator, Parenthesize)
                else str(self.denominator)
            ]),
            ')',
        ])

    def __repr__(self):
        return ''.join([
            'DiceDivMod(',
            ', '.join([
                repr(self.numerator),
                repr(self.denominator)
            ]),
            ')'
        ])


class DiceBitwiseAnd(ScalarRollableSequence, Parenthesize):
    def __new__(cls, *values, scalar=-1):
        mappings = {
            type_: [item for item in values if type(item) is type_]
            for type_ in {type(item) for item in values}
        }

        while DiceBitwiseAnd in mappings:
            dice_values = mappings.pop(DiceBitwiseAnd)
            value_items, scalars = zip(*[
                (
                    value._group,
                    value.scalar
                )
                for value in dice_values
            ])
            value_items = tuple(
                item
                for group in value_items
                for item in group
            )
            scalar |= functools.reduce(
                operator.and_,
                (
                    item
                    for item in scalars
                    if item is not None
                ),
                -1
            )


            for type_, items in (
                (
                    type_,
                    [
                        item
                        for item in value_items
                        if type(item) is type_
                    ]
                )
                for type_ in {type(item) for item in value_items}
            ):
                if type_ in mappings:
                    mappings[type_].extend(items)

                else:
                    mappings[type_] = items

        merged_adders = []

        if mappings:
            rollable_items, scalars = zip(*[
                (
                    items if is_rollable else None,

                    functools.reduce(operator.and_, items)
                    if not is_rollable
                    else None
                )
                for items, is_rollable in (
                    (
                        items,
                        issubclass(type_, Rollable)
                    )
                    for type_, items in mappings.items()
                )
            ])


            merged_adders.extend(
                item
                for group in (
                    items
                    for items in rollable_items
                    if items is not None
                )
                for item in group
            )
            scalar &= functools.reduce(
                operator.and_,
                (
                    item
                    for item in scalars
                    if item is not None
                ),
                -1
            )


        if not scalar:
            ret = 0

        elif len(merged_values) == 1:
            ret = merged_values[0]

        else:
            ret = super().__new__(cls)
            ScalarRollableSequence.__init__(
                ret,
                merged_values,
                scalar=scalar
            )

        return ret

    def __init__(self, *values, scalar=-1):
        pass

    def _roll(self):
        ret = functools.reduce(
            operator.and_,
            (
                item()
                for item in self._group
            )
        )
        if self.scalar is not None:
            ret &= self.scalar

        return ret

    def copy(self):
        return DiceBitwiseAnd(
            *[item.copy() for item in self._group],
            scalar=self.scalar
        )

    def __hash__(self):
        return hash((type(self), self.scalar) + self._group)

    def __str__(self):
        if self.scalar == 0:
            ret = str(self.scalar)
        else:
            ret = ' & '.join(
                item.paren_str()
                if isinstance(item, Parenthesize)
                else str(item)
                for item in self._group
            )
            if self.scalar != -1:
                ret = ' & '.join([ret, str(self.scalar)])

        return ret

    def __repr__(self):
        if self.scalar == 0:
            ret = repr(self.scalar)
        else:
            ret = ', '.join(repr(item) for item in self._group)
            if self.scalar != -1:
                ret = ', '.join([ret, repr(self.scalar)])

        return ''.join(['DiceBitwiseAnd(', ret, ')'])


class DiceBitwiseOr(ScalarRollableSequence, Parenthesize):
    def __new__(cls, *values, scalar=0):
        mappings = {
            type_: [item for item in values if type(item) is type_]
            for type_ in {type(item) for item in values}
        }

        while DiceBitwiseOr in mappings:
            dice_values = mappings.pop(DiceBitwiseOr)
            value_items, scalars = zip(*[
                (
                    value._group,
                    value.scalar
                )
                for value in dice_values
            ])
            value_items = tuple(
                item
                for group in value_items
                for item in group
            )
            scalar |= functools.reduce(
                operator.or_,
                (
                    item
                    for item in scalars
                    if item is not None
                ),
                0
            )

            for type_, items in (
                (
                    type_,
                    [
                        item
                        for item in value_items
                        if type(item) is type_
                    ]
                )
                for type_ in {type(item) for item in value_items}
            ):
                if type_ in mappings:
                    mappings[type_].extend(items)

                else:
                    mappings[type_] = items

        merged_values = []

        if mappings:
            rollable_items, scalars = zip(*[
                (
                    items if is_rollable else None,

                    functools.reduce(operator.or_, items)
                    if not is_rollable
                    else None
                )
                for items, is_rollable in (
                    (
                        items,
                        issubclass(type_, Rollable)
                    )
                    for type_, items in mappings.items()
                )
            ])


            merged_values.extend(
                item
                for group in (
                    items
                    for items in rollable_items
                    if items is not None
                )
                for item in group
            )
            scalar |= functools.reduce(
                operator.or_,
                (
                    item
                    for item in scalars
                    if item is not None
                ),
                0
            )

        if len(merged_values) == 1:
            ret = merged_values[0]

        else:
            ret = super().__new__(cls)
            ScalarRollableSequence.__init__(
                ret,
                merged_values,
                scalar=scalar
            )

        return ret

    def __init__(self, *values, scalar):
        pass

    def _roll(self):
        ret = functools.reduce(
            operator.or_,
            (
                item()
                for item in self._group
            )
        ) | self.scalar

        return ret

    def copy(self):
        return DiceBitwiseOr(
            *[item.copy() for item in self._group],
            scalar=self.scalar
        )

    def __hash__(self):
        return hash((type(self), self.scalar) + self._group)

    def __str__(self):
        ret = ' | '.join(
            item.paren_str()
            if isinstance(item, Parenthesize)
            else str(item)
            for item in self._group
        )
        if self.scalar:
            ret = ' | '.join([ret, str(self.scalar)])

        return ret

    def __repr__(self):
        ret = ', '.join(repr(item) for item in self._group)
        if self.scalar is not None:
            ret = ', '.join([ret, repr(self.scalar)])

        return ''.join(['DiceBitwiseOr(', ret, ')'])


class DiceBitwiseXOr(ScalarRollableSequence, Parenthesize):
    def __new__(cls, *values, scalar=0):
        mappings = {
            type_: [item for item in values if type(item) is type_]
            for type_ in {type(item) for item in values}
        }

        while DiceBitwiseXOr in mappings:
            dice_values = mappings.pop(DiceBitwiseXOr)
            value_items, scalars = zip(*[
                (
                    value._group,
                    value.scalar
                )
                for value in dice_values
            ])
            value_items = tuple(
                item
                for group in value_items
                for item in group
            )
            scalar ^= functools.reduce(
                operator.xor_,
                (
                    item
                    for item in scalars
                    if item is not None
                ),
                0
            )

            for type_, items in (
                (
                    type_,
                    [
                        item
                        for item in value_items
                        if type(item) is type_
                    ]
                )
                for type_ in {type(item) for item in value_items}
            ):
                if type_ in mappings:
                    mappings[type_].extend(items)

                else:
                    mappings[type_] = items

        merged_values = []

        if mappings:
            rollable_items, scalars = zip(*[
                (
                    items if is_rollable else None,

                    functools.reduce(operator.xor_, items)
                    if not is_rollable
                    else None
                )
                for items, is_rollable in (
                    (
                        items,
                        issubclass(type_, Rollable)
                    )
                    for type_, items in mappings.items()
                )
            ])


            merged_values.extend(
                item
                for group in (
                    items
                    for items in rollable_items
                    if items is not None
                )
                for item in group
            )
            scalar ^= functools.reduce(
                operator.or_,
                (
                    item
                    for item in scalars
                    if item is not None
                ),
                0
            )

        if len(merged_values) == 1:
            ret = merged_values[0]

        else:
            ret = super().__new__(cls)
            ScalarRollableSequence.__init__(
                ret,
                merged_values,
                scalar=scalar
            )

        return ret

    def __init__(self, *values, scalar):
        pass

    def _roll(self):
        ret = functools.reduce(
            operator.xor_,
            (
                item()
                for item in self._group
            )
        ) ^ self.scalar

        return ret

    def copy(self):
        return DiceBitwiseXOr(
            *[item.copy() for item in self._group],
            scalar=self.scalar
        )

    def __hash__(self):
        return hash((type(self), self.scalar) + self._group)

    def __str__(self):
        ret = ' ^ '.join(
            item.paren_str()
            if isinstance(item, Parenthesize)
            else str(item)
            for item in self._group
        )
        if self.scalar:
            ret = ' ^ '.join([ret, str(self.scalar)])

        return ret

    def __repr__(self):
        ret = ', '.join(repr(item) for item in self._group)
        if self.scalar is not None:
            ret = ', '.join([ret, repr(self.scalar)])

        return ''.join(['DiceBitwiseXOr(', ret, ')'])


class DiceBitwiseInvert(Rollable):
    def __new__(cls, element):
        if isinstance(element, DiceBitwiseInvert):
            ret = element._element

        else:
            ret = super().__new__(cls)
            ret.__element = element

        return ret

    def __init__(self, element):
        pass

    @property
    def _element(self):
        return self.__element

    def copy(self):
        return DiceBitwiseInvert(self._element.copy())

    def _roll(self):
        return ~(self._element())

    def __hash__(self):
        return hash((type(self), self._element))

    def __str__(self):
        return ''.join([
            '~',
            self._element.paren_str()
            if isinstance(self._element, Parenthesize)
            else str(self._element)
        ])

    def __repr__(self):
        return ''.join(['DiceBitwiseInvert(', repr(self._element), ')'])


class DiceBitwiseShift(Rollable, Parenthesize):
    def __new__(cls, value, shift):
        self.__value = value
        self.__shift = shift

    @property
    def _value(self):
        return self.__value

    @property
    def _shift(self):
        return self.__shift

    def _roll(self):
        try:
            value = self._value()
        except TypeError:
            value = self._value

        try:
            shift = self._shift()
        except TypeError:
            shift = self._shift

        if shift < 0:
            return value << abs(shift)
        else:
            return value >> abs(shift)

    def copy(self):
        try:
            value = self._value.copy()
        except AttributeError:
            value = self._value

        try:
            shift = self._shift.copy()
        except AttributeError:
            shift = self._shift

        return DiceBitwiseShift(value, shift)

    def __hash__(self):
        return hash((type(self), self._value, self._shift))

    def __str__(self):
        return (' << ' if int(self._shift) < 0 else ' >> ').join([
            self._value.paren_str()
            if isinstance(self._value, Parenthesize)
            else str(self._value),

            self._shift.paren_str()
            if isinstance(abs(self._shift), Parenthesize)
            else str(abs(self._shift))
        ])

    def __repr__(self):
        return ''.join([
            'DiceBitwiseShift(',
            ', '.join([
                repr(self._value),
                repr(self._shift)
            ]),
            ')'
        ])


class DiceAbs(Rollable):
    def __new__(cls, element):
        if isinstance(element, DiceAbs):
            ret = element

        else:
            ret = super().__new__(cls)
            ret.__element = element

        return ret

    def __init__(self, element):
        pass

    @property
    def _element(self):
        return self.__element

    def copy(self):
        return DiceAbs(self._element.copy())

    def _roll(self):
        return abs(self._element())

    def __hash__(self):
        return hash((type(self), self._element))

    def __str__(self):
        return ''.join([
            'abs(',
            str(self._element),
            ')'
        ])

    def __repr__(self):
        return ''.join(['DiceAbs(', repr(self._element), ')'])


class DiceTrunc(Rollable):
    def __new__(cls, element):
        if isinstance(element, DiceTrunc):
            ret = element

        else:
            ret = super().__new__(cls)
            ret.__element = element

        return ret

    def __init__(self, element):
        pass

    @property
    def _element(self):
        return self.__element

    def copy(self):
        return DiceTrunc(self._element.copy())

    def _roll(self):
        return math.trunc(self._element())

    def __hash__(self):
        return hash((type(self), self._element))

    def __str__(self):
        return ''.join([
            'math.trunc(',
            str(self._element),
            ')'
        ])

    def __repr__(self):
        return ''.join(['DiceTrunc(', repr(self._element), ')'])


class DiceFloor(Rollable):
    def __new__(cls, element):
        if isinstance(element, DiceFloor):
            ret = element

        else:
            ret = super().__new__(cls)
            ret.__element = element

        return ret

    def __init__(self, element):
        pass

    @property
    def _element(self):
        return self.__element

    def copy(self):
        return DiceFloor(self._element.copy())

    def _roll(self):
        return math.floor(self._element())

    def __hash__(self):
        return hash((type(self), self._element))

    def __str__(self):
        return ''.join([
            'math.floor(',
            str(self._element),
            ')'
        ])

    def __repr__(self):
        return ''.join(['DiceFloor(', repr(self._element), ')'])


class DiceCeil(Rollable):
    def __new__(cls, element):
        if isinstance(element, DiceCeil):
            ret = element

        else:
            ret = super().__new__(cls)
            ret.__element = element

        return ret

    def __init__(self, element):
        pass

    @property
    def _element(self):
        return self.__element

    def copy(self):
        return DiceCeil(self._element.copy())

    def _roll(self):
        return math.ceil(self._element())

    def __hash__(self):
        return hash((type(self), self._element))

    def __str__(self):
        return ''.join([
            'math.ceil(',
            str(self._element),
            ')'
        ])

    def __repr__(self):
        return ''.join(['DiceCeil(', repr(self._element), ')'])


class DiceRound(Rollable):
    def __new__(cls, element, ndigits=0):
        if isinstance(element, DiceRound):
            if element.ndigits < ndigits:
                ndigits = element.ndigits
            element = element._element

        ret = super().__new__(cls)
        ret.__element = element
        ret.__ndigits = ndigits

        return ret

    def __init__(self, element):
        pass

    @property
    def _element(self):
        return self.__element

    @property
    def _ndigits(self):
        return self.__ndigits

    def copy(self):
        return DiceRound(self._element.copy(), self._ndigits)

    def _roll(self):
        return round(self._element(), self._ndigits)

    def __hash__(self):
        return hash((type(self), self._element, self._ndigits))

    def __str__(self):
        elems = [
            self._element.paren_str()
            if isinstance(self._element, Parenthesize)
            else str(self._element)
        ]
        if self._ndigits:
            elems += [str(self._ndigits)]

        return ''.join(['random(', ', '.join(elems), ')'])

    def __repr__(self):
        return ''.join([
            'DiceRound(',
            repr(self._element),
            ', ndigits=',
            repr(self._ndigits),
            ')'
        ])


class DiceModulus(Rollable, Parenthesize):
    def __new__(cls, numerator, denominator):
        if not denominator:
            raise ZeroDivisionError

        if isinstance(numerator, DiceModulus):
            new_numerator = numerator.numerator
            new_denominator = numerator.denominator

        else:
            new_numerator = numerator
            new_denominator = 1

        if isinstance(denominator, DiceModulus):
            new_denominator *= denominator.numerator
            new_numerator *= denominator.denominator

        else:
            new_denominator *= denominator

        if (
            isinstance(numerator, (Dice, Die)) and
            not isinstance(denominator, Rollable)
        ):
            if isinstance(numerator, Dice):
                rolls = len(numerator)
                sides = numerator.die.sides
            else:
                rolls = 1
                sides = numerator.sides

            if not sides % denominator:
                sides = denominator
                return Dice(rolls, Die(sides)) - 1


        ret = super().__new__(cls)
        ret.__numerator = new_numerator
        ret.__denominator = new_denominator
        return ret

    def __init__(self, numerator, denominator):
        pass

    @property
    def numerator(self):
        return self.__numerator

    @property
    def denominator(self):
        return self.__denominator

    def _roll(self):
        try:
            numerator = self.numerator()
        except TypeError:
            numerator = self.numerator

        try:
            denominator = self.denominator()
        except TypeError:
            denominator = self.denominator

        return numerator % denominator

    def copy(self):
        try:
            numerator = self.numerator.copy()
        except AttributeError:
            numerator = self.numerator

        try:
            denominator = self.denominator.copy()
        except AttributeError:
            denominator = self.denominator

        return DiceModulus(numerator, denominator)

    def __hash__(self):
        return hash(type(self), self.numerator, self.denominator)

    def __str__(self):
        return ' % '.join([
            self.numerator.paren_str()
            if isinstance(self.numerator, Parenthesize)
            else str(self.numerator),

            self.denominator.paren_str()
            if isinstance(self.denominator, Parenthesize)
            else str(self.denominator)
        ])

    def __repr__(self):
        return ''.join([
            'DiceModulus(',
            ', '.join([
                repr(self.numerator),
                repr(self.denominator)
            ]),
            ')'
        ])


class DicePower(Rollable, Parenthesize):
    @classmethod
    def __get_pieces(cls, item):
        if isinstance(item, DicePower):
            bbase, bexp = cls.__get_pieces(item._base)
            ebase, eexp = cls.__get_pieces(item._exponent)
            base = bbase
            exp = []
            if bexp:
                exp.extend(bexp)

            if ebase:
                exp.append(ebase)

            if eexp:
                exp.extend(eexp)

            return base, exp

        else:
            return item, []

    def __new__(cls, base, exponent):
        bbase, bexp = cls.__get_pieces(base)
        ebase, eexp = cls.__get_pieces(exponent)

        base = bbase
        group = []

        if bexp:
            group.extend(bexp)

        if ebase:
            group.append(ebase)

        if eexp:
            group.extend(eexp)

        rollables, scalars = zip(*[
            (
                item if is_rollable else None,
                item if not is_rollable else None
            )
            for item, is_rollable in (
                (
                    item,
                    isinstance(item, Rollable)
                )
                for item in group
            )
        ])
        rollables = [item for item in rollables if item is not None]
        scalar = functools.reduce(
            operator.mul,
            (item for item in scalars if item is not None),
            1
        )

        if rollables:
            exponent = DiceMultiplier(*rollables, scalar=scalar)
        else:
            exponent = scalar

        if not isinstance(base, Rollable) and base == 0:
            ret = 0

        elif (
            (not isinstance(base, Rollable) and base == 1) or
            (not isinstance(exponent, Rollable) and exponent == 0)
        ):
            ret = 1

        elif not isinstance(exponent, Rollable) and exponent == 1:
            ret = base

        elif not isinstance(exponent, Rollable) and exponent == -1:
            ret = DiceTrueDivider(1, base)

        else:
            ret = super().__new__(cls)
            ret.__base = base
            ret.__exponent = exponent

        return ret

    def __init__(self, base, exponent):
        pass

    @property
    def _base(self):
        return self.__base

    @property
    def _exponent(self):
        return self.__exponent

    def _roll(self):
        try:
            base = self._base()
        except TypeError:
            base = self._base

        try:
            exponent = self._exponent()
        except TypeError:
            exponent = self._exponent

        return base ** exponent

    def copy(self):
        try:
            base = self._base.copy()
        except AttributeError:
            base = self._base

        try:
            exponent = self._exponent.copy()
        except AttributeError:
            exponent = self._exponent

        return DicePower(base, exponent)

    def __hash__(self):
        return hash((type(self), self._base, self._exponent))

    def __str__(self):
        return ' ** '.join([
            self._base.paren_str()
            if isinstance(self._base, Parenthesize)
            else str(self._base),

            self._exponent.paren_str()
            if isinstance(self._exponent, Parenthesize)
            else str(self._exponent)
        ])

    def __repr__(self):
        return ''.join([
            'DicePower(',
            ', '.join([
                repr(self._base),
                repr(self._exponent)
            ]),
            ')'
        ])

class DiceConfig(config.Base):
    def __init__(self):
        super().__init__()

        self.register_attr(
            'd',
            lambda: Die,
            Die.__doc__
        )

        self.register_attr(
            'd2',
            lambda: Die(2),
            '2-sided die'
        )

        self.register_attr(
            'd3',
            lambda: Die(3),
            '3-sided die'
        )

        self.register_attr(
            'd4',
            lambda: Die(4),
            '4-sided die'
        )

        self.register_attr(
            'd6',
            lambda: Die(6),
            '6-sided die'
        )

        self.register_attr(
            'd8',
            lambda: Die(8),
            '8-sided die'
        )

        self.register_attr(
            'd10',
            lambda: Die(10),
            '10-sided die'
        )

        self.register_attr(
            'd12',
            lambda: Die(12),
            '12-sided die'
        )

        self.register_attr(
            'd20',
            lambda: Die(20),
            '20-sided die'
        )

        self.register_attr(
            'd100',
            lambda: Die(100),
            '100-sided die (percentile)'
        )