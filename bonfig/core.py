import itertools
import sys
import collections

from bonfig.fields import Field, Store, Section


class BonfigType(type):
    """
    Metaclass for Bonfig base class.

    Facilitates the loading of Fields into class attributes, which is in turn used by the Bonfig `__init__` to
    initialise `Field` values.

    Additionally back-ports `__set_name__` behaviour from 3.6 that's extensively used.
    """

    def __new__(cls,  name, bases, attrs, **kwargs):
        """Creates Bonfig class object

        """
        attrs['__fields__'] = collections.defaultdict(list)
        return super().__new__(cls, name, bases, attrs, **kwargs)

    def __init__(cls, name, bases, attrs, **kwargs):
        """Initialises Bonfig class object.

        """
        if sys.version_info[1] < 6:  # Backport of __set_name__ from 3.6 :)
            for k, v in attrs.items():
                if isinstance(v, (Field, Store, Section)):
                    v.__set_name__(cls, k)

        fields = collections.defaultdict(list)

        # Allow for inheritance
        for attr in itertools.chain(*(base.__dict__.values() for base in bases)):
            if isinstance(attr, Field):
                fields[attr.store_attr].append(attr)

        # Overwrites any base class values.
        for attr in attrs.values():
            if isinstance(attr, Field):
                fields[attr.store_attr].append(attr)

        attrs['__fields__'].update(fields)
        super().__init__(name, bases, attrs)


class Bonfig(metaclass=BonfigType):
    """
    Base class for all Bonfigs.

    Arguments
    ----------
    locked : bool, optional
        Lock `Bonfig` instance immediately after initialisation (default - False)
    *args
        Positional arguments, passed to `load` (see load)
    **kwargs
        Keyword arguments, passed to `load` (see load)

    Notes
    -----
    Instances of this class shouldn't be created directly, instead it should be subclassed (see examples).

    Ideally do not call `__init__` directly, instead use the provided load hook for initialising things like data stores.

    Attributes
    ----------
    __fields__ : defaultdict
        a `defaultdict` containing all the classes `Field` attributes, grouped by `store_attr`

    Examples
    --------
    # Todo
    """

    def __init__(self, locked=False, *args, **kwargs):
        self._locked = False

        self.load(*args, **kwargs)

        for store_attr, field_list in self.__fields__.items():

            for field in field_list:
                field.initialise(self)

        self.finalise()

        self._locked = locked

    def load(self, *args, **kwargs):
        """
        Hook called during initialisation for loading store attributes.

        Is basically `__init__`, but called at the right time such that locking works and that fields can be
        initialised.

        Note
        ----
        As `load` is called before `Field`s are initialised, values can be overwritten by fields unless
        `Field.val=None`.

        Arguments
        ---------
        *args
            args from `__init__`
        **kwargs
            kwargs from `__init__`
        """
        pass

    def finalise(self):
        """
        Hook called during initialisation after fields have been initialised.

        This could be useful for maybe replacing your store with a read-only version of itself (see examples)

        Default behaviour is to do absolutely nothing!

        Examples
        --------
        # Todo
        """
        pass

    @property
    def locked(self):
        """
        Check if `Bonfig` instance is locked
        """
        return self._locked

    def lock(self):
        """
        Lock `Bonfig` instance. This prevents any values being set on `Field` s.

        .. warning:: Whilst this prevents setting `Field` values through attributes, values can still be changed in the \
        underlying store data.

        See Also
        --------
        unlock : unlock the `Bonfig` instance
        """
        self._locked = True

    def unlock(self):
        """
        Unlock `Bonfig` instance. This allows setting values of `Field` s.

        See Also
        --------
        lock : lock the `Bonfig` instance
        """
        self._locked = False

    def __enter__(self):
        """Unlock `Bonfig` instance within `with` block. `Bonfig` with re-lock upon `__exit__`.

        """
        self.unlock()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lock()
