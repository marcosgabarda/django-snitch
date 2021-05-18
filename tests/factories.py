from django.contrib.auth import get_user_model
from factory import Faker, post_generation
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):

    username = Faker("email")

    @post_generation
    def password(self, create, extracted, **kwargs):
        password = Faker(
            "password",
            length=42,
            special_chars=True,
            digits=True,
            upper_case=True,
            lower_case=True,
        ).evaluate(None, None, {"locale": "en-us"})
        self.set_password(password)

    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]
