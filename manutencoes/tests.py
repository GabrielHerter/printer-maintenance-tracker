from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cadastros.models import ModeloImpressora, NumeroSerie, Setor, TipoDefeito
from .forms import ManutencaoForm
from .models import Manutencao, SituacaoManutencao


class ManutencoesOperationalModuleTests(TestCase):
    def setUp(self):
        self.modelo_ativo = ModeloImpressora.objects.create(nome='HP 401DNE', ativo=True)
        self.modelo_inativo = ModeloImpressora.objects.create(nome='HP 1102W', ativo=False)

        self.serial_ativo = NumeroSerie.objects.create(serial='CNF8G1M854', ativo=True)
        self.serial_ativo_2 = NumeroSerie.objects.create(serial='BRCSJ7BFLN', ativo=True)
        self.serial_inativo = NumeroSerie.objects.create(serial='INATIVO999', ativo=False)

        self.setor_ativo = Setor.objects.create(nome='FARMACIA INTERNA CMI', ativo=True)
        self.setor_ativo_2 = Setor.objects.create(nome='CONSULTORIO DE CLINICA CIRURGICA', ativo=True)
        self.setor_inativo = Setor.objects.create(nome='SETOR DESATIVADO', ativo=False)

        self.defeito_ativo = TipoDefeito.objects.create(descricao='ATOLAMENTO NA ENTRADA', ativo=True)
        self.defeito_inativo = TipoDefeito.objects.create(descricao='DEFEITO INATIVO', ativo=False)

    def test_manutencao_form_filters_only_active_records_and_uses_date_widgets(self):
        form = ManutencaoForm()

        self.assertQuerySetEqual(
            form.fields['modelo'].queryset,
            [self.modelo_ativo],
        )
        self.assertQuerySetEqual(
            form.fields['numero_serie'].queryset,
            [self.serial_ativo_2, self.serial_ativo],
        )
        self.assertQuerySetEqual(
            form.fields['setor'].queryset,
            [self.setor_ativo_2, self.setor_ativo],
        )
        self.assertQuerySetEqual(
            form.fields['defeito'].queryset,
            [self.defeito_ativo],
        )

        self.assertEqual(form.fields['data_abertura'].widget.input_type, 'date')
        self.assertEqual(form.fields['data_retorno'].widget.input_type, 'date')

    def test_create_manutencao_via_htmx_triggers_event(self):
        url = reverse('manutencoes:manutencao_create')
        response = self.client.post(
            url,
            data={
                'modelo': self.modelo_ativo.pk,
                'numero_serie': self.serial_ativo.pk,
                'setor': self.setor_ativo.pk,
                'defeito': self.defeito_ativo.pk,
                'data_abertura': '2026-10-01',
                'data_retorno': '',
                'observacao': 'Aguardando peça do fusor',
            },
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Trigger'], 'manutencaoAtualizada')

        manutencao = Manutencao.objects.get()
        self.assertEqual(manutencao.situacao, SituacaoManutencao.MANUTENCAO)
        self.assertIsNone(manutencao.tempo_manutencao_dias)

    def test_dar_baixa_manutencao_recalculates_status_days_and_triggers_event(self):
        manutencao = Manutencao.objects.create(
            modelo=self.modelo_ativo,
            numero_serie=self.serial_ativo,
            setor=self.setor_ativo,
            defeito=self.defeito_ativo,
            data_abertura=date(2026, 10, 10),
        )
        self.assertEqual(manutencao.situacao, SituacaoManutencao.MANUTENCAO)

        url = reverse('manutencoes:dar_baixa_manutencao', args=[manutencao.pk])
        response = self.client.post(
            url,
            data={'data_retorno': '2026-10-15'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Trigger'], 'manutencaoAtualizada')

        manutencao.refresh_from_db()
        self.assertEqual(manutencao.situacao, SituacaoManutencao.RESOLVIDO)
        self.assertEqual(manutencao.data_retorno, date(2026, 10, 15))
        self.assertEqual(manutencao.tempo_manutencao_dias, 5)
        self.assertContains(response, 'RESOLVIDO')
        self.assertContains(response, '5 dias')

    def test_dar_baixa_rejects_return_date_before_opening_date(self):
        manutencao = Manutencao.objects.create(
            modelo=self.modelo_ativo,
            numero_serie=self.serial_ativo,
            setor=self.setor_ativo,
            defeito=self.defeito_ativo,
            data_abertura=date(2026, 10, 10),
        )
        url = reverse('manutencoes:dar_baixa_manutencao', args=[manutencao.pk])
        response = self.client.post(
            url,
            data={'data_retorno': '2026-10-05'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('HX-Trigger', response)

        manutencao.refresh_from_db()
        self.assertEqual(manutencao.situacao, SituacaoManutencao.MANUTENCAO)
        self.assertIsNone(manutencao.data_retorno)
        self.assertContains(response, 'A data de retorno não pode ser anterior à data de abertura.')

    def test_update_manutencao_via_modal_triggers_event(self):
        manutencao = Manutencao.objects.create(
            modelo=self.modelo_ativo,
            numero_serie=self.serial_ativo,
            setor=self.setor_ativo,
            defeito=self.defeito_ativo,
            data_abertura=date(2026, 10, 1),
        )
        url = reverse('manutencoes:manutencao_update', args=[manutencao.pk])
        response = self.client.post(
            url,
            data={
                'modelo': self.modelo_ativo.pk,
                'numero_serie': self.serial_ativo.pk,
                'setor': self.setor_ativo_2.pk,
                'defeito': self.defeito_ativo.pk,
                'data_abertura': '2026-10-01',
                'data_retorno': '2026-10-04',
                'observacao': 'Rolo fusor substituído',
            },
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Trigger'], 'manutencaoAtualizada')

        manutencao.refresh_from_db()
        self.assertEqual(manutencao.setor, self.setor_ativo_2)
        self.assertEqual(manutencao.situacao, SituacaoManutencao.RESOLVIDO)
        self.assertEqual(manutencao.tempo_manutencao_dias, 3)

    def test_list_view_filters_and_avoids_n_plus_one_queries(self):
        hoje = timezone.localdate()
        m1 = Manutencao.objects.create(
            modelo=self.modelo_ativo,
            numero_serie=self.serial_ativo,
            setor=self.setor_ativo,
            defeito=self.defeito_ativo,
            data_abertura=hoje - timedelta(days=7),
        )
        m2 = Manutencao.objects.create(
            modelo=self.modelo_ativo,
            numero_serie=self.serial_ativo_2,
            setor=self.setor_ativo_2,
            defeito=self.defeito_ativo,
            data_abertura=hoje - timedelta(days=3),
            data_retorno=hoje - timedelta(days=1),
        )

        list_url = reverse('manutencoes:manutencao_list')

        # Filtro por situação MANUTENCAO via HTMX
        resp_manut = self.client.get(
            list_url,
            data={'situacao': 'MANUTENCAO'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(resp_manut.status_code, 200)
        self.assertContains(resp_manut, self.serial_ativo.serial)
        self.assertNotContains(resp_manut, self.serial_ativo_2.serial)
        self.assertContains(resp_manut, '7 dias em aberto')

        # Filtro por busca de serial
        resp_serial = self.client.get(
            list_url,
            data={'q': 'BRCSJ7'},
            HTTP_HX_REQUEST='true',
        )
        self.assertContains(resp_serial, self.serial_ativo_2.serial)
        self.assertNotContains(resp_serial, self.serial_ativo.serial)

        # Filtro por setor
        resp_setor = self.client.get(
            list_url,
            data={'setor': self.setor_ativo.pk},
            HTTP_HX_REQUEST='true',
        )
        self.assertContains(resp_setor, m1.numero_serie.serial)
        self.assertNotContains(resp_setor, m2.numero_serie.serial)

    def test_htmx_pagination_preserves_active_filters_in_querystring(self):
        hoje = timezone.localdate()
        for i in range(18):
            Manutencao.objects.create(
                modelo=self.modelo_ativo,
                numero_serie=self.serial_ativo,
                setor=self.setor_ativo,
                defeito=self.defeito_ativo,
                data_abertura=hoje - timedelta(days=i),
                observacao=f'Ordem paginada {i}',
            )

        list_url = reverse('manutencoes:manutencao_list')
        resp_page1 = self.client.get(
            list_url,
            data={'situacao': 'MANUTENCAO', 'setor': self.setor_ativo.pk, 'page': 1},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(resp_page1.status_code, 200)
        self.assertContains(resp_page1, 'Página 1 de 2')
        self.assertContains(resp_page1, f'situacao=MANUTENCAO&amp;setor={self.setor_ativo.pk}')

        resp_page2 = self.client.get(
            list_url,
            data={'situacao': 'MANUTENCAO', 'setor': self.setor_ativo.pk, 'page': 2},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(resp_page2.status_code, 200)
        self.assertContains(resp_page2, 'Página 2 de 2')
        self.assertEqual(len(resp_page2.context['page_obj']), 3)
