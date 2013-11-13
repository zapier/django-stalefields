# Adapted from http://stackoverflow.com/questions/110803
# and https://github.com/callowayproject/django-dirtyfields
# and https://github.com/smn/django-dirtyfields

import copy

from django import VERSION

from django.conf import settings
from django.db import router
from django.db.models import signals


def stale_copy(value):
    # no copy for primitives
    if isinstance(value, int) or isinstance(value, bool) or isinstance(value, basestring):
        return value
    # deepcopy for things like JSONField (where the object reference is sticky)
    return copy.deepcopy(value)


class StaleFieldsMixin(object):
    """
    Gives stale field tracking ability to models, also implements a save_stale
    method which updates only the stale fields using QuerySet.update - useful
    for multi-process or multi-worker setups where save() will actually update
    all fields, potentially overriding changes by other workers while the
    current worker has the object open.
    """
    _is_stale_enabled = True
    _original_state = {}

    def _reset_stale_state(self):
        self._original_state = self._as_dict()

    def _as_dict(self):
        # For relations, saves all fk values too so that we can update fk by
        # id, e.g. obj.foreignkey_id = 4
        if self._deferred:
            return {}
        return {f.name: stale_copy(f.to_python(getattr(self, f.attname))) for f in self._meta.fields}

    def get_changed_values(self):
        new_state = self._as_dict()
        return {name: new_state[name] for name, old_value in self._original_state.iteritems() if old_value != new_state[name]}

    @property
    def stale_fields(self):
        """
        Returns a list of keys that have changed
        """
        if self._deferred:
            raise TypeError('Cant be used with deferred objects')
        return tuple(self.get_changed_values().keys())
    dirty_fields = stale_fields

    @property
    def is_stale(self):
        if self._state.adding:
            return True
        return bool(self.stale_fields)
    is_dirty = is_stale

    def save_stale(self, raw=False, using=None, signal_anyways=False):
        """
        An alternative to save, instead writing every field again, only updates
        the stale fields via QuerySet.update
        """
        updated = 0

        if not self.pk:
            self.save(using=using)
            updated = 1
        else:
            # some copied from django/db/models/base.py
            using = using or router.db_for_write(self.__class__, instance=self)

            changed_values = self.get_changed_values()

            if changed_values or signal_anyways:
                signals.pre_save.send(sender=self.__class__, instance=self, raw=raw, using=using)

            # nothing has changed, don't do anything at all
            if changed_values:
                # detect if updating relationship field_ids directly
                # if related field object itself has changed then the field_id
                # also changes, in which case we detect and ignore the field_id
                # change, otherwise we'll reload the object again later unnecessarily
                rel_fields = {f.column: f for f in self._meta.fields if f.rel}
                updated_rel_ids = []
                for field_name in changed_values.keys():
                    if field_name in rel_fields.keys():
                        rel_field = rel_fields[field_name]
                        value = changed_values[rel_field.column]
                        obj_value = getattr(self, rel_field.name).pk
                        del changed_values[rel_field.column]
                        changed_values[rel_field.name] = value
                        if value != obj_value:
                            updated_rel_ids.append(rel_field.column)

                # maps db column names back to field names if they differ
                field_map = {f.column: f.name for f in self._meta.fields if f.db_column}
                for field_from, field_to in field_map.iteritems():
                    if field_from in changed_values:
                        changed_values[field_to] = changed_values[field_from]
                        del changed_values[field_from]

                # apply auto_now values if present
                for field in self._meta.fields:
                    if hasattr(field, 'auto_now') and field.auto_now and field.name not in changed_values:
                        new_value = field.pre_save(self, False)
                        changed_values[field.name] = new_value
                        setattr(self, field.name, new_value)

                updated = self.__class__.objects.filter(pk=self.pk).update(**changed_values)

                # Reload updated relationships
                for field_name in updated_rel_ids:
                    field = rel_fields[field_name]
                    field_pk = getattr(self, field_name)
                    rel_obj = field.related.parent_model.objects.get(pk=field_pk)
                    setattr(self, field.name, rel_obj)

            if changed_values or signal_anyways:
                signals.post_save.send(sender=self.__class__, instance=self, created=False, raw=raw, using=using)

        return updated == 1
    save_dirty = save_stale


def reset_instance(sender, instance, **kwargs):
    """
    Called on the post_save signal.
    """
    if hasattr(instance, '_reset_stale_state'):
        instance._reset_stale_state()
signals.post_save.connect(reset_instance)
signals.post_init.connect(reset_instance)

def get_raw_method(method):
    """
    Allows you to attach other class methods or random
    functions to other classes properly. 
    """
    import types
    if type(method) == types.FunctionType:
        method = staticmethod(method)
    elif type(method) == types.MethodType:
        method = method.__func__
    return method

def auto_add_to_model(sender, **kwargs):
    """
    Applies these to models.
    """
    attrs = ['_original_state', '_reset_stale_state', '_as_dict',
             'get_changed_values', 'stale_fields', 'is_stale',
             'save_stale', 'dirty_fields', 'is_dirty', 'save_dirty',
             '_is_stale_enabled']
    if not (isinstance(sender, StaleFieldsMixin) or getattr(sender, '_is_stale_enabled', False)):
        for attr in attrs:
            method = get_raw_method(getattr(StaleFieldsMixin, attr))
            sender.add_to_class(attr, method)

if getattr(settings, 'AUTO_STALE_FIELDS', False):
    signals.class_prepared.connect(auto_add_to_model)


# Django 1.5 added support for updating only specified fields, this fails in
# older versions.
if VERSION >= (1, 5):
    def save(self, *args, **kwargs):
        if not self._state.adding:
            kwargs['update_fields'] = self.stale_fields
        return super(StaleFieldsMixin, self).save(*args, **kwargs)
    StaleFieldsMixin.save = save
