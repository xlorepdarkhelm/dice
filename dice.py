#!/usr/bin/env python3

import abc
import functools
import math
import numbers
import operator
import random
import collections.abc


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
        return DiceDivider(self, other, truediv=True)

    def __rtruediv__(self, other):
        return DiceDivider(other, self, truediv=True)

    def __floordiv__(self, other):
        return DiceDivider(self, other, truediv=False)

    def __rfloordiv__(self, other):
        return DiceDivider(other, self, truediv=False)

    def __pos__(self):
        return self.copy()

    def __neg__(self):
        return DiceMultiplier(self, scalar=-1)

    def __invert__(self):
        return -self

    def __abs__(self):
        return self.copy()

    def __trunc__(self):
        return math.trunc(self.last)

    def __ceil__(self):
        return math.ceil(self.last)

    def __floor__(self):
        return math.floor(self.last)

    def __round__(self, ndigits=0):
        return round(self.last, ndigits)

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
        return int(self) << other

    def __rlshift__(self, other):
        return other << int(self)

    def __rshift__(self, other):
        return int(self) >> other

    def __rrshift__(self, other):
        return other >> int(self)

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

class CollectedRollableSequence(RollableSequence):
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
    def __init__(self, num, rollable, convention=standard_dice):
        num = int(num)
        if num < 1:
            raise ValueError('There must be at least one rollable.')

        if isinstance(rollable, Dice):
            num = num * len(rollable)
            rollable = rollable.die

        RollableSequence.__init__(self, (rollable.copy() for i in range(num)))
        HasConvention.__init__(self, convention)


    def _roll(self):
        return self.convention(item() for item in self._group)

    @property
    def die(self):
        try:
            return self.__die

        except AttributeError:
            self.__die = self._group[0].copy()
            return self.__die

    def copy(self):
        return Dice(len(self), self.die)

    def __hash__(self):
        return hash((type(self), self.convention) + self._group)

    def __str__(self):
        return ''.join([str(len(self)), str(self.die)])

    def __repr__(self):
        return ''.join(['Dice(', repr(len(self)), ', ', repr(self.die), ')'])

