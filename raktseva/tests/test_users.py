import pytest
from users.models import OTP
from users.utils  import generate_otp
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_user_registration(api_client):
    """POST /api/users/register/ returns email and id."""
    payload = {
        "email":    "new@example.com",
        "name":     "New User",
        "password": "testpass123",
        "role":     "donor"
    }
    resp = api_client.post('/api/users/register/', payload, format='json')
    assert resp.status_code == 201
    assert resp.data['email'] == payload['email']
    assert 'id' in resp.data

@pytest.mark.django_db
def test_generate_and_verify_otp(monkeypatch, api_client, unverified_user):
    """OTP generation writes to DB and verify endpoint succeeds."""
    monkeypatch.setattr('users.utils.random.randint', lambda a, b: 424242)
    monkeypatch.setattr('users.utils.send_mail', lambda *args, **kw: 1)

    generate_otp(unverified_user.email)
    otp = OTP.objects.get(email=unverified_user.email)
    assert otp.code == '424242'

    resp = api_client.post('/api/users/verify/', {
        "email": unverified_user.email,
        "code":  "424242"
    }, format='json')
    assert resp.status_code == 200
    assert 'verified' in resp.data['message'].lower()

@pytest.mark.django_db
def test_login_and_refresh_token(api_client, verified_user):
    """Obtain JWT tokens and refresh them."""
    print(verified_user.is_verified)
    login = api_client.post('/api/token/', {
        "email":    verified_user.email,
        "password": "testpass123"
    }, format='json')
    assert login.status_code == 200
    assert 'access'  in login.data
    assert 'refresh' in login.data

    refresh = api_client.post('/api/token/refresh/', {
        "refresh": login.data['refresh']
    }, format='json')
    assert refresh.status_code == 200
    assert 'access' in refresh.data

@pytest.mark.django_db
def test_resend_otp(monkeypatch, api_client, unverified_user):
    """POST /api/users/resend-otp/ triggers OTP resend."""
    monkeypatch.setattr('users.utils.generate_otp', lambda email: None)
    resp = api_client.post('/api/users/resend-otp/', {
        "email": unverified_user.email
    }, format='json')
    assert resp.status_code == 200
    assert 'otp' in resp.data['message'].lower()

@pytest.mark.django_db
def test_current_logged_in_user(api_client, verified_user):
    """GET /api/users/me/ returns the logged‑in user (Bearer token only)."""

    login = api_client.post('/api/token/', {
        "email":    verified_user.email,
        "password": "testpass123"
    }, format='json')
    token = login.data['access']

    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    resp = api_client.get('/api/users/me/')
    assert resp.status_code == 200
    assert resp.data['email'] == verified_user.email
    assert resp.data['is_verified'] is True

@pytest.mark.django_db
def test_list_all_users_admin_only(api_client, admin_user, donor_user):
    """
    Admin can GET /api/users/all/ (paginated),
    donor (non‑admin) gets 403.
    """
    # admin succeeds
    api_client.force_authenticate(admin_user)
    resp = api_client.get('/api/users/all/')
    assert resp.status_code == 200
    assert 'results' in resp.data
    assert any(u['email'] == admin_user.email for u in resp.data['results'])

    # non‑admin forbidden
    api_client.force_authenticate(donor_user)
    resp = api_client.get('/api/users/all/')
    assert resp.status_code == 403
