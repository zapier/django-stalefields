from django.db import models


class ForeignTestModel(models.Model):
    """
    A simple test model with which to test foreign keys and stale fields mixin
    """
    last_changed = models.DateTimeField(auto_now=True)
    boolean = models.BooleanField(default=True)
    characters = models.CharField(blank=True, max_length=80)

    def __unicode__(self):
        return u'{} {}'.format(self.boolean, self.characters)


class TestModel(models.Model):
    """
    A simple test model with which to test stale fields mixin
    """
    last_changed = models.DateTimeField(auto_now=True)
    integer = models.IntegerField(default=123, db_index=True)
    boolean = models.BooleanField(default=True)
    characters = models.CharField(blank=True, max_length=80)
    text_characters = models.TextField(blank=True, max_length=80)
    foreign_test_model = models.ForeignKey(ForeignTestModel, blank=True, null=True)

    def __unicode__(self):
        return u'{} {} {}'.format(self.boolean, self.characters, self.foreign_test_model)
