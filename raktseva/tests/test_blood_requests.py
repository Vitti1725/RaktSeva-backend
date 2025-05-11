import pytest
from django.urls import reverse
from blood_request.models import BloodRequest
from donor.models import DonorInterest
from django.contrib.auth import get_user_model

from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@pytest.mark.django_db
def test_create_blood_request_as_hospital(api_client, hospital_user):
    """
    POST /api/blood-requests/create/:
    - hospital users can create a blood request
    """
    # log in as hospital
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    payload = {
        "blood_group": "B+",
        "city":  "Chennai",
        "quantity":    2
    }
    resp = api_client.post('/api/blood-requests/create/', payload, format='json')
    assert resp.status_code == 201
    data = resp.data
    assert data['blood_group'] == payload['blood_group']
    assert data['quantity']    == payload['quantity']

    # verify in DB
    br = BloodRequest.objects.get(id=data['id'])
    assert br.hospital == hospital_user.hospital


@pytest.mark.django_db
def test_list_my_requests(api_client, user_factory, hospital_user, blood_request_factory, hospital_factory):
    """
    GET /api/blood-requests/my/:
    - returns only the logged-in hospital’s requests
    """
    # create 2 for this hospital and 1 for another
    blood_request_factory(hospital=hospital_user.hospital)
    blood_request_factory(hospital=hospital_user.hospital)

    other_hosp_user = user_factory(role='hospital', is_verified=True)
    hospital_factory(user=other_hosp_user)
    blood_request_factory(hospital=other_hosp_user.hospital)

    # login & list
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    resp = api_client.get('/api/blood-requests/my/', format='json')
    assert resp.status_code == 200
    results = resp.data['results']
    assert len(results) == 2
    assert all(r['hospital']['id'] == hospital_user.hospital.id for r in results)


@pytest.mark.django_db
def test_available_requests_for_donors(api_client, blood_request_factory, donor_user, monkeypatch):
    """
    GET /api/blood-requests/available/:
    - shows only non‐expired, unfulfilled requests to donors
    """
    now = timezone.now()

    # make some requests
    r1 = blood_request_factory(
        blood_group = donor_user.donor.blood_group,
        city = donor_user.donor.city,
    )
    r1.created_at = now - timedelta(hours=1)
    r1.save()

    r2 = blood_request_factory(is_fulfilled=True)
    # expired: set created_at older than 48h
    expired = blood_request_factory()
    expired.created_at = now - timedelta(hours=49)
    expired.save()

    # login as donor
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": donor_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.get('/api/blood-requests/available/', format='json')
    assert resp.status_code == 200
    print(resp.data)
    ids = {r['id'] for r in resp.data['results']}
    assert r1.id in ids
    assert r2.id not in ids
    assert expired.id not in ids


@pytest.mark.django_db
def test_fulfill_request(api_client, hospital_user, blood_request_factory):
    """
    PATCH /api/blood-requests/{id}/fulfill/:
    - hospital can mark their own request fulfilled
    """
    br = blood_request_factory(hospital=hospital_user.hospital)
    # login
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.patch(f'/api/blood-requests/{br.id}/fulfill/', format='json')
    assert resp.status_code == 200
    br.refresh_from_db()
    assert br.is_fulfilled is True


@pytest.mark.django_db
def test_extend_request(api_client, hospital_user, blood_request_factory):
    """
    PATCH /api/blood-requests/{id}/extend/:
    - hospital can extend expiry by +48h
    """
    br = blood_request_factory(hospital=hospital_user.hospital)
    original_expiry = br.created_at
    # login
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.patch(f'/api/blood-requests/{br.id}/extend/', format='json')
    assert resp.status_code == 200
    br.refresh_from_db()
    # expiry moved forward relative to created_at
    assert br.created_at > original_expiry


@pytest.mark.django_db
def test_cancel_request(api_client, hospital_user, blood_request_factory):
    """
    DELETE /api/blood-requests/{id}/cancel/:
    - hospital can cancel their request
    """
    br = blood_request_factory(hospital=hospital_user.hospital)
    # login
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.delete(f'/api/blood-requests/{br.id}/cancel/')
    assert resp.status_code == 200
    assert not BloodRequest.objects.filter(id=br.id).exists()

@pytest.mark.django_db
def test_donor_help_creates_interest(api_client, donor_user, blood_request_factory):
    """
    POST /api/blood-requests/{pk}/help/:
    - authenticated donor can express interest (offer help)
    """

    br = blood_request_factory()

    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": donor_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.post(f'/api/blood-requests/{br.id}/help/', format='json')
    assert resp.status_code == 201

    # verify DonorInterest row in db
    di = DonorInterest.objects.get(blood_request=br, donor=donor_user.donor)
    assert di.donor == donor_user.donor
    assert di.blood_request == br

