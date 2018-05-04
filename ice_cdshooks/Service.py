from flask import json, request
from cdshooks_core import card
from cdshooks_core import link
import pyicefhir
import pyiceclient
import datetime
from Detail import Detail

def service(detail):
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

    source = link('ICE', 'https://cdsframework.atlassian.net/wiki/spaces/ICE')

    card_list = []
    for forecast in forecast_list:
        if forecast[pyiceclient.ICE_FORECASTS_CONCEPT] == "RECOMMENDED" \
                or forecast[pyiceclient.ICE_FORECASTS_CONCEPT] == "FUTURE_RECOMMENDED":
            ice_card = card('ICE Recommendation Card', 'info', source)
            ice_card['detail'] = forecast[pyiceclient.ICE_FORECASTS_GROUP] + ": " \
                + forecast[pyiceclient.ICE_FORECASTS_CONCEPT]
            ice_card['links'].append(
                link('ICE Default Immunization Schedule',
                     'https://cdsframework.atlassian.net/wiki/spaces/ICE/pages/14352468/Default+Immunization+Schedule'))
            ice_card['links'].append(
                link('CDC / ACIP Immunization Schedule', 'https://www.cdc.gov/vaccines/schedules/index.html'))
            ice_card['links'].append(link('ICE Web App', 'https://cds.hln.com/iceweb/#about'))

            card_list.append(ice_card)

    for evaluation in evaluation_list:
        if evaluation[6] == 'VALID':
            indicator = 'info'
        else:
            indicator = 'warning'
        ice_card = card('ICE Evaluation Card', indicator, source)
        ice_card['detail'] = 'Administration Date: ' + evaluation[1] + ' - CVX: ' + evaluation[2] + " - " + evaluation[
            3] + " - evaluation: " + evaluation[6]
        ice_card['links'].append(
            link('ICE Default Immunization Schedule',
                 'https://cdsframework.atlassian.net/wiki/spaces/ICE/pages/14352468/Default+Immunization+Schedule'))
        ice_card['links'].append(
            link('CDC / ACIP Immunization Schedule', 'https://www.cdc.gov/vaccines/schedules/index.html'))
        ice_card['links'].append(link('ICE Web App', 'https://cds.hln.com/iceweb/#about'))

        card_list.append(ice_card)

    # other card types: success, info, warning, hard-stop

    return json.jsonify({
        'cards': card_list
    })
