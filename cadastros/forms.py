from django import forms
from django.core.exceptions import ValidationError

from .models import ModeloImpressora, NumeroSerie, Setor, TipoDefeito

TAILWIND_TEXT_INPUT_CLASS = (
    'w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm '
    'text-slate-900 placeholder-slate-400 shadow-sm transition uppercase '
    'focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500/20'
)

TAILWIND_CHECKBOX_CLASS = (
    'h-4 w-4 rounded border-slate-300 text-brand-600 '
    'focus:ring-2 focus:ring-brand-500/20 cursor-pointer'
)


class ModeloImpressoraForm(forms.ModelForm):
    class Meta:
        model = ModeloImpressora
        fields = ['nome', 'ativo']
        widgets = {
            'nome': forms.TextInput(
                attrs={
                    'class': TAILWIND_TEXT_INPUT_CLASS,
                    'placeholder': 'Ex: HP 401DNE, HP 1102W',
                    'autocomplete': 'off',
                    'autofocus': 'autofocus',
                }
            ),
            'ativo': forms.CheckboxInput(
                attrs={
                    'class': TAILWIND_CHECKBOX_CLASS,
                }
            ),
        }
        error_messages = {
            'nome': {
                'unique': 'Já existe um Modelo de Impressora cadastrado com este nome.',
                'required': 'Informe o nome do modelo de impressora.',
            }
        }

    def clean_nome(self) -> str:
        nome = (self.cleaned_data.get('nome') or '').strip().upper()
        if not nome:
            raise ValidationError('Informe o nome do modelo de impressora.')
        qs = ModeloImpressora.objects.filter(nome__iexact=nome)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Já existe um Modelo de Impressora cadastrado com este nome.')
        return nome


class NumeroSerieForm(forms.ModelForm):
    class Meta:
        model = NumeroSerie
        fields = ['serial', 'ativo']
        widgets = {
            'serial': forms.TextInput(
                attrs={
                    'class': TAILWIND_TEXT_INPUT_CLASS,
                    'placeholder': 'Ex: CNF8G1M854, BRCSJ7BFLN',
                    'autocomplete': 'off',
                    'autofocus': 'autofocus',
                }
            ),
            'ativo': forms.CheckboxInput(
                attrs={
                    'class': TAILWIND_CHECKBOX_CLASS,
                }
            ),
        }
        error_messages = {
            'serial': {
                'unique': 'Já existe um Número de Série cadastrado com este código.',
                'required': 'Informe o número de série.',
            }
        }

    def clean_serial(self) -> str:
        serial = (self.cleaned_data.get('serial') or '').strip().upper()
        if not serial:
            raise ValidationError('Informe o número de série.')
        qs = NumeroSerie.objects.filter(serial__iexact=serial)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Já existe um Número de Série cadastrado com este código.')
        return serial


class SetorForm(forms.ModelForm):
    class Meta:
        model = Setor
        fields = ['nome', 'ativo']
        widgets = {
            'nome': forms.TextInput(
                attrs={
                    'class': TAILWIND_TEXT_INPUT_CLASS,
                    'placeholder': 'Ex: FARMACIA INTERNA CMI, CONSULTORIO DE CLINICA CIRURGICA',
                    'autocomplete': 'off',
                    'autofocus': 'autofocus',
                }
            ),
            'ativo': forms.CheckboxInput(
                attrs={
                    'class': TAILWIND_CHECKBOX_CLASS,
                }
            ),
        }
        error_messages = {
            'nome': {
                'unique': 'Já existe um Setor cadastrado com este nome.',
                'required': 'Informe o nome do setor.',
            }
        }

    def clean_nome(self) -> str:
        nome = (self.cleaned_data.get('nome') or '').strip().upper()
        if not nome:
            raise ValidationError('Informe o nome do setor.')
        qs = Setor.objects.filter(nome__iexact=nome)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Já existe um Setor cadastrado com este nome.')
        return nome


class TipoDefeitoForm(forms.ModelForm):
    class Meta:
        model = TipoDefeito
        fields = ['descricao', 'ativo']
        widgets = {
            'descricao': forms.TextInput(
                attrs={
                    'class': TAILWIND_TEXT_INPUT_CLASS,
                    'placeholder': 'Ex: ATOLAMENTO NA ENTRADA, ROLO DO FUSOR, NAO LIGA',
                    'autocomplete': 'off',
                    'autofocus': 'autofocus',
                }
            ),
            'ativo': forms.CheckboxInput(
                attrs={
                    'class': TAILWIND_CHECKBOX_CLASS,
                }
            ),
        }
        error_messages = {
            'descricao': {
                'unique': 'Já existe um Tipo de Defeito cadastrado com esta descrição.',
                'required': 'Informe a descrição do defeito.',
            }
        }

    def clean_descricao(self) -> str:
        descricao = (self.cleaned_data.get('descricao') or '').strip().upper()
        if not descricao:
            raise ValidationError('Informe a descrição do defeito.')
        qs = TipoDefeito.objects.filter(descricao__iexact=descricao)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Já existe um Tipo de Defeito cadastrado com esta descrição.')
        return descricao

