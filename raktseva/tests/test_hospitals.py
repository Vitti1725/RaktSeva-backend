import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from hospital.models import Hospital
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_hospital_profile_as_hospital(user_factory, api_client):
    """
    POST /api/hospitals/create/:
    - a verified hospital-role user can create their profile
    """
    user = user_factory(is_verified=True, role='hospital')
    user.save()
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": user.email, "password": "testpass123"},
        format='json'
    )
    token = login.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    payload = {
        "name":               "City Hospital",
        "city":               "Kolkata",
        "address":            "123 Main St",
        "contact_number":     "+911234567890",
        "registration_number":"REG-001"
    }
    resp = api_client.post('/api/hospitals/create/', payload, format='json')
    assert resp.status_code == 201
    data = resp.data
    assert data['name']  == payload['name']
    assert data['city']  == payload['city']

    # verify in db
    h = Hospital.objects.get(user__email=user.email)
    assert h.address == payload['address']


@pytest.mark.django_db
def test_create_hospital_duplicate_fails(api_client, hospital_user):
    """
    POST /api/hospitals/create/:
    - second attempt for same user → 403
    """
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.post('/api/hospitals/create/', {
        "name":               "City Hospital 2",
        "city":               "Pune",
        "address":            "456 Side St",
        "contact_number":     "+919876543210",
        "registration_number":"REG-002"
    }, format='json')
    assert resp.status_code == 403


@pytest.mark.django_db
def test_create_hospital_forbidden_to_donor(api_client, donor_user):
    """
    Donor users may not create hospital profiles → 403
    """
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": donor_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.post('/api/hospitals/create/', {
        "name":               "Bad Hospital",
        "city":               "Nowhere",
        "address":            "N/A",
        "contact_number":     "+910000000000",
        "registration_number":"REG-000"
    }, format='json')
    assert resp.status_code == 403


@pytest.mark.django_db
def test_view_and_update_hospital_profile(api_client, hospital_user):
    """
    GET /api/hospitals/me/ → retrieve own profile
    PATCH /api/hospitals/me/ → update fields
    """
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    # GET
    get_resp = api_client.get('/api/hospitals/me/', format='json')
    assert get_resp.status_code == 200
    assert get_resp.data['city'] == hospital_user.hospital.city

    # PATCH
    patch_resp = api_client.patch(
        '/api/hospitals/me/',
        {"contact_number": "+911112223334"},
        format='json'
    )
    assert patch_resp.status_code == 200
    assert patch_resp.data['contact_number'] == "+911112223334"


@pytest.mark.django_db
def test_view_update_forbidden_to_donor(api_client, donor_user):
    """
    Donor users should not be able to view or update /api/hospitals/me/
    """
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": donor_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    for method in ('get', 'patch'):
        resp = getattr(api_client, method)('/api/hospitals/me/', format='json')
        assert resp.status_code == 403
