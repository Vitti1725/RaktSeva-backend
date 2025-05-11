import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from donor.models import Donor, DonorInterest

User = get_user_model()

@pytest.mark.django_db
def test_create_donor_profile_success(api_client, user_factory):
    """
    POST /api/donors/create/:
    - a verified donor‐role user can create their Donor profile
    """

    user = user_factory(is_verified=True, role='donor')
    user.save()
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": user.email, "password": "testpass123"},
        format='json'
    )
    token = login.data['access']
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    payload = {
        "blood_group":   "O+",
        "city":          "Bengaluru",
        "contact_number":"+919900112233",
        "is_available":  True
    }
    resp = api_client.post('/api/donors/create/', payload, format='json')
    assert resp.status_code == 201
    assert resp.data['blood_group'] == payload['blood_group']
    assert resp.data['city']  == payload['city']
    assert resp.data['is_available'] is True

    # verify in db
    d = Donor.objects.get(user__email=user.email)
    assert d.contact_number == payload['contact_number']

@pytest.mark.django_db
def test_create_donor_profile_duplicate_fails(api_client, donor_user):
    """
    POST /api/donors/create/:
    - second attempt to create profile for same user → 403
    """
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": donor_user.email, "password": "testpass123"},
        format='json'
    )
    print(login.data)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.post('/api/donors/create/', {
        "blood_group": "A+",
        "city": "Test",
        "contact_number": "+911234567890",
        "is_available": True
    }, format='json')
    assert resp.status_code == 403

@pytest.mark.django_db
def test_view_and_update_own_profile(api_client, donor_user):
    """
    GET  /api/donors/me/ → see own profile
    PATCH /api/donors/me/ → update fields
    """
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": donor_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    # GET
    get_resp = api_client.get('/api/donors/me/')
    assert get_resp.status_code == 200
    assert get_resp.data['blood_group'] == donor_user.donor.blood_group

    # PATCH
    patch_resp = api_client.patch(
        '/api/donors/me/',
        {"is_available": False},
        format='json'
    )
    assert patch_resp.status_code == 200
    assert patch_resp.data['is_available'] is False

@pytest.mark.django_db
def test_view_update_profile_forbidden_to_hospitals(api_client, hospital_user):
    """
    Hospital users should not be able to GET/PATCH /api/donors/me/
    """
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    for method in ('get', 'patch'):
        resp = getattr(api_client, method)('/api/donors/me/', format='json')
        assert resp.status_code == 403

@pytest.mark.django_db
def test_list_and_filter_donors(api_client, hospital_user, donor_factory):
    """
    GET /api/donors/?blood_group=&city=&is_available=
    - returns paginated list for hospital users
    - filters work correctly
    """
    # create mixed donors
    donor_factory(blood_group='A+', city='Delhi',   is_available=True)
    donor_factory(blood_group='A+', city='Mumbai',  is_available=True)
    donor_factory(blood_group='B+', city='Mumbai',  is_available=False)
    donor_factory(blood_group='A+', city='Mumbai', is_available=True)

    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    # unfiltered
    list_resp = api_client.get('/api/donors/', format='json')
    assert list_resp.status_code == 200
    assert 'results' in list_resp.data
    assert len(list_resp.data['results']) == 4

    # filtered: only A+ in Mumbai & available
    filter_resp = api_client.get(
        '/api/donors/',
        {'blood_group': 'A+', 'city': 'Mumbai', 'is_available': True},
        format='json'
    )
    print(filter_resp.data)
    assert filter_resp.status_code == 200
    results = filter_resp.data['results']

    assert all(d['blood_group']=='A+' for d in results)
    assert all(d['city']=='Mumbai' for d in results)
    assert all(d['is_available'] for d in results)

@pytest.mark.django_db
def test_list_and_filter_forbidden_to_donors(api_client, donor_user):
    """
    Regular donors should get 403 on listing other donors.
    """
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": donor_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.get('/api/donors/', format='json')
    assert resp.status_code == 403

@pytest.mark.django_db
def test_get_specific_donor(api_client, hospital_user, donor_factory):
    """
    GET /api/donors/{id}/ → hospital users can fetch any donor
    """
    donor = donor_factory()
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.get(f'/api/donors/{donor.id}/', format='json')
    print(resp.data)
    assert resp.status_code == 200
    assert resp.data['id'] == donor.id

@pytest.mark.django_db
def test_get_specific_forbidden_to_non_hospital(api_client, donor_user, donor_factory):
    """
    GET /api/donors/{id}/ → only hospital/admin can view other donor
    """
    donor = donor_factory()
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": donor_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.get(f'/api/donors/{donor.id}/', format='json')
    assert resp.status_code in (403, 404)

@pytest.mark.django_db
def test_list_my_donor_interests(api_client, donor_user, blood_request_factory):
    """
    GET /api/donors/interests/my/:
    - returns the list of BloodRequests this donor has expressed interest in
    """

    br1 = blood_request_factory()
    br2 = blood_request_factory()

    DonorInterest.objects.create(blood_request=br1, donor=donor_user.donor)
    DonorInterest.objects.create(blood_request=br2, donor=donor_user.donor)

    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": donor_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.get('/api/donors/interests/my/', format='json')
    assert resp.status_code == 200

    returned_ids = {r['id'] for r in resp.data['results']}
    assert br1.id in returned_ids
    assert br2.id in returned_ids
    assert len(returned_ids) == 2




