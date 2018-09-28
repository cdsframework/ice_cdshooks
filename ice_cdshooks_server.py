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

__author__ = "HLN Consulting, LLC"
__copyright__ = "Copyright 2018, HLN Consulting, LLC"

from flask import Flask, json, request
from flask_cors import CORS
from ice_cdshooks import RequestHandler
from ice_cdshooks import Detail

app = Flask(__name__)
CORS(app)

# TODO:add diagnostic objects for ICE for immunity determination

# IZ_CODE_SYSTEM is the code system identifier to look for in the patient Immunization history
IZ_CODE_SYSTEM = 'http://www2a.cdc.gov/vaccines/IIS/IISStandards/vaccines.asp?rpt=cvx'
# ICE_SERVICE_ENDPOINT is the URL of the ICE evaluate web service - intended to be on the localhost
ICE_SERVICE_ENDPOINT = "https://cds.hln.com/opencds-decision-support-service/evaluate"


@app.route('/cds-services')
def discovery():
    return json.jsonify({
        'services': [
            {
                'hook': 'patient-view',
                'name': 'Immunization Calculation Engine (ICE) CDS Service',
                'description': 'An Immunization Forecasting CDS service: High Detail',
                'id': 'ice-high',
                'prefetch': {
                    'patient': 'Patient/{{context.patientId}}',
                    'immunization': 'Immunization?patient={{context.patientId}}'
                }
            },
            {
                'hook': 'patient-view',
                'name': 'Immunization Calculation Engine (ICE) CDS Service',
                'description': 'An Immunization Forecasting CDS service: Low Detail',
                'id': 'ice-low',
                'prefetch': {
                    'patient': 'Patient/{{context.patientId}}',
                    'immunization': 'Immunization?patient={{context.patientId}}'
                }
            }

        ]
    })


@app.route('/cds-services/ice-high', methods=['POST'])
def high_service():
    h = RequestHandler(Detail.HIGH, IZ_CODE_SYSTEM, ICE_SERVICE_ENDPOINT)
    return h.handle()


@app.route('/cds-services/ice-low', methods=['POST'])
def low_service():
    h = RequestHandler(Detail.LOW, IZ_CODE_SYSTEM, ICE_SERVICE_ENDPOINT)
    return h.handle()


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
