import json
from dataclasses import dataclass
from typing import Type

from django.db import models
from django.http import HttpRequest, HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import (
    ModeloImpressoraForm,
    NumeroSerieForm,
    SetorForm,
    TipoDefeitoForm,
)
from .models import ModeloImpressora, NumeroSerie, Setor, TipoDefeito


@dataclass(frozen=True)
class EntityConfig:
    key: str
    slug: str
    model: Type[models.Model]
    form_class: type
    title: str
    title_singular: str
    subtitle: str
    field_name: str
    field_label: str
    placeholder_search: str
    list_url_name: str
    create_url_name: str
    toggle_url_name: str
    options_url_name: str
    select_id: str


ENTITY_CONFIGS: dict[str, EntityConfig] = {
    'modelo': EntityConfig(
        key='modelo',
        slug='modelos',
        model=ModeloImpressora,
        form_class=ModeloImpressoraForm,
        title='Modelos de Impressora',
        title_singular='Modelo de Impressora',
        subtitle='Cadastro independente de modelos de equipamentos (ex: HP 401DNE, HP 1102W).',
        field_name='nome',
        field_label='Modelo',
        placeholder_search='Buscar por nome do modelo...',
        list_url_name='cadastros:modelo_list',
        create_url_name='cadastros:modelo_create',
        toggle_url_name='cadastros:modelo_toggle_ativo',
        options_url_name='cadastros:modelo_select_options',
        select_id='id_modelo',
    ),
    'numero_serie': EntityConfig(
        key='numero_serie',
        slug='numeros-serie',
        model=NumeroSerie,
        form_class=NumeroSerieForm,
        title='Números de Série',
        title_singular='Número de Série',
        subtitle='Cadastro independente de seriais físicos das impressoras (ex: CNF8G1M854).',
        field_name='serial',
        field_label='Número de Série',
        placeholder_search='Buscar por número de série...',
        list_url_name='cadastros:numero_serie_list',
        create_url_name='cadastros:numero_serie_create',
        toggle_url_name='cadastros:numero_serie_toggle_ativo',
        options_url_name='cadastros:numero_serie_select_options',
        select_id='id_numero_serie',
    ),
    'setor': EntityConfig(
        key='setor',
        slug='setores',
        model=Setor,
        form_class=SetorForm,
        title='Setores',
        title_singular='Setor',
        subtitle='Cadastro independente de unidades e setores hospitalares/corporativos.',
        field_name='nome',
        field_label='Setor',
        placeholder_search='Buscar por nome do setor...',
        list_url_name='cadastros:setor_list',
        create_url_name='cadastros:setor_create',
        toggle_url_name='cadastros:setor_toggle_ativo',
        options_url_name='cadastros:setor_select_options',
        select_id='id_setor',
    ),
    'tipo_defeito': EntityConfig(
        key='tipo_defeito',
        slug='tipos-defeito',
        model=TipoDefeito,
        form_class=TipoDefeitoForm,
        title='Tipos de Defeito',
        title_singular='Tipo de Defeito',
        subtitle='Catálogo padronizado de falhas e defeitos recorrentes.',
        field_name='descricao',
        field_label='Descrição do Defeito',
        placeholder_search='Buscar por descrição do defeito...',
        list_url_name='cadastros:tipo_defeito_list',
        create_url_name='cadastros:tipo_defeito_create',
        toggle_url_name='cadastros:tipo_defeito_toggle_ativo',
        options_url_name='cadastros:tipo_defeito_select_options',
        select_id='id_defeito',
    ),
}


def _get_config(entity_key: str) -> EntityConfig:
    config = ENTITY_CONFIGS.get(entity_key)
    if not config:
        raise Http404(f"Entidade '{entity_key}' não encontrada.")
    return config


def _is_htmx(request: HttpRequest) -> bool:
    return bool(getattr(request, 'htmx', False) or request.headers.get('HX-Request') == 'true')


def _get_stats(config: EntityConfig) -> dict[str, int]:
    qs = config.model.objects.all()
    total = qs.count()
    ativos = qs.filter(ativo=True).count()
    return {
        'total': total,
        'ativos': ativos,
        'inativos': total - ativos,
    }


def _attach_item_display(items, config: EntityConfig):
    for item in items:
        item.valor_principal = getattr(item, config.field_name)
        item.toggle_url = reverse(config.toggle_url_name, args=[item.pk])
    return items


@require_GET
def index_redirect(request: HttpRequest) -> HttpResponse:
    return redirect('cadastros:modelo_list')


@require_GET
def cadastro_list(request: HttpRequest, entity_key: str) -> HttpResponse:
    config = _get_config(entity_key)
    q = (request.GET.get('q') or '').strip()
    status_filter = (request.GET.get('status') or 'todos').strip().lower()

    queryset = config.model.objects.all()
    if q:
        queryset = queryset.filter(**{f'{config.field_name}__icontains': q})
    if status_filter == 'ativos':
        queryset = queryset.filter(ativo=True)
    elif status_filter == 'inativos':
        queryset = queryset.filter(ativo=False)

    items = _attach_item_display(list(queryset), config)
    stats = _get_stats(config)

    context = {
        'config': config,
        'entity_key': config.key,
        'items': items,
        'q': q,
        'status_filter': status_filter,
        'stats': stats,
        'list_url': reverse(config.list_url_name),
        'create_url': reverse(config.create_url_name),
        'all_configs': ENTITY_CONFIGS.values(),
    }

    if _is_htmx(request) and request.headers.get('HX-Target') in ('tabela-cadastros-container', 'lista-itens-body'):
        return render(request, 'cadastros/partials/tabela_itens.html', context)

    return render(request, 'cadastros/cadastro_list.html', context)


