#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ice_cdshooks: A Python 3 + Flask implementation of CDS Hooks for
ICE (Immunization Calculation Engine).

Based on example CDS Hooks Service in Python + Flask provided by the
CDS Hooks project at
https://github.com/cds-hooks/cds-service-example-python

Provides a CDS Hook on 'patient-view' that requests prefetched
patient+immunization data from the EHR and then returns cards for each
vaccine group currently recommended.

"""

__author__      = "HLN Consulting, LLC"
__copyright__   = "Copyright 2018, HLN Consulting, LLC"

from flask import Flask, json, request
from flask_cors import CORS
import pyiceclient
import pyicefhir
import datetime

app = Flask(__name__)
cors = CORS(app)

@app.route('/cds-services')
def discovery():
  return json.jsonify({
    'services': [
      {
        'hook': 'patient-view',
        'name': 'Immunization Calculation Engine (ICE) CDS Service',
        'description': 'An Immunization Forecasting CDS service',
        'id': 'ice',
        'prefetch': {
          'patient': 'Patient/{{Patient.id}}',
          'immunization': 'Immunization?patient={{Patient.id}}'
        }
      }
    ]
  })

@app.route('/cds-services/ice', methods=['POST'])
def service():
  fhirdata = request.get_json()
  request_vmr = pyicefhir.fhir2vmr(fhirdata['prefetch'])
  response_vmr = pyiceclient.send_request(request_vmr, datetime.date.today().strftime('%Y-%m-%d'))
  (evaluation_list, forecast_list) = pyiceclient.process_vmr(response_vmr)

  source = link('ICE','https://cdsframework.atlassian.net/wiki/spaces/ICE')

  card_list = []
  for forecast in forecast_list:
    if forecast[pyiceclient.ICE_FORECASTS_CONCEPT] == "RECOMMENDED" or forecast[pyiceclient.ICE_FORECASTS_CONCEPT] == "FUTURE_RECOMMENDED":
      ice_card = card('ICE Card','info', source)
      ice_card['detail'] = forecast[pyiceclient.ICE_FORECASTS_GROUP] + ": " + forecast[pyiceclient.ICE_FORECASTS_CONCEPT]
      ice_card['links'].append(link('ICE Default Immunization Schedule', 'https://cdsframework.atlassian.net/wiki/spaces/ICE/pages/14352468/Default+Immunization+Schedule'))
      ice_card['links'].append(link('CDC / ACIP Immunization Schedule', 'https://www.cdc.gov/vaccines/schedules/index.html'))
      ice_card['links'].append(link('ICE Web App', 'https://cds.hln.com/iceweb/#about'))

      card_list.append(ice_card)
  
  # other card types: success, info, warning, hard-stop

  return json.jsonify({
    'cards': card_list
  })

def card(summary, indicator, source):
  return {
    'summary': summary, 'detail': '', 'indicator': indicator,
    'source': source, 'links': []
  }

def link(label, url=None):
  result = { 'label': label }
  if url:
    result['url'] = url

  return result

if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True)
