# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=unused-argument
# pylint: disable=no-self-use
# pylint: disable=unnecessary-lambda

import abc
import functools
import unittest
from typing import Optional, List, Type  # pylint: disable=unused-import

import icontract
import tests.error
import tests.mock


class TestOK(unittest.TestCase):
    def test_with_condition_as_lambda(self):
        @icontract.ensure(lambda result, x: result > x)
        def some_func(x: int, y: int = 5) -> int:
            return x + y

        some_func(x=5)
        some_func(x=5, y=10)


class TestViolation(unittest.TestCase):
    def test_with_condition(self):
        @icontract.ensure(lambda result, x: result > x)
        def some_func(x: int, y: int = 5) -> int:
            return x - y

        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            some_func(x=1)
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual("result > x:\n"
                         "result was -4\n"
                         "x was 1", tests.error.wo_mandatory_location(str(violation_error)))

    def test_condition_as_function(self):
        def some_condition(result: int) -> bool:
            return result > 3

        @icontract.ensure(some_condition)
        def some_func(x: int) -> int:
            return x

        # Valid call
        some_func(x=4)

        # Invalid call
        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            some_func(x=1)
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual('some_condition: result was 1', tests.error.wo_mandatory_location(str(violation_error)))

    def test_condition_as_function_with_default_argument_value(self):
        def some_condition(result: int, y: int = 0) -> bool:
            return result > y

        @icontract.ensure(some_condition)
        def some_func(x: int) -> int:
            return x

        # Valid call
        some_func(x=1)

        # Invalid call
        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            some_func(x=-1)
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual('some_condition: result was -1', tests.error.wo_mandatory_location(str(violation_error)))

    def test_condition_as_function_with_default_argument_value_set(self):
        def some_condition(result: int, y: int = 0) -> bool:
            return result > y

        @icontract.ensure(some_condition)
        def some_func(x: int, y: int) -> int:
            return x

        # Valid call
        some_func(x=-1, y=-2)

        # Invalid call
        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            some_func(x=1, y=3)
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual('some_condition:\n'
                         'result was 1\n'
                         'y was 3', tests.error.wo_mandatory_location(str(violation_error)))

    def test_with_description(self):
        @icontract.ensure(lambda result, x: result > x, "expected summation")
        def some_func(x: int, y: int = 5) -> int:
            return x - y

        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            some_func(x=1)
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual("expected summation: result > x:\n"
                         "result was -4\n"
                         "x was 1", tests.error.wo_mandatory_location(str(violation_error)))

    def test_with_stacked_decorators(self):
        def mydecorator(f):
            @functools.wraps(f)
            def wrapped(*args, **kwargs):
                result = f(*args, **kwargs)
                return result

            return wrapped

        some_var = 1
        another_var = 2

        @mydecorator
        @icontract.ensure(lambda result, x: x < result + some_var)
        @icontract.ensure(lambda result, y: y > result + another_var)
        @mydecorator
        def some_func(x: int, y: int) -> int:
            return 100

        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            some_func(x=0, y=10)
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual("y > result + another_var:\n"
                         "another_var was 2\n"
                         "result was 100\n"
                         "y was 10", tests.error.wo_mandatory_location(str(violation_error)))

    def test_with_default_values_outer(self):
        @icontract.ensure(lambda result, c: result % c == 0)
        @icontract.ensure(lambda result, b: result < b)
        def some_func(a: int, b: int = 21, c: int = 2) -> int:
            return a

        # Check first the outer post condition
        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            some_func(a=13)
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual("result % c == 0:\n"
                         "c was 2\n"
                         "result was 13", tests.error.wo_mandatory_location(str(violation_error)))

        # Check the inner post condition
        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            some_func(a=36)
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual("result < b:\n"
                         "b was 21\n"
                         "result was 36", tests.error.wo_mandatory_location(str(violation_error)))

    def test_only_result(self):
        @icontract.ensure(lambda result: result > 3)
        def some_func(x: int) -> int:
            return 0

        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            some_func(x=10 * 1000)
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual("result > 3: result was 0", tests.error.wo_mandatory_location(str(violation_error)))


