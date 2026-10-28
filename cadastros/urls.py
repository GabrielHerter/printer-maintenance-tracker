from django.urls import path

from . import views

app_name = 'cadastros'

urlpatterns = [
    path('', views.index_redirect, name='index'),

    # Modelo de Impressora
    path('modelos/', views.modelo_list, name='modelo_list'),
    path('modelos/novo/', views.modelo_create, name='modelo_create'),
    path('modelos/<int:pk>/toggle-ativo/', views.modelo_toggle_ativo, name='modelo_toggle_ativo'),
    path('modelos/options/', views.modelo_select_options, name='modelo_select_options'),

    # Número de Série
    path('numeros-serie/', views.numero_serie_list, name='numero_serie_list'),
    path('numeros-serie/novo/', views.numero_serie_create, name='numero_serie_create'),
    path('numeros-serie/<int:pk>/toggle-ativo/', views.numero_serie_toggle_ativo, name='numero_serie_toggle_ativo'),
    path('numeros-serie/options/', views.numero_serie_select_options, name='numero_serie_select_options'),

    # Setor
    path('setores/', views.setor_list, name='setor_list'),
    path('setores/novo/', views.setor_create, name='setor_create'),
    path('setores/<int:pk>/toggle-ativo/', views.setor_toggle_ativo, name='setor_toggle_ativo'),
    path('setores/options/', views.setor_select_options, name='setor_select_options'),

    # Tipo de Defeito
    path('tipos-defeito/', views.tipo_defeito_list, name='tipo_defeito_list'),
    path('tipos-defeito/novo/', views.tipo_defeito_create, name='tipo_defeito_create'),
    path('tipos-defeito/<int:pk>/toggle-ativo/', views.tipo_defeito_toggle_ativo, name='tipo_defeito_toggle_ativo'),
    path('tipos-defeito/options/', views.tipo_defeito_select_options, name='tipo_defeito_select_options'),
]