@require_http_methods(['GET', 'POST'])
def cadastro_create_modal(request: HttpRequest, entity_key: str) -> HttpResponse:
    config = _get_config(entity_key)
    create_url = reverse(config.create_url_name)

    if request.method == 'POST':
        form = config.form_class(request.POST)
        if form.is_valid():
            instance = form.save()
            label = getattr(instance, config.field_name)

            trigger_payload = {
                'closeModal': {
                    'entity': config.key,
                    'id': instance.pk,
                    'label': label,
                },
                'cadastroUpdated': {
                    'entity': config.key,
                    'id': instance.pk,
                    'label': label,
                    'select_id': config.select_id,
                },
                f'{config.key}Created': {
                    'id': instance.pk,
                    'label': label,
                    'select_id': config.select_id,
                },
                f'{config.key}Updated': {
                    'id': instance.pk,
                    'label': label,
                },
            }

            response = HttpResponse('', status=200)
            response['HX-Retarget'] = '#modal-container'
            response['HX-Reswap'] = 'innerHTML'
            response['HX-Trigger'] = json.dumps(trigger_payload)
            return response

        context = {
            'config': config,
            'form': form,
            'action_url': create_url,
        }
        return render(request, 'cadastros/partials/modal_form.html', context)

    form = config.form_class()
    context = {
        'config': config,
        'form': form,
        'action_url': create_url,
    }
    return render(request, 'cadastros/partials/modal_form.html', context)


@require_POST
def cadastro_toggle_ativo(request: HttpRequest, entity_key: str, pk: int) -> HttpResponse:
    config = _get_config(entity_key)
    item = get_object_or_404(config.model, pk=pk)
    item.ativo = not item.ativo
    item.save(update_fields=['ativo'])

    item.valor_principal = getattr(item, config.field_name)
    item.toggle_url = reverse(config.toggle_url_name, args=[item.pk])
    stats = _get_stats(config)

    context = {
        'item': item,
        'config': config,
        'stats': stats,
        'oob_stats': True,
    }

    response = render(request, 'cadastros/partials/linha_item.html', context)
    trigger_payload = {
        f'{config.key}Updated': {
            'id': item.pk,
            'ativo': item.ativo,
            'label': item.valor_principal,
        },
        'cadastroStatusToggled': {
            'entity': config.key,
            'id': item.pk,
            'ativo': item.ativo,
        },
    }
    response['HX-Trigger'] = json.dumps(trigger_payload)
    return response


@require_GET
def cadastro_select_options(request: HttpRequest, entity_key: str) -> HttpResponse:
    config = _get_config(entity_key)
    items = list(config.model.objects.filter(ativo=True))
    for item in items:
        item.valor_principal = getattr(item, config.field_name)

    selected_id = request.GET.get('selected')
    if selected_id and selected_id.isdigit():
        selected_pk = int(selected_id)
    else:
        latest = config.model.objects.filter(ativo=True).order_by('-id').first()
        selected_pk = latest.pk if latest else None

    context = {
        'config': config,
        'items': items,
        'selected_pk': selected_pk,
        'empty_label': f'Selecione {config.title_singular.lower()}...',
    }
    return render(request, 'cadastros/partials/select_options.html', context)


# Explicit entity views delegating to the core handlers
@require_GET
def modelo_list(request: HttpRequest) -> HttpResponse:
    return cadastro_list(request, 'modelo')


@require_http_methods(['GET', 'POST'])
def modelo_create(request: HttpRequest) -> HttpResponse:
    return cadastro_create_modal(request, 'modelo')


@require_POST
def modelo_toggle_ativo(request: HttpRequest, pk: int) -> HttpResponse:
    return cadastro_toggle_ativo(request, 'modelo', pk)


@require_GET
def modelo_select_options(request: HttpRequest) -> HttpResponse:
    return cadastro_select_options(request, 'modelo')


@require_GET
def numero_serie_list(request: HttpRequest) -> HttpResponse:
    return cadastro_list(request, 'numero_serie')


@require_http_methods(['GET', 'POST'])
def numero_serie_create(request: HttpRequest) -> HttpResponse:
    return cadastro_create_modal(request, 'numero_serie')


@require_POST
def numero_serie_toggle_ativo(request: HttpRequest, pk: int) -> HttpResponse:
    return cadastro_toggle_ativo(request, 'numero_serie', pk)


@require_GET
def numero_serie_select_options(request: HttpRequest) -> HttpResponse:
    return cadastro_select_options(request, 'numero_serie')


@require_GET
def setor_list(request: HttpRequest) -> HttpResponse:
    return cadastro_list(request, 'setor')


@require_http_methods(['GET', 'POST'])
def setor_create(request: HttpRequest) -> HttpResponse:
    return cadastro_create_modal(request, 'setor')


@require_POST
def setor_toggle_ativo(request: HttpRequest, pk: int) -> HttpResponse:
    return cadastro_toggle_ativo(request, 'setor', pk)


@require_GET
def setor_select_options(request: HttpRequest) -> HttpResponse:
    return cadastro_select_options(request, 'setor')


@require_GET
def tipo_defeito_list(request: HttpRequest) -> HttpResponse:
    return cadastro_list(request, 'tipo_defeito')


@require_http_methods(['GET', 'POST'])
def tipo_defeito_create(request: HttpRequest) -> HttpResponse:
    return cadastro_create_modal(request, 'tipo_defeito')


@require_POST
def tipo_defeito_toggle_ativo(request: HttpRequest, pk: int) -> HttpResponse:
    return cadastro_toggle_ativo(request, 'tipo_defeito', pk)


@require_GET
def tipo_defeito_select_options(request: HttpRequest) -> HttpResponse:
    return cadastro_select_options(request, 'tipo_defeito')