class TestError(unittest.TestCase):
    def test_as_type(self):
        @icontract.ensure(lambda result: result > 0, error=ValueError)
        def some_func(x: int) -> int:
            return x

        value_error = None  # type: Optional[ValueError]
        try:
            some_func(x=0)
        except ValueError as err:
            value_error = err

        self.assertIsNotNone(value_error)
        self.assertIsInstance(value_error, ValueError)
        self.assertEqual('result > 0: result was 0', tests.error.wo_mandatory_location(str(value_error)))

    def test_as_function(self):
        @icontract.ensure(lambda result: result > 0, error=lambda result: ValueError("result must be positive."))
        def some_func(x: int) -> int:
            return x

        value_error = None  # type: Optional[ValueError]
        try:
            some_func(x=0)
        except ValueError as err:
            value_error = err

        self.assertIsNotNone(value_error)
        self.assertIsInstance(value_error, ValueError)
        self.assertEqual('result must be positive.', str(value_error))

    def test_with_empty_args(self):
        @icontract.ensure(lambda result: result > 0, error=lambda: ValueError("result must be positive"))
        def some_func(x: int) -> int:
            return x

        value_error = None  # type: Optional[ValueError]
        try:
            some_func(x=0)
        except ValueError as err:
            value_error = err

        self.assertIsNotNone(value_error)
        self.assertIsInstance(value_error, ValueError)
        self.assertEqual('result must be positive', str(value_error))

    def test_with_different_args_from_condition(self):
        @icontract.ensure(
            lambda result: result > 0, error=lambda x, result: ValueError("x is {}, result is {}".format(x, result)))
        def some_func(x: int) -> int:
            return x

        value_error = None  # type: Optional[ValueError]
        try:
            some_func(x=0)
        except ValueError as err:
            value_error = err

        self.assertIsNotNone(value_error)
        self.assertIsInstance(value_error, ValueError)
        self.assertEqual('x is 0, result is 0', str(value_error))


class TestToggling(unittest.TestCase):
    def test_disabled(self):
        @icontract.ensure(lambda x, result: x > result, enabled=False)
        def some_func(x: int) -> int:
            return 123

        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            result = some_func(x=1234)
            self.assertEqual(123, result)
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNone(violation_error)


class TestInClass(unittest.TestCase):
    def test_postcondition_in_static_method(self):
        class SomeClass:
            @staticmethod
            @icontract.ensure(lambda result: result != 0)
            def some_func(x: int) -> int:
                return x

        result = SomeClass.some_func(x=1)
        self.assertEqual(1, result)

        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            _ = SomeClass.some_func(x=0)
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual('result != 0: result was 0', tests.error.wo_mandatory_location(str(violation_error)))

    def test_postcondition_in_class_method(self):
        class SomeClass:
            @classmethod
            @icontract.ensure(lambda result: result != 0)
            def some_func(cls: Type, x: int) -> int:
                return x

        result = SomeClass.some_func(x=1)
        self.assertEqual(1, result)

        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            _ = SomeClass.some_func(x=0)
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual('result != 0: result was 0', tests.error.wo_mandatory_location(str(violation_error)))

    def test_postcondition_in_abstract_static_method(self):
        class SomeAbstract(icontract.DBC):
            @staticmethod
            @icontract.ensure(lambda result: result != 0)
            def some_func(x: int) -> int:
                pass

        class SomeClass(SomeAbstract):
            @staticmethod
            def some_func(x: int) -> int:
                return x

        result = SomeClass.some_func(x=1)
        self.assertEqual(1, result)

        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            _ = SomeClass.some_func(x=0)
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual('result != 0: result was 0', tests.error.wo_mandatory_location(str(violation_error)))

    def test_postcondition_in_abstract_class_method(self):
        class Abstract(icontract.DBC):
            @classmethod
            @abc.abstractmethod
            @icontract.ensure(lambda result: result != 0)
            def some_func(cls: Type, x: int) -> int:
                pass

        class SomeClass(Abstract):
            @classmethod
            def some_func(cls: Type, x: int) -> int:
                return x

        result = SomeClass.some_func(x=1)
        self.assertEqual(1, result)

        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            _ = SomeClass.some_func(x=0)
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual('result != 0: result was 0', tests.error.wo_mandatory_location(str(violation_error)))

    def test_getter(self):
        class SomeClass:
            def __init__(self) -> None:
                self._some_prop = -1

            @property
            @icontract.ensure(lambda result: result > 0)
            def some_prop(self) -> int:
                return self._some_prop

        some_inst = SomeClass()

        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            _ = some_inst.some_prop
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual('result > 0: result was -1', tests.error.wo_mandatory_location(str(violation_error)))

    def test_setter(self):
        class SomeClass:
            @property
            def some_prop(self) -> int:
                return 0

            @some_prop.setter
            @icontract.ensure(lambda self: self.some_prop > 0)
            def some_prop(self, value: int) -> None:
                pass

            def __repr__(self):
                return self.__class__.__name__

        some_inst = SomeClass()

        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            some_inst.some_prop = -1
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual('self.some_prop > 0:\n'
                         'self was SomeClass\n'
                         'self.some_prop was 0', tests.error.wo_mandatory_location(str(violation_error)))

    def test_deleter(self):
        class SomeClass:
            def __init__(self) -> None:
                self._some_prop = -1

            @property
            def some_prop(self) -> int:
                return self._some_prop

            @some_prop.deleter
            @icontract.ensure(lambda self: self.some_prop > 0)
            def some_prop(self) -> None:
                pass

            def __repr__(self):
                return self.__class__.__name__

        some_inst = SomeClass()

        violation_error = None  # type: Optional[icontract.ViolationError]
        try:
            del some_inst.some_prop
        except icontract.ViolationError as err:
            violation_error = err

        self.assertIsNotNone(violation_error)
        self.assertEqual('self.some_prop > 0:\nself was SomeClass\nself.some_prop was -1',
                         tests.error.wo_mandatory_location(str(violation_error)))


