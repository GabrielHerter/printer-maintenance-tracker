import json
from django.test import TestCase
from django.urls import reverse

from .forms import (
    ModeloImpressoraForm,
    NumeroSerieForm,
    SetorForm,
    TipoDefeitoForm,
)
from .models import ModeloImpressora, NumeroSerie, Setor, TipoDefeito


class CadastrosFormsAndHTMXViewsTests(TestCase):
    def test_forms_normalize_to_uppercase(self):
        form_modelo = ModeloImpressoraForm(data={'nome': '  hp 401dne  ', 'ativo': True})
        self.assertTrue(form_modelo.is_valid())
        modelo = form_modelo.save()
        self.assertEqual(modelo.nome, 'HP 401DNE')

        form_serial = NumeroSerieForm(data={'serial': ' cnf8g1m854 ', 'ativo': True})
        self.assertTrue(form_serial.is_valid())
        serial = form_serial.save()
        self.assertEqual(serial.serial, 'CNF8G1M854')

        form_setor = SetorForm(data={'nome': 'farmacia interna cmi', 'ativo': True})
        self.assertTrue(form_setor.is_valid())
        setor = form_setor.save()
        self.assertEqual(setor.nome, 'FARMACIA INTERNA CMI')

        form_defeito = TipoDefeitoForm(data={'descricao': 'atolamento na entrada', 'ativo': True})
        self.assertTrue(form_defeito.is_valid())
        defeito = form_defeito.save()
        self.assertEqual(defeito.descricao, 'ATOLAMENTO NA ENTRADA')

    def test_duplicate_validation_in_modal_returns_form_errors(self):
        ModeloImpressora.objects.create(nome='HP 1102W', ativo=True)

        response = self.client.post(
            reverse('cadastros:modelo_create'),
            data={'nome': 'hp 1102w', 'ativo': 'on'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Já existe um Modelo de Impressora cadastrado com este nome.')
        self.assertEqual(ModeloImpressora.objects.count(), 1)

    def test_htmx_create_emits_hx_trigger_and_closes_modal(self):
        response = self.client.post(
            reverse('cadastros:setor_create'),
            data={'nome': 'consultorio de clinica cirurgica', 'ativo': 'on'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Retarget'], '#modal-container')
        self.assertEqual(response['HX-Reswap'], 'innerHTML')

        triggers = json.loads(response['HX-Trigger'])
        self.assertIn('closeModal', triggers)
        self.assertIn('cadastroUpdated', triggers)
        self.assertIn('setorCreated', triggers)
        self.assertEqual(triggers['setorCreated']['label'], 'CONSULTORIO DE CLINICA CIRURGICA')

    def test_htmx_soft_toggle_ativo(self):
        serial = NumeroSerie.objects.create(serial='BRCSJ7BFLN', ativo=True)
        toggle_url = reverse('cadastros:numero_serie_toggle_ativo', args=[serial.pk])

        response = self.client.post(toggle_url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        serial.refresh_from_db()
        self.assertFalse(serial.ativo)
        self.assertContains(response, 'Inativo')

        response = self.client.post(toggle_url, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        serial.refresh_from_db()
        self.assertTrue(serial.ativo)
        self.assertContains(response, 'Ativo')

    def test_select_options_endpoint(self):
        d1 = TipoDefeito.objects.create(descricao='ROLO DO FUSOR', ativo=True)
        TipoDefeito.objects.create(descricao='NAO LIGA', ativo=False)

        response = self.client.get(reverse('cadastros:tipo_defeito_select_options'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'<option value="{d1.pk}" selected>ROLO DO FUSOR</option>')
        self.assertNotContains(response, 'NAO LIGA')
