from datetime import date
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q, QuerySet
from django.http import HttpRequest, HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET, require_http_methods

from cadastros.models import ModeloImpressora, NumeroSerie, Setor, TipoDefeito
from .forms import ManutencaoForm
from .models import Manutencao, SituacaoManutencao

DEFAULT_PAGE_SIZE = 15


def _is_htmx(request: HttpRequest) -> bool:
    return bool(getattr(request, 'htmx', False) or request.headers.get('HX-Request') == 'true')


def _parse_date_param(value: str | None) -> date | None:
    if not value:
        return None
    value = value.strip()
    parsed = parse_date(value)
    if parsed:
        return parsed
    # Suporte para formato DD/MM/YYYY caso enviado manualmente
    parts = value.split('/')
    if len(parts) == 3:
        try:
            return date(int(parts[2]), int(parts[1]), int(parts[0]))
        except ValueError:
            return None
    return None


def _get_base_queryset() -> QuerySet[Manutencao]:
    return Manutencao.objects.select_related(
        'modelo',
        'numero_serie',
        'setor',
        'defeito',
    ).order_by('-data_abertura', '-criado_em')


def _apply_filters(queryset: QuerySet[Manutencao], params) -> tuple[QuerySet[Manutencao], dict]:
    situacao = (params.get('situacao') or '').strip().upper()
    setor_id = (params.get('setor') or '').strip()
    modelo_id = (params.get('modelo') or '').strip()
    defeito_id = (params.get('defeito') or '').strip()

    # Suporte flexível para busca por número de série (q, serial ou numero_serie)
    busca_serial = (
        params.get('q')
        or params.get('serial')
        or params.get('numero_serie')
        or ''
    ).strip()

    data_inicio_raw = (params.get('data_inicio') or params.get('data_de') or '').strip()
    data_fim_raw = (params.get('data_fim') or params.get('data_ate') or '').strip()

    if situacao in (SituacaoManutencao.MANUTENCAO, SituacaoManutencao.RESOLVIDO):
        queryset = queryset.filter(situacao=situacao)
    else:
        situacao = ''

    if setor_id.isdigit():
        queryset = queryset.filter(setor_id=int(setor_id))
    else:
        setor_id = ''

    if modelo_id.isdigit():
        queryset = queryset.filter(modelo_id=int(modelo_id))
    else:
        modelo_id = ''

    if defeito_id.isdigit():
        queryset = queryset.filter(defeito_id=int(defeito_id))
    else:
        defeito_id = ''

    if busca_serial:
        if params.get('numero_serie') and busca_serial.isdigit():
            queryset = queryset.filter(
                Q(numero_serie_id=int(busca_serial))
                | Q(numero_serie__serial__icontains=busca_serial)
            )
        else:
            queryset = queryset.filter(numero_serie__serial__icontains=busca_serial)

    data_inicio = _parse_date_param(data_inicio_raw)
    if data_inicio:
        queryset = queryset.filter(data_abertura__gte=data_inicio)

    data_fim = _parse_date_param(data_fim_raw)
    if data_fim:
        queryset = queryset.filter(data_abertura__lte=data_fim)

    filtros_ativos = bool(
        situacao or setor_id or modelo_id or defeito_id or busca_serial or data_inicio or data_fim
    )

    filter_state = {
        'situacao': situacao,
        'setor_id': setor_id,
        'modelo_id': modelo_id,
        'defeito_id': defeito_id,
        'q': busca_serial,
        'data_inicio': data_inicio.strftime('%Y-%m-%d') if data_inicio else '',
        'data_fim': data_fim.strftime('%Y-%m-%d') if data_fim else '',
        'filtros_ativos': filtros_ativos,
    }
    return queryset, filter_state