class TestInvalid(unittest.TestCase):
    def test_invalid_postcondition_arguments(self):
        @icontract.ensure(lambda b, result: b > result)
        def some_function(a: int) -> None:  # pylint: disable=unused-variable
            pass

        type_err = None  # type: Optional[TypeError]
        try:
            some_function(a=13)
        except TypeError as err:
            type_err = err

        self.assertIsNotNone(type_err)
        self.assertEqual("The argument(s) of the postcondition have not been set: ['b']. "
                         "Does the original function define them? Did you supply them in the call?",
                         tests.error.wo_mandatory_location(str(type_err)))

    def test_conflicting_result_argument(self):
        @icontract.ensure(lambda a, result: a > result)
        def some_function(a: int, result: int) -> None:  # pylint: disable=unused-variable
            pass

        type_err = None  # type: Optional[TypeError]
        try:
            some_function(a=13, result=2)
        except TypeError as err:
            type_err = err

        self.assertIsNotNone(type_err)
        self.assertEqual("Unexpected argument 'result' in a function decorated with postconditions.", str(type_err))

    def test_conflicting_OLD_argument(self):
        @icontract.snapshot(lambda a: a[:])
        @icontract.ensure(lambda OLD, a: a == OLD.a)
        def some_function(a: List[int], OLD: int) -> None:  # pylint: disable=unused-variable
            pass

        type_err = None  # type: Optional[TypeError]
        try:
            some_function(a=[13], OLD=2)
        except TypeError as err:
            type_err = err

        self.assertIsNotNone(type_err)
        self.assertEqual("Unexpected argument 'OLD' in a function decorated with postconditions.", str(type_err))

    def test_error_with_invalid_arguments(self):
        @icontract.ensure(
            lambda result: result > 0, error=lambda z, result: ValueError("x is {}, result is {}".format(z, result)))
        def some_func(x: int) -> int:
            return x

        type_error = None  # type: Optional[TypeError]
        try:
            some_func(x=0)
        except TypeError as err:
            type_error = err

        self.assertIsNotNone(type_error)
        self.assertEqual("The argument(s) of the postcondition error have not been set: ['z']. "
                         "Does the original function define them? Did you supply them in the call?",
                         tests.error.wo_mandatory_location(str(type_error)))

    def test_no_boolyness(self):
        @icontract.ensure(lambda: tests.mock.NumpyArray([True, False]))
        def some_func() -> None:
            pass

        value_error = None  # type: Optional[ValueError]
        try:
            some_func()
        except ValueError as err:
            value_error = err

        self.assertIsNotNone(value_error)
        self.assertEqual('Failed to negate the evaluation of the condition.',
                         tests.error.wo_mandatory_location(str(value_error)))
