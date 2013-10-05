from django.test import TestCase

from example_app.testing_app.models import TestModel, ForeignTestModel


class StaleFieldsMixinTestCase(TestCase):

    def test_stale_fields(self):
        tm = TestModel()
        # initial state shouldn't be stale
        self.assertEqual(tm.stale_fields, tuple())

        # changing values should flag them as stale
        tm.boolean = False
        tm.characters = 'testing'
        self.assertEqual(set(tm.stale_fields), set(('boolean', 'characters')))

        # resetting them to original values should unflag
        tm.boolean = True
        self.assertEqual(tm.stale_fields, ('characters', ))

    def test_sweeping(self):
        tm = TestModel()
        tm.boolean = False
        tm.characters = 'testing'
        self.assertEqual(set(tm.stale_fields), set(('boolean', 'characters')))
        tm.save()
        self.assertEqual(tm.stale_fields, tuple())

    def test_foreignkeys(self):
        ftm1 = ForeignTestModel.objects.create(characters="foreign1")
        ftm2 = ForeignTestModel.objects.create(characters="foreign2")

        tm = TestModel()
        tm.boolean = False
        tm.characters = 'testing'
        tm.foreign_test_model = ftm1
        self.assertEqual(set(tm.stale_fields), set(('boolean', 'characters', 'foreign_test_model')))
        tm.save()

        self.assertEqual(tm.stale_fields, tuple())
        tm.foreign_test_model = ftm2
        self.assertEqual(tm.stale_fields, ('foreign_test_model', ))
        tm.foreign_test_model.characters = "foreign2.0"
        self.assertEqual(tm.foreign_test_model.stale_fields, ('characters', ))

    def test_stale_save(self):
        ftm1 = ForeignTestModel.objects.create(characters="foreign1")
        ftm2 = ForeignTestModel.objects.create(characters="foreign2")

        tm = TestModel.objects.create(
            boolean = False,
            characters='testing',
            foreign_test_model=ftm1,
        )
        tm.characters = 'another test'
        tm.foreign_test_model = ftm2
        tm.save_stale()

        tm = TestModel.objects.get(id=tm.id)
        self.assertEqual(tm.characters, 'another test')
        self.assertEqual(tm.foreign_test_model, ftm2)

    def test_stale_save_fk_id(self):
        ftm1 = ForeignTestModel.objects.create(characters="foreign1")
        ftm2 = ForeignTestModel.objects.create(characters="foreign2")

        tm = TestModel.objects.create(
            boolean = False,
            characters='testing',
            foreign_test_model=ftm1,
        )
        tm.foreign_test_model_id = ftm2.id
        tm.save_stale()

        tm = TestModel.objects.get(id=tm.id)
        self.assertEqual(tm.foreign_test_model, ftm2)
