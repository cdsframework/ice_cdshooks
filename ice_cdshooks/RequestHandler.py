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

SOURCE = Source('ICE', 'https://cdsframework.atlassian.net/wiki/spaces/ICE')
ICE_SCHEDULE_LINK = Link('ICE Default Immunization Schedule',
                         'https://cdsframework.atlassian.net/wiki/spaces/ICE/pages/14352468/Default+Immunization+Schedule',
                         'absolute')
ACIP_SCHEDULE_LINK = Link('CDC / ACIP Immunization Schedule',
                          'https://www.cdc.gov/vaccines/schedules/index.html',
                          'absolute')
ICE_WEBAPP_LINK = Link('ICE Web App', 'https://cds.hln.com/iceweb/#about', 'absolute')


class RequestHandler:
    def __init__(self, detail):
        self.detail = detail
        if not self.detail:
            self.detail = Detail.LOW

    def handle(self):
        fhirdata = request.get_json()
        gender = None
        birthDate = None
        izs = None
        if 'prefetch' in fhirdata and fhirdata['prefetch']:
            gender = fhirdata['prefetch']['patient']['resource']['gender']
            birthDate = fhirdata['prefetch']['patient']['resource']['birthDate']
            if 'immunization' in fhirdata['prefetch'] and 'resource' in fhirdata['prefetch']['immunization'] \
                    and 'entry' in fhirdata['prefetch']['immunization']['resource']:
                izs = fhirdata['prefetch']['immunization']['resource']['entry']

        elif 'fhirServer' in fhirdata and fhirdata['fhirServer'] \
                and 'fhirAuthorization' in fhirdata and fhirdata['fhirAuthorization'] \
                and 'patient' in fhirdata and fhirdata['patient']:
            r = requests.get(fhirdata['fhirServer'] + '/Patient/' + fhirdata['patient'],
                             headers={'Authorization': 'Bearer ' + fhirdata['fhirAuthorization']['access_token']})
            patient = json.loads(r.text)
            gender = patient['gender']
            birthDate = patient['birthDate']

            r = requests.get(fhirdata['fhirServer'] + '/Immunization', params={'patient': fhirdata['patient']},
                             headers={'Authorization': 'Bearer ' + fhirdata['fhirAuthorization']['access_token']})
            immunizations = json.loads(r.text)
            izs = immunizations['entry']
        else:
            raise ValueError('Incomplete patient data.')

        request_vmr = pyicefhir.fhir2vmr(gender, birthDate, izs)
        response_vmr = pyiceclient.send_request(request_vmr, datetime.date.today().strftime('%Y-%m-%d'))
        (evaluation_list, forecast_list) = pyiceclient.process_vmr(response_vmr)

        card_list = []
        for forecast in forecast_list:
            if forecast[pyiceclient.ICE_FORECASTS_CONCEPT] == "RECOMMENDED" \
                    or forecast[pyiceclient.ICE_FORECASTS_CONCEPT] == "FUTURE_RECOMMENDED":
                ice_card = Card('ICE Recommendation Card', 'info', SOURCE, '')
                ice_card.detail += forecast[pyiceclient.ICE_FORECASTS_GROUP] + ": " + forecast[
                    pyiceclient.ICE_FORECASTS_CONCEPT]
                ice_card.add_link(ICE_SCHEDULE_LINK)
                ice_card.add_link(ACIP_SCHEDULE_LINK)
                ice_card.add_link(ICE_WEBAPP_LINK)

                card_list.append(ice_card.get_card())

        for evaluation in evaluation_list:
            if evaluation[6] == 'VALID':
                indicator = 'info'
            else:
                indicator = 'warning'
            ice_card = Card('ICE Evaluation Card', indicator, SOURCE, '')
            ice_card.detail += 'Administration Date: ' + evaluation[1] + ' - CVX: ' + evaluation[2] + " - " + evaluation[
                3] + " - evaluation: " + evaluation[6]
            ice_card.add_link(ICE_SCHEDULE_LINK)
            ice_card.add_link(ACIP_SCHEDULE_LINK)
            ice_card.add_link(ICE_WEBAPP_LINK)

            card_list.append(ice_card.get_card())

        # other card types: success, info, warning, hard-stop

        return json.jsonify({
            'cards': card_list
        })
