from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Pages
    path('', views.index, name='index'),
    path('profile/', views.profile, name='profile'),
    path('lottery/', views.lottery, name='lottery'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),

    # API Endpoints
    path('api/auth/', views.auth_user, name='auth_user'),
    path('api/deposit/', views.deposit_ton, name='deposit_ton'),
    path('api/roulettes/', views.get_roulettes, name='get_roulettes'),
    path('api/spin/', views.spin_roulette, name='spin_roulette'),
    path('api/inventory/', views.get_inventory, name='get_inventory'),
    path('api/sell/', views.sell_item, name='sell_item'),
    path('api/withdraw/', views.withdraw_item, name='withdraw_item'),
    path('api/lotteries/', views.get_lotteries, name='get_lotteries'),
    path('api/lotteries/buy/', views.buy_lottery_ticket, name='buy_lottery_ticket'),
    path('api/leaderboard/', views.get_leaderboard, name='get_leaderboard'),

    # Admin API
    path('api/admin/withdrawals/', views.get_admin_withdrawals, name='get_admin_withdrawals'),
    path('api/admin/fulfill/', views.fulfill_withdrawal, name='fulfill_withdrawal'),
    path('api/admin/settings/', views.admin_manage_entity, kwargs={'entity_type': 'settings'}, name='admin_settings'),
    path('api/admin/users/', views.admin_manage_users, name='admin_users'),
    path('api/admin/gifts/', views.admin_manage_gifts, name='admin_gifts'),
    path('api/admin/roulettes/', views.admin_manage_roulettes, name='admin_roulettes'),
    path('api/admin/lotteries/', views.admin_manage_lotteries, name='admin_lotteries'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
