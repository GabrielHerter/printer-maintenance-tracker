from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from cadastros.models import ModeloImpressora, NumeroSerie, Setor, TipoDefeito


class SituacaoManutencao(models.TextChoices):
    MANUTENCAO = 'MANUTENCAO', 'Manutenção'
    RESOLVIDO = 'RESOLVIDO', 'Resolvido'


class Manutencao(models.Model):
    modelo = models.ForeignKey(
        ModeloImpressora,
        on_delete=models.PROTECT,
        related_name='manutencoes',
        verbose_name='Modelo de Impressora',
    )
    numero_serie = models.ForeignKey(
        NumeroSerie,
        on_delete=models.PROTECT,
        related_name='manutencoes',
        verbose_name='Número de Série',
    )
    setor = models.ForeignKey(
        Setor,
        on_delete=models.PROTECT,
        related_name='manutencoes',
        verbose_name='Setor',
    )
    defeito = models.ForeignKey(
        TipoDefeito,
        on_delete=models.PROTECT,
        related_name='manutencoes',
        verbose_name='Tipo de Defeito',
    )

    data_abertura = models.DateField(
        verbose_name='Data de Abertura',
    )
    data_retorno = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Retorno',
    )

    situacao = models.CharField(
        max_length=20,
        choices=SituacaoManutencao.choices,
        default=SituacaoManutencao.MANUTENCAO,
        verbose_name='Situação',
    )
    tempo_manutencao_dias = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Tempo de Manutenção (dias)',
    )
    observacao = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observação',
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em',
    )

    class Meta:
        verbose_name = 'Manutenção'
        verbose_name_plural = 'Manutenções'
        ordering = ['-data_abertura', '-criado_em']

    def __str__(self) -> str:
        return f"{self.modelo} ({self.numero_serie}) - {self.get_situacao_display()}"

    @property
    def dias_em_aberto(self) -> int:
        """Retorna a quantidade de dias em manutenção até hoje para itens não resolvidos."""
        if self.data_retorno is not None and self.tempo_manutencao_dias is not None:
            return self.tempo_manutencao_dias
        if not self.data_abertura:
            return 0
        hoje = timezone.localdate()
        return max(0, (hoje - self.data_abertura).days)

    def clean(self) -> None:
        super().clean()

        if self.data_retorno is not None:
            if self.data_abertura and self.data_retorno < self.data_abertura:
                raise ValidationError({
                    'data_retorno': 'A data de retorno não pode ser anterior à data de abertura.'
                })
            self.situacao = SituacaoManutencao.RESOLVIDO
            if self.data_abertura:
                self.tempo_manutencao_dias = (self.data_retorno - self.data_abertura).days
        else:
            self.situacao = SituacaoManutencao.MANUTENCAO
            self.tempo_manutencao_dias = None

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
