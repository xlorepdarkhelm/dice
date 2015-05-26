#!/usr/bin/env python3

import abc
import functools
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


@functools.total_ordering
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

    def __sub__(self, other):
        return operator.add(self, -other)

    def __rsub__(self, other):
        return operator.add(-self, other)

    def __mul__(self, other):
        return DiceMultiplier(self, other)

    def __rmul__(self, other):
        return DiceMultiplier(other, self)
        
    def __truediv__(self, other):
        return DiceDivider(self, other, truediv=True)
        
    def __rtruediv(self, other):
        return DiceDivider(other, self, truediv=True)

    def __floordiv__(self, other):
        return DiceDivider(self, other, truediv=False)
        
    def __rfloordiv(self, other):
        return DiceDivider(other, self, truediv=False)

    def __pos__(self):
        return self

    def __neg__(self):
        return DiceMultiplier(self, scalar=-1)

    def __invert__(self):
        return DiceMultiplier(self, scalar=-1)

    def __abs__(self):
        return self

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

class DiceAdder(RollableSequence):
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
            ret.__scalar = scalar
            RollableSequence.__init__(ret, merged_adders)

        return ret

    def __init__(self, *adders, scalar=0):
        pass

    @property
    def scalar(self):
        return self.__scalar

    def _roll(self):
        return sum(item() for item in self._group) + self.scalar

    def copy(self):
        return DiceAdder(*self._group, scalar=self.scalar)

    def __hash__(self):
        return hash((type(self), self.scalar) + self._group)

    def __str__(self):
        ret = ' + '.join(
            ''.join(['(', str(item), ')'])
            if isinstance(item, DiceMultiplier)
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


class DiceMultiplier(RollableSequence):
    def __new__(cls, *multipliers, scalar=1):
        mappings = {
            type_: [item for item in multipliers if type(item) is type_]
            for type_ in {type(item) for item in multipliers}
        }

        merged_multipliers = []

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
            RollableSequence.__init__(ret, merged_multipliers)

        return ret

    def __init__(self, *multipliers, scalar=1):
        pass

    @property
    def scalar(self):
        return self.__scalar

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
                if isinstance(item, DiceAdder)
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
            if isinstance(self.numerator, (DiceMultiplier, DiceAdder))
            else str(self.numerator),
            
            ''.join(['(', str(self.denominator), ')'])
            if isinstance(self.denominator, (DiceMultiplier, DiceAdder))
            else str(self.denominator)
        ])
        
    def __repr__(self):
        return ''.join([
            'DiceDivider(',
            ', '.join([
                repr(self.numerator),
                repr(self.denominator),
                '='.join(['truediv', self._truediv])
            ])
            ')'
        ])