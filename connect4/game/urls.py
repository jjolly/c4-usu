from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    re_path(r'^api/v1/move/(?P<pk>[0-2]{42})$', views.move_from_board)
]
