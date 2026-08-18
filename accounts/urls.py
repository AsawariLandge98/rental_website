from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('internal-login/', views.admin_login, name='admin_login'),

    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('forgot-password/done/', views.ForgotPasswordDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.ForgotPasswordConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.ForgotPasswordCompleteView.as_view(), name='password_reset_complete'),
]
