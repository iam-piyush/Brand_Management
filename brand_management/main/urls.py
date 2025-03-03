from django.urls import path
from . import views

urlpatterns = [
    # Brand-related URLs
    path("brands/", views.brands, name="brands"),
    path("get_brands/", views.get_brands, name="get_brands"),
    path("create_brand/", views.create_brand, name="create_brand"),
    path("brand/<str:brand_id>/", views.brand_detail, name="brand_detail"),

    # Campaign-related URLs
    path("campaigns/", views.campaigns, name="campaigns"),
    path("create_campaign/<str:brand_id>/", views.create_campaign, name="create_campaign"),
    path("get_campaigns/", views.get_campaigns, name="get_campaigns"),

    # Newsletter-related URLs
    path('newsletters/', views.newsletter_list, name='newsletter_list'),
    path('api/create-newsletter/', views.create_newsletter, name='create_newsletter'),
    path('newsletter/<str:newsletter_id>/', views.newsletter_detail, name='newsletter_detail'),
    path('api/generate-subscriber-pdfs/', views.generate_subscriber_pdfs, name='generate-subscriber-pdfs'),

    # Subscription URLs
    path("subscribe/", views.subscribe, name="subscribe"),
    path("subscription-success/", views.subscription_success, name="subscription_success"),

    # Subscriber-related URLs
    path("subscribers/", views.get_subscribers, name="subscribers"),
    path("update_subscriber_group/", views.update_subscriber_group, name="update_subscriber_group"),

    # Coupons-related URLs
    path("coupons/", views.coupons, name="coupons"),
    path('create_coupon/<str:campaign_id>/', views.create_coupon, name='create_coupon'),
    path("get_coupons/<str:newsletter_id>/", views.get_coupons, name="get_coupons"),
    path("coupon/<str:coupon_id>/", views.coupon_detail, name="coupon_detail"),

    # PDF Related
    path('api/process-template/', views.process_template, name='process-template'),
    path('api/generate-preview/', views.generate_preview, name='generate-preview'),

    #Coupon Reedem
    path('redeem/<str:tracking_id>/', views.redeem_coupon, name='redeem_coupon'),
    path("validate-coupon/<str:brand_id>/", views.validate_coupon, name="validate_coupon"),

    #brand login
    path('brand_login/', views.brand_login, name='brand_login'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('brand/dashboard/<str:brand_id>/', views.brand_dashboard, name='brand_dashboard'),
    path('brand/analytics/<str:brand_id>/', views.brand_analytics, name='brand_analytics'),
]
