# -*- coding: utf-8 -*-

__author__ = "HLN Consulting, LLC"
__copyright__ = "Copyright 2018, HLN Consulting, LLC"

from flask import json, request
from cdshooks_core import Card
from cdshooks_core import Link
from cdshooks_core import Source
from ice_cdshooks import pyicefhir
import pyiceclient
import datetime
from ice_cdshooks.Detail import Detail
import requests

SOURCE = Source('ICE', 'https://cdsframework.atlassian.net/wiki/spaces/ICE')
ICE_SCHEDULE_LINK = Link('ICE Default Immunization Schedule',
                         'https://cdsframework.atlassian.net/wiki/spaces/ICE/pages/14352468/Default+Immunization+Schedule',
                         'absolute')
ACIP_SCHEDULE_LINK = Link('CDC / ACIP Immunization Schedule',
                          'https://www.cdc.gov/vaccines/schedules/index.html',
                          'absolute')
ICE_WEBAPP_LINK = Link('ICE SMART App', 'http://cds.hln.com/smart-ice-client/launch.html', 'smart')


class RequestHandler:
    def __init__(self, detail, iz_code_system, ice_service_endpoint):
        self.detail = detail
        self.iz_code_system = iz_code_system
        self.ice_service_endpoint = ice_service_endpoint
        if not self.detail:
            self.detail = Detail.LOW

    def handle(self):
        fhirdata = request.get_json()
        print('fhirdata=' + str(fhirdata))
        gender = None
        birth_date = None
        izs = None
        if 'prefetch' in fhirdata \
                and fhirdata['prefetch'] \
                and 'patient' in fhirdata['prefetch'] \
                and 'gender' in fhirdata['prefetch']['patient'] \
                and 'birthDate' in fhirdata['prefetch']['patient']:
            gender = fhirdata['prefetch']['patient']['gender']
            birth_date = fhirdata['prefetch']['patient']['birthDate']
            if 'immunization' in fhirdata['prefetch'] \
                    and 'entry' in fhirdata['prefetch']['immunization']:
                izs = fhirdata['prefetch']['immunization']['entry']
            # print('prefetch izs=' + str(izs))

        elif 'fhirServer' in fhirdata and fhirdata['fhirServer'] and (
                ('patient' in fhirdata and fhirdata['patient']) or (
                'context' in fhirdata and fhirdata and 'patientId' in fhirdata['context']
                and fhirdata['context']['patientId'])):

            if 'patient' in fhirdata:
                patient_id = fhirdata['patient']
            else:
                patient_id = fhirdata['context']['patientId']

            if 'fhirAuthorization' in fhirdata and fhirdata['fhirAuthorization']:
                r = requests.get(fhirdata['fhirServer'] + '/Patient/' + patient_id,
                                 headers={'Authorization': 'Bearer ' + fhirdata['fhirAuthorization']['access_token'],
                                          'Accept': 'application/json'})
            else:
                r = requests.get(fhirdata['fhirServer'] + '/Patient/' + patient_id,
                                 headers={'Accept': 'application/json'})

            print(fhirdata['fhirServer'] + '/Patient/' + patient_id + '   r.text=' + str(r.text))
            patient = json.loads(r.text)
            gender = patient['gender']
            birth_date = patient['birthDate']

            if 'fhirAuthorization' in fhirdata and fhirdata['fhirAuthorization']:
                r = requests.get(fhirdata['fhirServer'] + '/Immunization', params={'patient': patient_id},
                                 headers={'Authorization': 'Bearer ' + fhirdata['fhirAuthorization']['access_token'],
                                          'Accept': 'application/json'})
            else:
                r = requests.get(fhirdata['fhirServer'] + '/Immunization', params={'patient': patient_id},
                                 headers={'Accept': 'application/json'})

            print(fhirdata['fhirServer'] + '/Immunization?patient=' + patient_id + ' r.text=' + str(r.text))
            print('r.status_code=' + str(r.status_code))

            try:
                if r.status_code == '404':
                    izs = list()
                else:
                    immunizations = json.loads(r.text)
                    if 'entry' in immunizations:
                        izs = immunizations['entry']
                    else:
                        izs = list()
            except:
                izs = list()
            # print('fetched izs=' + str(izs))
        else:
            raise ValueError('Incomplete patient data.')

        (rejected_izs, request_vmr) = pyicefhir.fhir2vmr(gender, birth_date, izs, self.iz_code_system)
        response_vmr = pyiceclient.send_request(request_vmr, self.ice_service_endpoint,
                                                datetime.date.today().strftime('%Y-%m-%d'))
        (evaluation_list, forecast_list) = pyiceclient.process_vmr(response_vmr)

        if self.detail == Detail.HIGH:
            return self.get_high_detail(rejected_izs, evaluation_list, forecast_list)
        elif self.detail == Detail.LOW:
            return self.get_low_detail(rejected_izs, evaluation_list, forecast_list)

    def get_high_detail(self, rejected_izs, evaluation_list, forecast_list):
        card_list = []
        for forecast in forecast_list:
            ice_card = Card('ICE Recommendation Card', 'info', SOURCE, '')
            if forecast[pyiceclient.ICE_FORECASTS_CONCEPT] == 'RECOMMENDED':
                ice_card.detail += 'Recommended: **%s**\r\n' % (forecast[pyiceclient.ICE_FORECASTS_GROUP],)
                ice_card.detail += '* Due date: Now\r\n'
            elif forecast[pyiceclient.ICE_FORECASTS_CONCEPT] == 'FUTURE_RECOMMENDED':
                ice_card.detail += 'Future recommended: **%s**\r\n' % (forecast[pyiceclient.ICE_FORECASTS_GROUP],)
                ice_card.detail += '* Due date: %s\r\n' % (format_date(forecast[pyiceclient.ICE_FORECASTS_DUE_DATE]),)
            elif forecast[pyiceclient.ICE_FORECASTS_CONCEPT] == 'CONDITIONAL':
                ice_card.detail += 'Conditionally recommended: **%s**\r\n' % (
                    forecast[pyiceclient.ICE_FORECASTS_GROUP],)
                ice_card.detail += '* Conditional reason: %s\r\n' % (forecast[pyiceclient.ICE_FORECASTS_INTERP],)
            elif forecast[pyiceclient.ICE_FORECASTS_CONCEPT] == 'NOT_RECOMMENDED':
                ice_card.detail += 'Not recommended: **%s**\r\n' % (forecast[pyiceclient.ICE_FORECASTS_GROUP],)
                ice_card.detail += '* Not recommended reason: %s\r\n' % (forecast[pyiceclient.ICE_FORECASTS_INTERP],)

            if forecast[pyiceclient.ICE_FORECASTS_VAC_CODE]:
                ice_card.detail += '* CVX specific code: %s\r\n' % (forecast[pyiceclient.ICE_FORECASTS_VAC_CODE],)

            if forecast[pyiceclient.ICE_FORECASTS_EARLIEST_DATE]:
                ice_card.detail += '* Earliest due date: %s\r\n' % (
                    format_date(forecast[pyiceclient.ICE_FORECASTS_EARLIEST_DATE]),)

            if forecast[pyiceclient.ICE_FORECASTS_PAST_DUE_DATE]:
                ice_card.detail += '* Past due date: %s\r\n' % (
                    format_date(forecast[pyiceclient.ICE_FORECASTS_PAST_DUE_DATE]),)

            ice_card.add_link(ICE_SCHEDULE_LINK)
            ice_card.add_link(ACIP_SCHEDULE_LINK)
            ice_card.add_link(ICE_WEBAPP_LINK)

            card_list.append(ice_card.get_card())

        for evaluation in evaluation_list:
            if evaluation[pyiceclient.ICE_EVALS_EVAL_CODE] == 'VALID':
                indicator = 'info'
            else:
                indicator = 'warning'
            ice_card = Card('ICE Substance Administration Evaluation Card', indicator, SOURCE, '')
            ice_card.detail += 'Substance administration evaluation:\r\n'
            ice_card.detail += '* Evaluation code: %s\r\n' % (evaluation[pyiceclient.ICE_EVALS_EVAL_CODE],)
            ice_card.detail += '* Administration date: %s\r\n' % (
                format_date(evaluation[pyiceclient.ICE_EVALS_DATE_OF_ADMIN]),)
            ice_card.detail += '* Substance administration group: %s\r\n' % (evaluation[pyiceclient.ICE_EVALS_GROUP],)
            ice_card.detail += '* Substance administration code: %s\r\n' % (evaluation[pyiceclient.ICE_EVALS_VACCINE],)
            ice_card.detail += '* Shot # %s\r\n' % (evaluation[pyiceclient.ICE_EVALS_DOSE_NUM],)
            if forecast[pyiceclient.ICE_EVALS_EVAL_INTERP]:
                ice_card.detail += '* Reason code: %s\r\n' % (evaluation[pyiceclient.ICE_EVALS_EVAL_INTERP],)

            ice_card.add_link(ICE_SCHEDULE_LINK)
            ice_card.add_link(ACIP_SCHEDULE_LINK)
            ice_card.add_link(ICE_WEBAPP_LINK)

            card_list.append(ice_card.get_card())

        for rejected_iz in rejected_izs:
            ice_card = Card('ICE Substance Administration Evaluation Skipped Card', indicator, SOURCE, '')
            ice_card.detail += 'Substance administration not given:\r\n'
            ice_card.detail += '* Evaluation code: %s - %s\r\n' % \
                               (rejected_iz['vaccineCode']['coding'][0]['code'],
                                rejected_iz['vaccineCode']['coding'][0]['display'])
            ice_card.detail += '* Administration date: %s\r\n' % (rejected_iz['date'][:10],)

            ice_card.add_link(ICE_SCHEDULE_LINK)
            ice_card.add_link(ACIP_SCHEDULE_LINK)
            ice_card.add_link(ICE_WEBAPP_LINK)

            card_list.append(ice_card.get_card())

        return json.jsonify({
            'cards': card_list
        })

    def get_low_detail(self, rejected_izs, evaluation_list, forecast_list):
        card_list = []

        rec_card = Card('ICE Recommendation Card', 'info', SOURCE, '')
        rec_card.add_link(ICE_SCHEDULE_LINK)
        rec_card.add_link(ACIP_SCHEDULE_LINK)
        rec_card.add_link(ICE_WEBAPP_LINK)

        for forecast in forecast_list:
            if forecast[pyiceclient.ICE_FORECASTS_CONCEPT] == 'RECOMMENDED':
                rec_card.detail += 'Recommended: **%s**\r\n' % (forecast[pyiceclient.ICE_FORECASTS_GROUP],)
                rec_card.detail += '* Due date: Now\r\n'
            elif forecast[pyiceclient.ICE_FORECASTS_CONCEPT] == 'FUTURE_RECOMMENDED':
                rec_card.detail += 'Future recommended: **%s**\r\n' % (forecast[pyiceclient.ICE_FORECASTS_GROUP],)
                rec_card.detail += '* Due date: %s\r\n' % (format_date(forecast[pyiceclient.ICE_FORECASTS_DUE_DATE]),)
            elif forecast[pyiceclient.ICE_FORECASTS_CONCEPT] == 'CONDITIONAL':
                rec_card.detail += 'Conditionally recommended: **%s**\r\n' % (
                    forecast[pyiceclient.ICE_FORECASTS_GROUP],)
                rec_card.detail += '* Conditional reason: %s\r\n' % (forecast[pyiceclient.ICE_FORECASTS_INTERP],)
            elif forecast[pyiceclient.ICE_FORECASTS_CONCEPT] == 'NOT_RECOMMENDED':
                rec_card.detail += 'Not recommended: **%s**\r\n' % (forecast[pyiceclient.ICE_FORECASTS_GROUP],)
                rec_card.detail += '* Not recommended reason: %s\r\n' % (forecast[pyiceclient.ICE_FORECASTS_INTERP],)

            if forecast[pyiceclient.ICE_FORECASTS_VAC_CODE]:
                rec_card.detail += '* CVX specific code: %s\r\n' % (forecast[pyiceclient.ICE_FORECASTS_VAC_CODE],)

            if forecast[pyiceclient.ICE_FORECASTS_EARLIEST_DATE]:
                rec_card.detail += '* Earliest due date: %s\r\n' % (
                    format_date(forecast[pyiceclient.ICE_FORECASTS_EARLIEST_DATE]),)

            if forecast[pyiceclient.ICE_FORECASTS_PAST_DUE_DATE]:
                rec_card.detail += '* Past due date: %s\r\n' % (
                    format_date(forecast[pyiceclient.ICE_FORECASTS_PAST_DUE_DATE]),)
            rec_card.detail += '\r\n'

        card_list.append(rec_card.get_card())

        if evaluation_list:
            eval_card = Card('ICE Substance Administration Evaluation Card', 'info', SOURCE, '')
            eval_card.add_link(ICE_SCHEDULE_LINK)
            eval_card.add_link(ACIP_SCHEDULE_LINK)
            eval_card.add_link(ICE_WEBAPP_LINK)

            for evaluation in evaluation_list:
                eval_card.detail += 'Substance administration evaluation:\r\n'
                eval_card.detail += '* Evaluation code: %s\r\n' % (evaluation[pyiceclient.ICE_EVALS_EVAL_CODE],)
                eval_card.detail += '* Administration date: %s\r\n' % (
                    format_date(evaluation[pyiceclient.ICE_EVALS_DATE_OF_ADMIN]),)
                eval_card.detail += '* Substance administration group: %s\r\n' % (
                    evaluation[pyiceclient.ICE_EVALS_GROUP],)
                eval_card.detail += '* Substance administration code: %s\r\n' % (
                    evaluation[pyiceclient.ICE_EVALS_VACCINE],)
                eval_card.detail += '* Shot # %s\r\n' % (evaluation[pyiceclient.ICE_EVALS_DOSE_NUM],)
                if forecast[pyiceclient.ICE_EVALS_EVAL_INTERP]:
                    eval_card.detail += '* Reason code: %s\r\n' % (evaluation[pyiceclient.ICE_EVALS_EVAL_INTERP],)
                eval_card.detail += '\r\n'

            card_list.append(eval_card.get_card())

        if rejected_izs:
            skip_card = Card('ICE Substance Administration Evaluation Skipped Card', 'warning', SOURCE, '')
            skip_card.add_link(ICE_SCHEDULE_LINK)
            skip_card.add_link(ACIP_SCHEDULE_LINK)
            skip_card.add_link(ICE_WEBAPP_LINK)

            for rejected_iz in rejected_izs:
                skip_card.detail += 'Substance administration reported but not given:\r\n'
                skip_card.detail += '* Evaluation code: %s - %s\r\n' % \
                                    (rejected_iz['vaccineCode']['coding'][0]['code'],
                                     rejected_iz['vaccineCode']['coding'][0]['display'])
                skip_card.detail += '* Administration date: %s\r\n' % (rejected_iz['date'][:10],)
                skip_card.detail += '\r\n'

            card_list.append(skip_card.get_card())

        return json.jsonify({
            'cards': card_list
        })


def format_date(date):
    return '%s-%s-%s' % (date[:4], date[4:6], date[6:])
