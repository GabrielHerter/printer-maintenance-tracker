from django.contrib import admin

from .models import Manutencao


@admin.register(Manutencao)
class ManutencaoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'modelo',
        'numero_serie',
        'setor',
        'defeito',
        'data_abertura',
        'data_retorno',
        'situacao',
        'tempo_manutencao_dias',
    )
    list_select_related = ('modelo', 'numero_serie', 'setor', 'defeito')
    search_fields = (
        'modelo__nome',
        'numero_serie__serial',
        'setor__nome',
        'defeito__descricao',
        'observacao',
    )
    list_filter = (
        'situacao',
        'data_abertura',
        'data_retorno',
        'modelo',
        'setor',
        'defeito',
    )
    autocomplete_fields = ('modelo', 'numero_serie', 'setor', 'defeito')
    readonly_fields = ('situacao', 'tempo_manutencao_dias', 'criado_em', 'atualizado_em')
    ordering = ('-data_abertura', '-criado_em')
