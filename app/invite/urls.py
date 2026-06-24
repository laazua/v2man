"""邀请码、推广、提现 URL 配置。"""

from django.urls import path

from . import views

urlpatterns = [
    path("invite/codes/", views.ListInviteCodesView.as_view()),
    path("invite/codes/generate/", views.GenerateInviteCodeView.as_view()),
    path("invite/referrals/", views.ListReferralsView.as_view()),
    path("invite/earnings/", views.EarningsView.as_view()),
    path("invite/withdrawals/", views.ListWithdrawalsView.as_view()),
    path(
        "invite/withdrawals/create/",
        views.CreateWithdrawalView.as_view(),
    ),
    path("admin/invite/settings/", views.SettingsView.as_view()),
    path(
        "admin/invite/withdrawals/",
        views.AdminWithdrawalListView.as_view(),
    ),
    path(
        "admin/invite/withdrawals/<int:pk>/action/",
        views.AdminWithdrawalActionView.as_view(),
    ),
]
