from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_page, name='login'),
    path('collections/', views.collections, name='collections'),
    path('collections/<str:name>/', views.collectionview, name='collectionview'),
    path('collections/<str:cname>/<str:pname>/', views.product_details, name='product_details'),
    path('logout/', views.logout_page, name='logout'),
    path('addtocart/', views.add_to_cart, name='addtocart'),
    path('cart/', views.cart_page, name='cart'),
    path('remove_cart/<int:cid>/', views.remove_cart, name='remove_cart'),
    path('fav/', views.fav_page, name='fav'),
    path('favViewPage/', views.favViewPage, name='favViewPage'),
    path('remove_fav/<int:fid>/', views.remove_fav, name='remove_fav'),


]
