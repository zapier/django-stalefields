Django Stale Fields
===================

Tracking changed fields on a Django model instance.

Makes a Mixin available that will give you the properties:

- `is_stale`
- `stale_fields`

As well as the methods:

- `save_stale()`

Which will will selectively only update stale columns using the familiar
`Model.objects.filter(pk=pk).update(**stale_fields)` pattern (but still
resolves `F()` or `auto_now` constructs).


## Installing

Install the package using [pip][]. Then use the instructions in "Using
the Mixin in the Model".

```
$ pip install django-stalefields
```

or if you're interested in developing it, use [virtualenv][] and
[virtualenvwrapper][]. The default `settings.py` will look for the
stalefields package in its current location.

```
$ mkvirtualenv django-stalefields
(django-stalefields)$ pip install -r example_app/requirements.pip
(django-stalefields)$ example_app/manage.py test testing_app
```


## Auto-Mixin For All Models

You need to set make two `settings.py` tweaks:

```python
# settings.py


INSTALLED_APPS = (
    'stalefields', # must be first!

    # the rest...
)

AUTO_STALE_FIELDS = True
```

This provides the methods and functionality *automatically* for all
registered models.


## Manual Mixin in the Model

```python
from django.db import models
from stalefields import StaleFieldsMixin

class TestModel(StaleFieldsMixin, models.Model):
    """A simple test model to test stale fields mixin with"""
    boolean = models.BooleanField(default=True)
    characters = models.CharField(blank=True, max_length=80)
```


## Using it in the shell

```python
(django-stalefields)$ ./manage.py shell
>>> from testing_app.models import TestModel
>>> tm = TestModel(boolean=True, characters="testing")
>>> tm.save()
>>> tm.is_stale
False
>>> tm.stale_fields
()
>>> tm.boolean = False
>>> tm.is_stale
True
>>> tm.stale_fields
('boolean', )
>>> tm.characters = "have changed"
>>> tm.is_stale
True
>>> tm.stale_fields
('boolean', 'characters', )
>>> tm.save_dirty() # just saves the dirty fields via .update()
>>> tm.is_stale
False
>>> tm.get_stale_fields
()
```


## Why would you want this?

Three reasons:

* Convenience
* Optimization
* Bug avoidance

When using [signals][], especially [pressave][], it is useful to be able
to see what fields have changed or not. A signal could change its
behaviour depending on whether a specific field has changed, whereas
otherwise, you only could work on the event that the model's save()
method had been called.

Any time you call boring old `save()` inside Django, all columns are inserted
once again, which can be very heavy if, for example, you have lots of text in one
column or many indexes that don't need to be needlessly checked for updating. Only
updating changing columns via `update()` is much faster, but requires lots of state
monitoring of your own accord. Put simply, this is nicer you your database!

Finally, if multiple threads call `save()` for different operations, only the more
recent thread wins. If they both INSERTED only their column's changing values, that wouldn't
be an issue! These kinds of bugs are a nightmare to chase down...


## Credits

This code has largely be adapted from what was made available at [Stack Overflow][] and adapted from Forked from https://github.com/smn/django-dirtyfields and https://github.com/callowayproject/django-dirtyfields..


  [pip]: http://www.pip-installer.org/en/latest/
  [virtualenv]: https://pypi.python.org/pypi/virtualenv
  [virtualenvwrapper]: https://pypi.python.org/pypi/virtualenvwrapper
  [signals]: http://docs.djangoproject.com/en/1.2/topics/signals/
  [pressave]: http://docs.djangoproject.com/en/1.2/ref/signals/#django.db.models.signals.pre_save
  [Stack Overflow]: http://stackoverflow.com/questions/110803/stale-fields-in-django
