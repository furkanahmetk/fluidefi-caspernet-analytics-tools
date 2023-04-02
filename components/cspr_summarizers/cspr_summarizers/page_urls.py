from django.urls import path, include

urlpatterns = [
    path('', views.index, name='index'),
    path('index2', views.index2, name='index2'),
]