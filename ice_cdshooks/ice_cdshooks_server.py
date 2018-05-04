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
from ice_cdshooks.RequestHandler import RequestHandler
from ice_cdshooks.Detail import Detail

app = Flask(__name__)
CORS(app)

# TODO:add diagnostic objects for ICE for immunity determination


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
    print(str(request))
    h = RequestHandler(Detail.LOW)
    return h.handle()


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
