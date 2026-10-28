from django.urls import path

from . import views

app_name = 'manutencoes'

urlpatterns = [
    path('', views.manutencao_list, name='manutencao_list'),
    path('manutencoes/', views.manutencao_list, name='index'),
    path('nova/', views.manutencao_create, name='manutencao_create'),
    path('<int:pk>/editar/', views.manutencao_update, name='manutencao_update'),
    path('<int:pk>/edit/', views.manutencao_update, name='manutencao_edit'),
    path('<int:pk>/baixa-rapida/', views.dar_baixa_manutencao, name='dar_baixa_manutencao'),
    path('<int:pk>/excluir/', views.manutencao_delete, name='manutencao_delete'),
]

