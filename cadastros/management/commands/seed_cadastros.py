from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from cadastros.models import ModeloImpressora, NumeroSerie, Setor, TipoDefeito

MODELOS: list[str] = [
    'HP 401dne',
    'HP 4103fdw',
    'HP 1536dnf',
    'HP M401dn',
    'HP M401n',
    'HP 402dn',
    'HP 402n',
    'HP 425dn',
    'HP 426dw',
    'HP 426fdw',
    'HP 428fdw',
    'HP 428dw',
    'HP 1102w',
    'HP 402dne',
    'HP 404dw',
    'HP 26nw',
    'HP 402',
    'HP 404',
    'HP 1212nf',
    'HP P1606dn',
    'HP P1006',
    'HP M127FN',
    'HP M1132',
    'HP TESTE',
]

NUMEROS_SERIE: list[str] = [
    'BRBFCBL084',
    'BRBFD1D0WS',
    'BRBFD1Q03L',
    'BRBHB759CV',
    'BRBSBDV7D9',
    'BRBSBDW71P',
    'BRBSC4VOZY',
    'BRBSD5JT3G',
    'BRBSD6NSWR',
    'BRBSF8JBMJ',
    'BRBSG1FGJP',
    'BRBSG4YTJZ',
    'BRBSG6KGYV',
    'BRBSG9BS79',
    'BRBSGUX966',
    'BRBSH2CKM4',
    'BRBSH45KDR',
    'BRBSH7NK8Z',
    'BRBSH7YKHP',
    'BRBSHBTK8H',
    'BRBSJC81DC',
    'BRBSJ6567P',
    'BRBSK2V1BR',
    'BRBSKDG7K8',
    'BRBSL190CD',
    'BRBSL2VCZF',
    'BRBSL8Q2PR',
    'BRBSLCN60Z',
    'BRBSLCP6SQ',
    'BRBSLDD3FR',
    'BRBSLLB35P',
    'BRBSM2Q8BH',
    'BRBSM4J781',
    'BRBSM58111',
    'BRBSM5D1C8',
    'BRBSM5DID0',
    'BRBSM5Z49N',
    'BRBSM7VTDR',
    'BRBSM7XTVH',
    'BRBSM8VVZ20',
    'BRBSMD33KG',
    'BRBSMD54PY',
    'BRBSMD874Z',
    'BRBSMDDFCC',
    'BRBSMDFFLL',
    'BRBSMDFFLT',
    'BRBSMDFFMZ',
    'BRBSMDFFN0',
    'BRBSMDFFN3',
    'BRBSMDFFNT',
    'BRBSMDHFX8',
    'BRBSMDJH1Q',
    'BRBSMDKHQK',
    'BRBSN2C9VK',
    'BRBSN2DBWM',
    'BRBSN2DBWN',
    'BRBSN2DBX8',
    'BRBSN4D5H7',
    'BRBSS5M0DN',
    'BRBSS5M0DW',
    'BRBSS5M0NZ',
    'BRBSS5M0P8',
    'BRBSS5M0PD',
    'BRBSS9B09Z',
    'BRBSS9B0BG',
    'BRBSS9B0BV',
    'BRBSS9B0DG',
    'BRBSS9B0DL',
    'BRBSS9B0DS',
    'BRBSS9B0F9',
    'BRBSS9B0H5',
    'BRBSS9B0J5',
    'BRBSS9B0J6',
    'BRCSF18J0W',
    'BRCSFBNHRW',
    'BRCSJ7BFMC',
    'BRCSN8218Q',
    'BRCSNBHBTB',
    'BRCSNBHC6R',
    'BRCSP5K0HY',
    'BRDSDCY38Q',
    'BRDSF3KG4K',
    'BRDSG85SLZ',
    'BRDSG85SMC',
    'BRDSGD3PT7',
    'BRDSGD4PMM',
    'BRDSH2HCSK',
    'BRDSH65SSH',
    'BRDSQCC007',
    'BRFSG8C015',
    'BRGFC8P0C6',
    'BRGHC2L3F2',
    'BRGSD7R05Z',
    'BRGSD9G5NB',
    'BRGSDBQ034',
    'BRHSDDW005',
    'CNB6D3J0FF',
    'CNB6D5X09H',
    'CNB6D5X09N',
    'CNB6D63006',
    'CNB6D63053',
    'CNB6D63055',
    'CNB6D630B4',
    'CNB6D630BW',
    'CNB6D630BX',
    'CNB6D630BY',
    'CNB9E254YL',
    'CND8FB425F',
    'CNF8GBFCGJ',
    'CNF8GBFCHB',
    'CNF8H2FBB9',
    'CNF8H4RGS1',
    'PHBLL1M6YM',
    'PHBLLBS5ZZ',
    'PHBQD21671',
    'VNB4802567',
    'VND3N44730',
    'CNF8G1M854',
    'BRCSJ7BFLN',
    'BRBSN3JMQZ',
    'BRBSM7VTDW',
    'CNB6D6304W',
    'CNB6D6307N',
    'BRJSG5P67C',
    'BRBSHD41N4',
    'BRBSC5K0KV',
    'BRBSG2R98L',
]

