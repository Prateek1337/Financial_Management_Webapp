from django.contrib import admin
from django.urls import path,include
from app2 import views
app_name='app2'


urlpatterns = [
    path('home',views.home,name='home'),
    path('all_trans',views.all_trans,name='all_trans'),
    path('history',views.history,name='history'),
    path('settle_trans',views.settle_trans,name='settle_trans'),

]