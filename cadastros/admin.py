from django.contrib import admin

from .models import ModeloImpressora, NumeroSerie, Setor, TipoDefeito


@admin.register(ModeloImpressora)
class ModeloImpressoraAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'criado_em')
    search_fields = ('nome',)
    list_filter = ('ativo', 'criado_em')
    ordering = ('nome',)


@admin.register(NumeroSerie)
class NumeroSerieAdmin(admin.ModelAdmin):
    list_display = ('serial', 'ativo', 'criado_em')
    search_fields = ('serial',)
    list_filter = ('ativo', 'criado_em')
    ordering = ('serial',)


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'criado_em')
    search_fields = ('nome',)
    list_filter = ('ativo', 'criado_em')
    ordering = ('nome',)


@admin.register(TipoDefeito)
class TipoDefeitoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'ativo', 'criado_em')
    search_fields = ('descricao',)
    list_filter = ('ativo', 'criado_em')
    ordering = ('descricao',)
