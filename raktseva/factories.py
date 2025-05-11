import factory
from django.contrib.auth import get_user_model
from blood_request.models import BloodRequest
from donor.models import Donor
from hospital.models import Hospital

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    name = factory.Faker('user_name')
    email = factory.Faker('email')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    role = 'donor'
    is_verified = True


class DonorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Donor

    user = factory.SubFactory(UserFactory, role='donor')
    blood_group = factory.Faker('random_element', elements=['A+', 'B+', 'O+', 'AB+'])
    city = factory.Faker('city')
    is_available = True


class HospitalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Hospital
        skip_postgeneration_save = True

    user = factory.SubFactory(UserFactory, role='hospital')
    name = factory.Faker('company')
    city = factory.Faker('city')
    address = factory.Faker('address')
    contact_number = factory.Faker('bothify', text='+91##########')
    registration_number = factory.Faker('bothify', text='HOSP-###')
    latitude = factory.Faker('latitude')
    longitude = factory.Faker('longitude')


class BloodRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BloodRequest

    hospital = factory.SubFactory(HospitalFactory)
    blood_group = factory.Faker('random_element', elements=['A+', 'B+', 'O+', 'AB+'])
    city = factory.Faker('city')
    quantity = factory.Faker('pyint', min_value=1, max_value=5)
    is_fulfilled = False
