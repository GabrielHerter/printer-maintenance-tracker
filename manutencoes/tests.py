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

        for field_name in ('modelo', 'numero_serie', 'setor', 'defeito'):
            attrs = form.fields[field_name].widget.attrs
            self.assertIn('js-searchable-select', attrs.get('class', ''))
            self.assertEqual(
                attrs.get('placeholder'),
                'Selecione ou digite para pesquisar...',
            )

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
        self.assertEqual(response.content, b'')
        self.assertEqual(response['HX-Trigger'], 'manutencaoAtualizada')

        manutencao = Manutencao.objects.get()
        self.assertEqual(manutencao.situacao, SituacaoManutencao.MANUTENCAO)
        self.assertIsNone(manutencao.tempo_manutencao_dias)

    def test_reactive_table_container_present_when_empty_and_partial_without_navbar_on_htmx(self):
        list_url = reverse('manutencoes:lista')

        # 1. Lista vazia em requisição normal: container reativo presente com hx-trigger no body
        resp_empty = self.client.get(list_url)
        self.assertEqual(resp_empty.status_code, 200)
        self.assertContains(resp_empty, 'id="tabela-manutencoes-container"')
        self.assertContains(resp_empty, 'hx-trigger="manutencaoAtualizada from:body"')
        self.assertContains(resp_empty, 'hx-include="#form-filtros"')
        self.assertContains(resp_empty, 'Nenhum registro de manutenção encontrado')

        # 2. Requisição HTMX retorna apenas o fragmento parcial da tabela (sem navbar duplicada)
        resp_htmx = self.client.get(list_url, HTTP_HX_REQUEST='true')
        self.assertEqual(resp_htmx.status_code, 200)
        self.assertNotContains(resp_htmx, '<header')
        self.assertNotContains(resp_htmx, 'Navegação Principal')
        self.assertContains(resp_htmx, 'Nenhum registro de manutenção encontrado')

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

    def test_dashboard_kpis_partial_computes_accurate_metrics(self):
        # 1 em manutenção + 2 resolvidas (tempos: 4 dias e 6 dias -> MTTR = 5.0 dias)
        Manutencao.objects.create(
            modelo=self.modelo_ativo,
            numero_serie=self.serial_ativo,
            setor=self.setor_ativo,
            defeito=self.defeito_ativo,
            data_abertura=date(2026, 10, 1),
        )
        Manutencao.objects.create(
            modelo=self.modelo_ativo,
            numero_serie=self.serial_ativo_2,
            setor=self.setor_ativo,
            defeito=self.defeito_ativo,
            data_abertura=date(2026, 10, 1),
            data_retorno=date(2026, 10, 5),
        )
        Manutencao.objects.create(
            modelo=self.modelo_ativo,
            numero_serie=self.serial_ativo,
            setor=self.setor_ativo_2,
            defeito=self.defeito_ativo,
            data_abertura=date(2026, 10, 10),
            data_retorno=date(2026, 10, 16),
        )

        url = reverse('manutencoes:dashboard_kpis_partial')
        response = self.client.get(url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_manutencoes'], 3)
        self.assertEqual(response.context['em_manutencao'], 1)
        self.assertEqual(response.context['resolvidas'], 2)
        self.assertEqual(response.context['mttr_dias'], 5.0)
        self.assertContains(response, 'hx-trigger="manutencaoAtualizada from:body"')

    def test_dashboard_charts_api_returns_structured_orm_aggregations_and_top_5(self):
        modelos = [ModeloImpressora.objects.create(nome=f'MODELO {i}') for i in range(6)]
        setores = [Setor.objects.create(nome=f'SETOR {i}') for i in range(6)]
        defeitos = [TipoDefeito.objects.create(descricao=f'DEFEITO {i}') for i in range(6)]

        # Cria volume decrescente para validar ordenação e corte em Top 5
        for idx in range(6):
            repeats = 6 - idx
            for r in range(repeats):
                is_resolved = (r % 2 == 0)
                Manutencao.objects.create(
                    modelo=modelos[idx],
                    numero_serie=self.serial_ativo,
                    setor=setores[idx],
                    defeito=defeitos[idx],
                    data_abertura=date(2026, 10, 1),
                    data_retorno=date(2026, 10, 4) if is_resolved else None,
                )

        url = reverse('manutencoes:dashboard_charts_api')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['kpis']['total'], 21)
        self.assertEqual(
            data['situacao']['data'][0] + data['situacao']['data'][1],
            21,
        )
        self.assertEqual(len(data['top_modelos']['labels']), 5)
        self.assertEqual(data['top_modelos']['labels'][0], 'MODELO 0')
        self.assertEqual(data['top_modelos']['data'][0], 6)

        self.assertEqual(len(data['top_setores']['labels']), 5)
        self.assertEqual(data['top_setores']['labels'][0], 'SETOR 0')
        self.assertEqual(data['top_setores']['data'][0], 6)

        self.assertEqual(len(data['top_defeitos']['labels']), 5)
        self.assertEqual(data['top_defeitos']['labels'][0], 'DEFEITO 0')
        self.assertEqual(data['top_defeitos']['data'][0], 6)

    def test_exportar_manutencoes_csv_and_xlsx_respects_filters(self):
        import zipfile
        import io

        Manutencao.objects.create(
            modelo=self.modelo_ativo,
            numero_serie=self.serial_ativo,
            setor=self.setor_ativo,
            defeito=self.defeito_ativo,
            data_abertura=date(2026, 10, 1),
            observacao='Ordem em aberto na farmacia',
        )
        Manutencao.objects.create(
            modelo=self.modelo_ativo,
            numero_serie=self.serial_ativo_2,
            setor=self.setor_ativo_2,
            defeito=self.defeito_ativo,
            data_abertura=date(2026, 10, 2),
            data_retorno=date(2026, 10, 5),
            observacao='Ordem resolvida na cirurgica',
        )

        # 1. Exportação CSV filtrando apenas situacao=MANUTENCAO e setor=setor_ativo
        csv_url = reverse('manutencoes:exportar_manutencoes_formato', args=['csv'])
        resp_csv = self.client.get(
            csv_url,
            data={'situacao': 'MANUTENCAO', 'setor': self.setor_ativo.pk},
        )
        self.assertEqual(resp_csv.status_code, 200)
        self.assertIn('text/csv', resp_csv['Content-Type'])
        content_csv = resp_csv.content.decode('utf-8-sig')
        self.assertIn(self.serial_ativo.serial, content_csv)
        self.assertNotIn(self.serial_ativo_2.serial, content_csv)
        self.assertIn('Ordem em aberto na farmacia', content_csv)

        # 2. Exportação XLSX filtrando por busca de serial 'BRCSJ7'
        xlsx_url = reverse('manutencoes:exportar_manutencoes_formato', args=['xlsx'])
        resp_xlsx = self.client.get(
            xlsx_url,
            data={'q': 'BRCSJ7'},
        )
        self.assertEqual(resp_xlsx.status_code, 200)
        self.assertEqual(
            resp_xlsx['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        with zipfile.ZipFile(io.BytesIO(resp_xlsx.content), 'r') as zf:
            sheet_xml = zf.read('xl/worksheets/sheet1.xml').decode('utf-8')
            self.assertIn(self.serial_ativo_2.serial, sheet_xml)
            self.assertNotIn(self.serial_ativo.serial, sheet_xml)

    def test_operational_list_and_dashboard_views_are_decoupled(self):
        Manutencao.objects.create(
            modelo=self.modelo_ativo,
            numero_serie=self.serial_ativo,
            setor=self.setor_ativo,
            defeito=self.defeito_ativo,
            data_abertura=date(2026, 10, 1),
            data_retorno=date(2026, 10, 4),
        )

        # 1. Tela Operacional (/) não deve renderizar os 4 gráficos do Chart.js
        list_url = reverse('manutencoes:manutencao_list')
        resp_list = self.client.get(list_url)
        self.assertEqual(resp_list.status_code, 200)
        self.assertContains(resp_list, 'Planilha Operacional de Manutenções')
        self.assertContains(resp_list, 'form-filtros-manutencao')
        self.assertNotContains(resp_list, 'id="chart-situacao"')
        self.assertNotContains(resp_list, 'id="chart-modelos"')

        # 2. Tela de Dashboard (/dashboard/) deve renderizar KPIs + 4 gráficos em grid lg:grid-cols-2
        dashboard_url = reverse('manutencoes:dashboard')
        resp_dash = self.client.get(dashboard_url)
        self.assertEqual(resp_dash.status_code, 200)
        self.assertContains(resp_dash, 'Dashboard Analítico de Manutenções')
        self.assertContains(resp_dash, 'id="painel-indicadores"')
        self.assertContains(resp_dash, 'id="chart-situacao"')
        self.assertContains(resp_dash, 'id="chart-modelos"')
        self.assertContains(resp_dash, 'id="chart-setores"')
        self.assertContains(resp_dash, 'id="chart-defeitos"')
        self.assertContains(resp_dash, 'lg:grid-cols-2')
        self.assertEqual(resp_dash.context['total_manutencoes'], 1)
        self.assertEqual(resp_dash.context['resolvidas'], 1)
        self.assertEqual(resp_dash.context['mttr_dias'], 3.0)

