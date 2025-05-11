from django.urls import path
from .views import DonorCreateView, DonorProfileView, DonorDetailView, DonorListView, MyDonorInterestsView
urlpatterns = [
    path('create/', DonorCreateView.as_view(), name='donor-create'),
    path('me/', DonorProfileView.as_view(), name='donor-me'),
    path('', DonorListView.as_view(), name='donor-list'),
    path('<int:id>/', DonorDetailView.as_view(), name='donor-detail'),
    path('interests/my/', MyDonorInterestsView.as_view(), name='my-donor-interests'),

]
