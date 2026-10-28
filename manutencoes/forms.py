from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from cadastros.models import ModeloImpressora, NumeroSerie, Setor, TipoDefeito
from .models import Manutencao

TAILWIND_SELECT_CLASS = (
    'js-searchable-select w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm '
    'text-slate-900 shadow-sm transition '
    'focus:border-hc-blue focus:outline-none focus:ring-2 focus:ring-hc-blue/20'
)

TAILWIND_DATE_INPUT_CLASS = (
    'w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm '
    'text-slate-900 shadow-sm transition '
    'focus:border-hc-blue focus:outline-none focus:ring-2 focus:ring-hc-blue/20'
)

TAILWIND_TEXTAREA_CLASS = (
    'w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm '
    'text-slate-900 placeholder-slate-400 shadow-sm transition '
    'focus:border-hc-blue focus:outline-none focus:ring-2 focus:ring-hc-blue/20'
)

SEARCHABLE_SELECT_PLACEHOLDER = 'Selecione ou digite para pesquisar...'


class ManutencaoForm(forms.ModelForm):
    modelo = forms.ModelChoiceField(
        queryset=ModeloImpressora.objects.filter(ativo=True).order_by('nome'),
        label='Modelo de Impressora',
        empty_label=SEARCHABLE_SELECT_PLACEHOLDER,
        widget=forms.Select(
            attrs={
                'class': TAILWIND_SELECT_CLASS,
                'placeholder': SEARCHABLE_SELECT_PLACEHOLDER,
                'data-placeholder': SEARCHABLE_SELECT_PLACEHOLDER,
                'autocomplete': 'off',
            }
        ),
    )
    numero_serie = forms.ModelChoiceField(
        queryset=NumeroSerie.objects.filter(ativo=True).order_by('serial'),
        label='Número de Série',
        empty_label=SEARCHABLE_SELECT_PLACEHOLDER,
        widget=forms.Select(
            attrs={
                'class': TAILWIND_SELECT_CLASS,
                'placeholder': SEARCHABLE_SELECT_PLACEHOLDER,
                'data-placeholder': SEARCHABLE_SELECT_PLACEHOLDER,
                'autocomplete': 'off',
            }
        ),
    )
    setor = forms.ModelChoiceField(
        queryset=Setor.objects.filter(ativo=True).order_by('nome'),
        label='Setor',
        empty_label=SEARCHABLE_SELECT_PLACEHOLDER,
        widget=forms.Select(
            attrs={
                'class': TAILWIND_SELECT_CLASS,
                'placeholder': SEARCHABLE_SELECT_PLACEHOLDER,
                'data-placeholder': SEARCHABLE_SELECT_PLACEHOLDER,
                'autocomplete': 'off',
            }
        ),
    )
    defeito = forms.ModelChoiceField(
        queryset=TipoDefeito.objects.filter(ativo=True).order_by('descricao'),
        label='Tipo de Defeito',
        empty_label=SEARCHABLE_SELECT_PLACEHOLDER,
        widget=forms.Select(
            attrs={
                'class': TAILWIND_SELECT_CLASS,
                'placeholder': SEARCHABLE_SELECT_PLACEHOLDER,
                'data-placeholder': SEARCHABLE_SELECT_PLACEHOLDER,
                'autocomplete': 'off',
            }
        ),
    )

    class Meta:
        model = Manutencao
        fields = [
            'modelo',
            'numero_serie',
            'setor',
            'defeito',
            'data_abertura',
            'data_retorno',
            'observacao',
        ]
        widgets = {
            'data_abertura': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'class': TAILWIND_DATE_INPUT_CLASS,
                },
            ),
            'data_retorno': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'class': TAILWIND_DATE_INPUT_CLASS,
                },
            ),
            'observacao': forms.Textarea(
                attrs={
                    'class': TAILWIND_TEXTAREA_CLASS,
                    'rows': 3,
                    'placeholder': 'Observações técnicas, peças trocadas, protocolo ou detalhes do reparo (opcional)...',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['modelo'].queryset = ModeloImpressora.objects.filter(ativo=True).order_by('nome')
        self.fields['numero_serie'].queryset = NumeroSerie.objects.filter(ativo=True).order_by('serial')
        self.fields['setor'].queryset = Setor.objects.filter(ativo=True).order_by('nome')
        self.fields['defeito'].queryset = TipoDefeito.objects.filter(ativo=True).order_by('descricao')

        self.fields['data_abertura'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
        self.fields['data_retorno'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
        self.fields['data_retorno'].required = False
        self.fields['observacao'].required = False

        if not self.is_bound and not self.instance.pk and not self.initial.get('data_abertura'):
            self.initial['data_abertura'] = timezone.localdate().strftime('%Y-%m-%d')

    def clean(self):
        cleaned_data = super().clean()
        data_abertura = cleaned_data.get('data_abertura')
        data_retorno = cleaned_data.get('data_retorno')

        if data_abertura and data_retorno and data_retorno < data_abertura:
            self.add_error(
                'data_retorno',
                ValidationError('A data de retorno não pode ser anterior à data de abertura.'),
            )

        return cleaned_data

