from django.db import models


class ModeloImpressora(models.Model):
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome do Modelo',
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo',
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
    )

    class Meta:
        verbose_name = 'Modelo de Impressora'
        verbose_name_plural = 'Modelos de Impressora'
        ordering = ['nome']

    def __str__(self) -> str:
        return self.nome


class NumeroSerie(models.Model):
    serial = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Número de Série',
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo',
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
    )

    class Meta:
        verbose_name = 'Número de Série'
        verbose_name_plural = 'Números de Série'
        ordering = ['serial']

    def __str__(self) -> str:
        return self.serial


class Setor(models.Model):
    nome = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Nome do Setor',
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo',
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
    )

    class Meta:
        verbose_name = 'Setor'
        verbose_name_plural = 'Setores'
        ordering = ['nome']

    def __str__(self) -> str:
        return self.nome


class TipoDefeito(models.Model):
    descricao = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Descrição do Defeito',
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo',
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
    )

    class Meta:
        verbose_name = 'Tipo de Defeito'
        verbose_name_plural = 'Tipos de Defeito'
        ordering = ['descricao']

    def __str__(self) -> str:
        return self.descricao