def _get_stats(queryset: QuerySet[Manutencao] | None = None) -> dict:
    qs = queryset if queryset is not None else Manutencao.objects.all()
    agg = qs.aggregate(
        total=Count('id'),
        em_manutencao=Count('id', filter=Q(situacao=SituacaoManutencao.MANUTENCAO)),
        resolvidos=Count('id', filter=Q(situacao=SituacaoManutencao.RESOLVIDO)),
        tempo_medio=Avg(
            'tempo_manutencao_dias',
            filter=Q(situacao=SituacaoManutencao.RESOLVIDO),
        ),
    )
    tempo_medio_val = agg['tempo_medio']
    return {
        'total': agg['total'] or 0,
        'em_manutencao': agg['em_manutencao'] or 0,
        'resolvidos': agg['resolvidos'] or 0,
        'tempo_medio': round(float(tempo_medio_val), 1) if tempo_medio_val is not None else 0,
    }


def _build_list_context(request: HttpRequest) -> dict:
    base_qs = _get_base_queryset()
    filtered_qs, filter_state = _apply_filters(base_qs, request.GET)
    stats = _get_stats(filtered_qs)

    per_page_raw = (request.GET.get('per_page') or '').strip()
    if per_page_raw.isdigit() and 1 <= int(per_page_raw) <= 100:
        per_page = int(per_page_raw)
    else:
        per_page = DEFAULT_PAGE_SIZE

    paginator = Paginator(filtered_qs, per_page)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)
    elided_page_range = list(
        paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)
    )

    query_params = request.GET.copy()
    query_params.pop('page', None)
    # Remove chaves vazias para manter a query string limpa
    for key in list(query_params.keys()):
        if not str(query_params.get(key) or '').strip():
            query_params.pop(key, None)
    filter_querystring = query_params.urlencode()

    return {
        'manutencoes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'elided_page_range': elided_page_range,
        'filter_querystring': filter_querystring,
        'per_page': per_page,
        'stats': stats,
        'filtros': filter_state,
        'situacao_choices': SituacaoManutencao.choices,
        'modelos_filtro': ModeloImpressora.objects.filter(ativo=True).order_by('nome'),
        'setores_filtro': Setor.objects.filter(ativo=True).order_by('nome'),
        'defeitos_filtro': TipoDefeito.objects.filter(ativo=True).order_by('descricao'),
        'hoje_iso': timezone.localdate().strftime('%Y-%m-%d'),
    }


@require_GET
def manutencao_list(request: HttpRequest) -> HttpResponse:
    context = _build_list_context(request)

    if _is_htmx(request):
        return render(request, 'manutencoes/partials/tabela_manutencoes.html', context)

    return render(request, 'manutencoes/manutencao_list.html', context)