@pytest.mark.django_db
def test_interested_donors_list(api_client, hospital_user, donor_factory, blood_request_factory):
    """
    GET /api/blood-requests/{pk}/interested-donors/:
    - hospital user fetches list of donors who offered help
    """
    br = blood_request_factory(hospital=hospital_user.hospital)

    d1 = donor_factory()
    d2 = donor_factory()
    DonorInterest.objects.create(blood_request=br, donor=d1)
    DonorInterest.objects.create(blood_request=br, donor=d2)

    # login as that hospital
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.get(f'/api/blood-requests/{br.id}/interested-donors/', format='json')
    assert resp.status_code == 200

    ids = {d['id'] for d in resp.data['results']}
    assert d1.id in ids and d2.id in ids

@pytest.mark.django_db
def test_nearby_donors(api_client, hospital_user, donor_factory):
    """
    GET /api/blood-requests/nearby-donors/:
    - hospital user sees only donors within 20km & matching blood_group & city
    """
    # give hospital lat/lon
    hospital = hospital_user.hospital
    hospital.latitude = 12.9716
    hospital.longitude = 77.5946
    hospital.save()

    # donor A: within radius, matching group & city
    d1 = donor_factory(
        blood_group=hospital_user.hospital.blood_requests.first().blood_group
        if hospital_user.hospital.blood_requests.exists()
        else 'A+',
        city=hospital.city,
        latitude=12.9717,
        longitude=77.5947
    )

    # donor B: too far away
    d2 = donor_factory(
        blood_group=d1.blood_group,
        city=hospital.city,
        latitude=13.5,
        longitude=77.6
    )

    # login as hospital
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.get('/api/blood-requests/nearby-donors/', format='json')
    assert resp.status_code == 200

    ids = {d['id'] for d in resp.data['results']}
    assert d1.id in ids
    assert d2.id not in ids

@pytest.mark.django_db
def test_notify_donors_endpoint(api_client, hospital_user, donor_factory, monkeypatch):
    """
    POST /api/blood-requests/notify-donors/:
    - hospital can send a message to a list of donor IDs
    """

    d1 = donor_factory()
    d2 = donor_factory()

    sent = []
    monkeypatch.setattr('blood_request.views.send_mail', lambda *args, **kwargs: sent.append(args))

    # login as hospital
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    payload = {
        "donor_ids": [d1.id, d2.id],
        "message":   "Urgent: need help!"
    }
    resp = api_client.post('/api/blood-requests/notify-donors/', payload, format='json')
    print(sent)
    assert resp.status_code == 200
    assert len(sent) == 2

@pytest.mark.django_db
def test_create_blood_request_missing_fields(api_client, hospital_user):
    """POST /create/ with missing required fields should return 400."""
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.post('/api/blood-requests/create/', {"blood_group":"A+"}, format='json')
    assert resp.status_code == 400
    assert 'quantity' in resp.data

@pytest.mark.django_db
def test_list_my_requests_empty(api_client, hospital_user):
    """GET /my/ when no requests exist returns empty list."""
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.get('/api/blood-requests/my/', format='json')
    assert resp.status_code == 200
    assert resp.data['results'] == []

@pytest.mark.django_db
def test_extend_request_not_owned(api_client, hospital_user, blood_request_factory):
    """Hospitals can’t extend another hospital’s request (403 or 404)."""
    other = blood_request_factory()
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.patch(f'/api/blood-requests/{other.id}/extend/', format='json')
    assert resp.status_code in (403, 404)

@pytest.mark.django_db
def test_cancel_request_not_owned(api_client, hospital_user, blood_request_factory):
    """Hospitals can’t cancel another hospital’s request (403 or 404)."""
    other = blood_request_factory()
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": hospital_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    resp = api_client.delete(f'/api/blood-requests/{other.id}/cancel/')
    assert resp.status_code in (403, 404)

@pytest.mark.django_db
def test_duplicate_interest_help(api_client, donor_user, blood_request_factory):
    """Posting /help/ twice returns 400 (duplicate interest)."""
    br = blood_request_factory()
    login = api_client.post(
        reverse('token_obtain_pair'),
        {"email": donor_user.email, "password": "testpass123"},
        format='json'
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    first = api_client.post(f'/api/blood-requests/{br.id}/help/', format='json')
    assert first.status_code == 201

    second = api_client.post(f'/api/blood-requests/{br.id}/help/', format='json')
    assert second.status_code == 400