SETORES: list[str] = [
    'Almoxarifado',
    'Administração Lusimar',
    'Ambulatório HC/Atitus',
    'Ambulatório SUS Quartel A',
    'Ambulatório SUS Quartel B',
    'Autorizações',
    'Bloco Sala Enfermeiros',
    'Bloco Farmácia',
    'Bloco C. Enfermeiros',
    'Bloco Recepção',
    'Bloco Recuperação',
    'Bloco Sala 1',
    'Bloco Sala 2',
    'Bloco sala 3',
    'Bloco sala 4',
    'Bloco sala 5',
    'Bloco sala 6',
    'Bloco sala 7',
    'Bloco sala 8',
    'Bloco sala 9',
    'Bloco sala 10',
    'Bloco sala 11',
    'Bloco sala 12',
    'Bloco sala 13',
    'Bloco sala 14',
    'Bloco sala 15',
    'Bloco sala 16',
    'Entrega de Exames',
    'CD2 RECEPCAO',
    'CD2 RAIO X',
    'CD2 TESOURARIA',
    'CD4 RECEPCAO',
    'CENTRAL DE CONSULTAS',
    'CME',
    'FARMACIA INTERNA CMI',
    'HEMODINAMICA COMANDO',
    'CONSULTORIO DE CLINICA CIRURGICA',
    'CONSULTORIO DE CLINICA MEDICA',
    'CONSULTORIO DE TRAUMA',
    'CONSULTORIO MULTI',
    'CONSULTORIO PEDIATRIA',
    'Central Consultas Guiches',
    'Central Consultas Tesouraria',
    'Central de Contas',
    'Centro De Pesquisa Clinica',
    'Centro Logistico Farmacotecnica',
    'Contabilidade',
    'Coreme',
    'Departamento Pessoal',
    'Emergencia',
    'Emergencia Pediatrica',
    'Engenharia Clinica',
    'Ensino e Pesquisa',
    'Farmacia da Onco',
    'Faturamento',
    'Faturamento Hemodinamica',
    'Financeiro',
    'Fisioterapia',
    'HC Clinicas Ortopedia',
    'HC Clinicas Recepção',
    'Hemodinamica Recuperacao',
    'HPBM',
    'HPBM POSTO 01',
    'INTERNACOES',
    'Internações Select',
    'Laboratorio Particular',
    'Laboratorio de Analises',
    'Lab HC SUS Quartel',
    'Laboratório Bella Citta',
    'Manutenção',
    'Nutrição',
    'Oncologia Recepcao',
    'OrtoHC',
    'Obras',
    'P.S Recepcao',
    'PA PEDIATRIA',
    'PA CONSULTORIO',
    'PEDIÁTRIA POSTO 54',
    'PESQUISA CLINICA',
    'POSTO 01',
    'POSTO 02',
    'POSTO 03',
    'POSTO 04',
    'POSTO 05',
    'POSTO 07',
    'POSTO 08 SELECT',
    'POSTO 08',
    'POSTO 09',
    'POSTO 09 SELECT',
    'POSTO 64',
    'POSTO 74',
    'POSTO 75',
    'POSTO EMERGÊNCIA SECRETARIA',
    'PRESCRIÇÃO MEDICA',
    'PRONTO ATENDIMENTO',
    'Psicologia Clinica',
    'Posto 34',
    'Psicologia Hospitalar',
    'RADIOTERAPIA',
    'RECEPÇÃO SER MULHER',
    'RECUPERACAO BLOCO',
    'RECUPERAÇÃO SUS',
    'RESSONÂNCIA COMANDO',
    'RESSONÂNCIA RECUPERACAO 3',
    'SALA DE CLASSIFICAÇÃO DE RISCO',
    'SALA VERMELHA EMERGENCIA',
    'SAME (CENTRO LOGÍSTICO)',
    'SCIH NIR',
    'SESMT',
    'SR3 Select',
    'Serviço Social',
    'Sondário',
    'Suporte STI',
    'Terapia Ocupacional',
    'Transporte (Aricris)',
    'UCR',
    'UDT',
    'UDTA',
    'UTI ADULTO',
    'UTI NEO',
    'UTI PEDIATRICA',
    'UTI SELECT',
    'UTI-A',
    'UTI-NEO',
    'Unidade Transfusional',
]