@require_http_methods(['GET', 'POST'])
def manutencao_create(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = ManutencaoForm(request.POST)
        if form.is_valid():
            manutencao = form.save()
            manutencao = _get_base_queryset().get(pk=manutencao.pk)

            if _is_htmx(request):
                context = _build_list_context(request)
                context['manutencao_criada'] = manutencao
                context['oob_update_table'] = True
                context['oob_stats'] = True
                response = render(
                    request,
                    'manutencoes/partials/oob_mutacao_response.html',
                    context,
                )
                response['HX-Retarget'] = '#modal-container'
                response['HX-Reswap'] = 'innerHTML'
                response['HX-Trigger'] = 'manutencaoAtualizada'
                return response

            return redirect('manutencoes:manutencao_list')

        context = {
            'form': form,
            'is_edit': False,
            'modal_title': 'Nova Ordem de Manutenção',
            'action_url': request.path,
        }
        return render(request, 'manutencoes/partials/modal_form.html', context)

    form = ManutencaoForm()
    context = {
        'form': form,
        'is_edit': False,
        'modal_title': 'Nova Ordem de Manutenção',
        'action_url': request.path,
    }
    return render(request, 'manutencoes/partials/modal_form.html', context)


@require_http_methods(['GET', 'POST'])
def manutencao_update(request: HttpRequest, pk: int) -> HttpResponse:
    manutencao = get_object_or_404(_get_base_queryset(), pk=pk)

    if request.method == 'POST':
        form = ManutencaoForm(request.POST, instance=manutencao)
        if form.is_valid():
            manutencao = form.save()
            manutencao = _get_base_queryset().get(pk=manutencao.pk)

            if _is_htmx(request):
                stats = _get_stats()
                context = {
                    'manutencao': manutencao,
                    'stats': stats,
                    'hoje_iso': timezone.localdate().strftime('%Y-%m-%d'),
                    'oob_row': True,
                    'oob_stats': True,
                }
                response = render(
                    request,
                    'manutencoes/partials/oob_mutacao_response.html',
                    context,
                )
                response['HX-Retarget'] = '#modal-container'
                response['HX-Reswap'] = 'innerHTML'
                response['HX-Trigger'] = 'manutencaoAtualizada'
                return response

            return redirect('manutencoes:manutencao_list')

        context = {
            'form': form,
            'manutencao': manutencao,
            'is_edit': True,
            'modal_title': f'Editar Manutenção #{manutencao.pk}',
            'action_url': request.path,
        }
        return render(request, 'manutencoes/partials/modal_form.html', context)

    form = ManutencaoForm(instance=manutencao)
    context = {
        'form': form,
        'manutencao': manutencao,
        'is_edit': True,
        'modal_title': f'Editar Manutenção #{manutencao.pk}',
        'action_url': request.path,
    }
    return render(request, 'manutencoes/partials/modal_form.html', context)


@require_http_methods(['POST', 'PUT', 'PATCH'])
def dar_baixa_manutencao(request: HttpRequest, pk: int) -> HttpResponse:
    manutencao = get_object_or_404(_get_base_queryset(), pk=pk)

    if request.method in ('PUT', 'PATCH') and not request.POST:
        data = QueryDict(request.body)
    else:
        data = request.POST

    raw_data_retorno = (data.get('data_retorno') or '').strip()
    hoje_iso = timezone.localdate().strftime('%Y-%m-%d')

    if not raw_data_retorno:
        context = {
            'manutencao': manutencao,
            'hoje_iso': hoje_iso,
            'baixa_erro': 'Informe a data de retorno.',
        }
        return render(request, 'manutencoes/partials/linha_manutencao.html', context)

    parsed_retorno = _parse_date_param(raw_data_retorno)
    if not parsed_retorno:
        context = {
            'manutencao': manutencao,
            'hoje_iso': hoje_iso,
            'baixa_erro': 'Data de retorno inválida.',
        }
        return render(request, 'manutencoes/partials/linha_manutencao.html', context)

    manutencao.data_retorno = parsed_retorno
    try:
        manutencao.save()
    except ValidationError as exc:
        # Restaura estado original para exibição limpa da linha com o erro
        manutencao.refresh_from_db()
        mensagens = []
        if hasattr(exc, 'message_dict'):
            for msgs in exc.message_dict.values():
                mensagens.extend(msgs)
        else:
            mensagens.extend(exc.messages)
        context = {
            'manutencao': manutencao,
            'hoje_iso': hoje_iso,
            'baixa_erro': ' '.join(mensagens) or 'Erro ao registrar data de retorno.',
        }
        return render(request, 'manutencoes/partials/linha_manutencao.html', context)

    manutencao = _get_base_queryset().get(pk=manutencao.pk)
    stats = _get_stats()

    context = {
        'manutencao': manutencao,
        'stats': stats,
        'hoje_iso': hoje_iso,
        'oob_stats': True,
    }
    response = render(request, 'manutencoes/partials/linha_manutencao.html', context)
    response['HX-Trigger'] = 'manutencaoAtualizada'
    return response


@require_http_methods(['POST', 'DELETE'])
def manutencao_delete(request: HttpRequest, pk: int) -> HttpResponse:
    manutencao = get_object_or_404(Manutencao, pk=pk)
    manutencao.delete()

    if _is_htmx(request):
        stats = _get_stats()
        context = {
            'stats': stats,
            'oob_stats': True,
        }
        response = render(
            request,
            'manutencoes/partials/oob_mutacao_response.html',
            context,
        )
        response['HX-Trigger'] = 'manutencaoAtualizada'
        return response

    return redirect('manutencoes:manutencao_list')
