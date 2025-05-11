import os
import django

# Set up Django settings for pytest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'raktseva.settings')
django.setup()

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from raktseva.factories import UserFactory, DonorFactory, HospitalFactory, BloodRequestFactory

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_factory(db):
    """Factory for creating User objects with overrideable kwargs."""
    return UserFactory


@pytest.fixture
def donor_factory(db):
    """Factory for creating Donor profiles (requires a User)."""
    return DonorFactory


@pytest.fixture
def hospital_factory(db):
    """Factory for creating Hospital profiles (requires a User)."""
    return HospitalFactory

@pytest.fixture
def blood_request_factory(db):
    """Factory for creating blood request."""
    return BloodRequestFactory



@pytest.fixture
def unverified_user(user_factory):
    """A user who has NOT yet verified their OTP."""
    return user_factory(is_verified=False)


@pytest.fixture
def verified_user(user_factory):
    """A user who is already OTP‑verified."""
    user = user_factory(is_verified=True)
    user.save()
    return user



@pytest.fixture
def donor_user(user_factory, donor_factory):
    """
    A full donor flow: a verified User with role='donor'
    and an associated Donor profile.
    """
    user = user_factory(is_verified=True, role='donor')
    user.save()
    donor_factory(user=user)
    return user


@pytest.fixture
def hospital_user(user_factory, hospital_factory):
    """
    A full hospital flow: a verified User with role='hospital'
    and an associated Hospital profile.
    """
    user = user_factory(is_verified=True, role='hospital')
    user.save()
    hospital_factory(user=user)
    return user


@pytest.fixture
def admin_user(db):
    """
    A superuser/admin account for hitting admin‑only endpoints.
    """
    return User.objects.create_superuser(
        email='admin@example.com',
        password='adminpass123',
    )