class DiceAdder(CollectedRollableSequence):
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
                    for item in items
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
            CollectedRollableSequence.__init__(ret, merged_adders, scalar=scalar)

        return ret

    def __init__(self, *adders, scalar=0):
        pass

    def _roll(self):
        return sum(item() for item in self._group) + self.scalar

    def copy(self):
        return DiceAdder(*self._group, scalar=self.scalar)

    def __hash__(self):
        return hash((type(self), self.scalar) + self._group)

    def __str__(self):
        ret = ' + '.join(
            ''.join(['(', str(item), ')'])
            if isinstance(item, CollectedRollableSequence)
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


class DiceMultiplier(CollectedRollableSequence):
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
            CollectedRollableSequence.__init__(ret, merged_multipliers, scalar=scalar)

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
        return DiceMultiplier(*self._group, scalar=self.scalar)

    def __hash__(self):
        return hash((type(self), self.scalar) + self._group)

    def __str__(self):
        if self.scalar == 0:
            ret = str(self.scalar)
        else:
            ret = ' * '.join(
                ''.join(['(', str(item), ')'])
                if isinstance(item, CollectedRollableSequence)
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


def DiceDivider(Rollable):
    def __new__(self, numerator, denominator, *, truediv=True):
        if not denominator:
            raise ZeroDivisionError

        if (
            isinstance(numerator, DiceMultiplier) and
            isinstance(denominator, DiceMultiplier)
        ):
            new_scalar = numerator.scalar / denominator.scalar
            numerator = DiceMultiplier(*numerator._group, scalar=new_scalar)
            denominator = DiceMultiplier(*denominator._group)

        elif not isinstance(denominator, Rollable) and denominator == 1:
            return numerator

        elif not isinstance(denominator, Rollable):
            return DiceMultiplier(numerator, scalar=1 / denominator)

        else:
            ret = super().__new__(cls)
            ret.__numerator = numerator
            ret.__denominator = denominator
            ret.__truediv = truediv
            return ret

    def __init__(self, numerator, divisor):
        pass

    def __float__(self):
        if self._truediv:
            return float(self.numerator) / float(self.denominator)

        else:
            return int(float(self.numerator) // float(self.denominator))

    @property
    def numerator(self):
        return self.__numerator

    @property
    def denominator(self):
        return self.__denominator

    def _roll(self):
        try:
            self.numerator._roll()
        except AttributeError:
            pass

        try:
            self.denominator._roll()
        except AttributeError:
            pass

        return float(self)

    def _truediv(self):
        return self.__truediv

    def __hash__(self):
        return hash(type(self), self.numerator, self.denominator)

    def __str__(self):
        return (' / ' if self._truediv else ' // ').join([
            ''.join(['(', str(self.numerator), ')'])
            if isinstance(self.numerator, CollectedRollableSequence)
            else str(self.numerator),

            ''.join(['(', str(self.denominator), ')'])
            if isinstance(self.denominator, CollectedRollableSequence)
            else str(self.denominator)
        ])

    def __repr__(self):
        return ''.join([
            'DiceDivider(',
            ', '.join([
                repr(self.numerator),
                repr(self.denominator),
                '='.join(['truediv', self._truediv])
            ]),
            ')'
        ])


class DiceBitwiseAnd(CollectedRollableSequence):
    def __new__(self, *values, scalar=None):
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
            scalars = [item for item in scalars if item is not None]
            if scalars:
                if scalar is None:
                    scalar = functools.reduce(operator.and_, scalars)
                else:
                    scalar |= functools.reduce(operator.and_, scalars)


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
            scalars = [item for item in scalars if item is not None]
            if scalars:
                if scalar is None:
                    scalar = functools.reduce(operator.and_, scalars)
                else:
                    scalar |= functools.reduce(operator.and_, scalars)


        if not scalar:
            ret = 0

        elif len(merged_values) == 1:
            ret = merged_values[0]

        else:
            ret = super().__new__(cls)
            CollectedRollableSequence.__init__(ret, merged_values, scalar=scalar)

        return ret

    def __init__(self, *values, scalar=1):
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
        return DiceBitwiseAnd(*self._group, scalar=self.scalar)

    def __hash__(self):
        return hash((type(self), self.scalar) + self._group)

    def __str__(self):
        if self.scalar is not None and self.scalar == 0:
            ret = str(self.scalar)
        else:
            ret = ' & '.join(
                ''.join(['(', str(item), ')'])
                if isinstance(item, CollectedRollableSequence)
                else str(item)
                for item in self._group
            )
            if self.scalar is not None:
                ret = ' & '.join([ret, str(self.scalar)])

        return ret

    def __repr__(self):
        if self.scalar is not None and self.scalar == 0:
            ret = repr(self.scalar)
        else:
            ret = ', '.join(repr(item) for item in self._group)
            if self.scalar is not None:
                ret = ', '.join([ret, repr(self.scalar)])

        return ''.join(['DiceBitwiseAnd(', ret, ')'])


class DiceBitwiseOr(CollectedRollableSequence):
    def __new__(self, *values, scalar=0):
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
            CollectedRollableSequence.__init__(ret, merged_values, scalar=scalar)

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
        return DiceBitwiseOr(*self._group, scalar=self.scalar)

    def __hash__(self):
        return hash((type(self), self.scalar) + self._group)

    def __str__(self):
        ret = ' | '.join(
            ''.join(['(', str(item), ')'])
            if isinstance(item, CollectedRollableSequence)
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


class DiceBitwiseXOr(CollectedRollableSequence):
    def __new__(self, *values, scalar=0):
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
            CollectedRollableSequence.__init__(ret, merged_values, scalar=scalar)

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
        return DiceBitwiseXOr(*self._group, scalar=self.scalar)

    def __hash__(self):
        return hash((type(self), self.scalar) + self._group)

    def __str__(self):
        ret = ' ^ '.join(
            ''.join(['(', str(item), ')'])
            if isinstance(item, CollectedRollableSequence)
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
