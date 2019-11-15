from factory import DjangoModelFactory

from tests.app.models import Stuff, Target, Trigger, Actor, OtherStuff


class StuffFactory(DjangoModelFactory):
    class Meta:
        model = Stuff


class ActorFactory(DjangoModelFactory):
    class Meta:
        model = Actor


class TriggerFactory(DjangoModelFactory):
    class Meta:
        model = Trigger


class TargetFactory(DjangoModelFactory):
    class Meta:
        model = Target


class OtherStuffFactory(DjangoModelFactory):
    class Meta:
        model = OtherStuff
