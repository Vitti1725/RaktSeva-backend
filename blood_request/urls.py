from django.urls import path
from .views import (
                   BloodRequestCreateView, BloodRequestListView, AvailableBloodRequestsView, \
                   FulfillBloodRequestView, ExtendBloodRequestView , CancelBloodRequestView, \
                   DonorInterestCreateView, InterestedDonorsView, NearbyDonorsView, \
                   NotifyDonorView
)


urlpatterns = [
    path('create/', BloodRequestCreateView.as_view(), name='blood-request-create'),
    path('my/', BloodRequestListView.as_view(), name='blood-request-list'),
    path('available/', AvailableBloodRequestsView.as_view(), name='available-blood-requests'),
    path('<int:pk>/fulfill/', FulfillBloodRequestView.as_view(), name='blood-request-fulfill'),
    path('<int:pk>/extend/', ExtendBloodRequestView.as_view(), name='blood-request-extend'),
    path('<int:pk>/cancel/', CancelBloodRequestView.as_view(), name='blood-request-cancel'),
    path('<int:pk>/help/', DonorInterestCreateView.as_view(), name='donor-help'),
    path('<int:pk>/interested-donors/', InterestedDonorsView.as_view(), name='interested-donors'),
    path('nearby-donors/', NearbyDonorsView.as_view(), name='nearby-donors'),
    path('notify-donors/', NotifyDonorView.as_view(), name='notify-donors'),

]