TIPOS_DEFEITO: list[str] = [
    'ADF',
    'AMASSANDO FOLHA',
    'ATOLAMENTO SAIDA',
    'ATOLAMENTO FUSOR',
    'ATOLAMENTO DEPOIS DO TONNER',
    'ATOLAMENTO NA ENTRADA',
    'NAO PUXA B1',
    'BARULHO ALTO',
    'BORRACHA GASTA',
    'BOTÃO NÃO FUNCIONA',
    'NAO PUXA B2',
    'DISPLAY NÃO FUNCIONA',
    'ERRO 49',
    'ERRO FUSOR',
    'ERRO SCANNER 13',
    'ESTEIRA DO SCANNER',
    'FRENTE E VERSO',
    'ROLO DO FUSOR',
    'IMPRIME TORTO',
    'LIMPEZA',
    'MANCHANDO',
    'TONNER PRESO',
    'NAO ENCAIXA O TONNER',
    'NAO LIGA',
    'PELICULA MANCHANDO FOLHA',
    'PLACA DE REDE',
    'PLACA USB',
    'RASGANDO PAPEL',
    'SENSOR PAPEL',
    'FALHA RENCIDENCIA',
]


class Command(BaseCommand):
    help = 'Popula de forma idempotente os cadastros mestres (Modelos, Números de Série, Setores e Tipos de Defeito).'

    def _seed_model(
        self,
        model_class: Any,
        field_name: str,
        items: list[str],
    ) -> tuple[int, int]:
        criados = 0
        existentes = 0

        for raw_item in items:
            valor = raw_item.strip()
            if not valor:
                continue

            # Verificação case-insensitive antes de get_or_create para evitar conflitos de caixa
            lookup_iexact = {f'{field_name}__iexact': valor}
            obj = model_class.objects.filter(**lookup_iexact).first()

            if obj is not None:
                if not obj.ativo:
                    obj.ativo = True
                    obj.save(update_fields=['ativo'])
                existentes += 1
            else:
                _, created = model_class.objects.get_or_create(
                    **{field_name: valor},
                    defaults={'ativo': True},
                )
                if created:
                    criados += 1
                else:
                    existentes += 1

        return criados, existentes

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(
            self.style.MIGRATE_HEADING('Iniciando carga de cadastros mestres...')
        )

        with transaction.atomic():
            modelos_criados, modelos_existentes = self._seed_model(
                ModeloImpressora, 'nome', MODELOS
            )
            seriais_criados, seriais_existentes = self._seed_model(
                NumeroSerie, 'serial', NUMEROS_SERIE
            )
            setores_criados, setores_existentes = self._seed_model(
                Setor, 'nome', SETORES
            )
            defeitos_criados, defeitos_existentes = self._seed_model(
                TipoDefeito, 'descricao', TIPOS_DEFEITO
            )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS('=== RESUMO DA IMPORTAÇÃO DE CADASTROS MESTRES ===')
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'• Modelos de Impressora (Total: {len(MODELOS)}): '
                f'{modelos_criados} novos criados | {modelos_existentes} já existiam'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'• Números de Série      (Total: {len(NUMEROS_SERIE)}): '
                f'{seriais_criados} novos criados | {seriais_existentes} já existiam'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'• Setores               (Total: {len(SETORES)}): '
                f'{setores_criados} novos criados | {setores_existentes} já existiam'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'• Tipos de Defeito      (Total: {len(TIPOS_DEFEITO)}): '
                f'{defeitos_criados} novos criados | {defeitos_existentes} já existiam'
            )
        )
        self.stdout.write(
            self.style.SUCCESS('=================================================')
        )

