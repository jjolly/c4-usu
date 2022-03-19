from django.urls import path, re_path
from . import views

app_name = "game"
urlpatterns = [
    path('', views.index, name='index'),
    path('one-player/', views.onePlayer, name='one-player'),
    path('two-player/', views.twoPlayer, name='two-player'),
    re_path(r'^api/v1/move/(?P<pk>[0-2]{42})$', views.move_from_board)
]
