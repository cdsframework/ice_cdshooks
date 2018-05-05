# -*- coding: utf-8 -*-

"""FHIR extension to Python ICE client (pyiceclient):

A Python 3 module to convert FHIR data structure to vMR suitable for sending to ICE. 

Could be incorporated into pyiceclient but keeping separate for now.

"""

__author__      = "HLN Consulting, LLC"
__copyright__   = "Copyright 2018, HLN Consulting, LLC"

import pyiceclient
import uuid


def fhir2vmr(gender, birth_date, izs, iz_code_system):
    """Take a FHIR data structure with a patient and immunization resource
    and transform it into a vMR. Return vMR. (Limitation: does not
    include evidence of disease/immunity)

    """

    dob = birth_date.replace('-', '')
    gender = gender[0].upper()
    vmr_body = pyiceclient.VMR_HEADER % (str(uuid.uuid4()), dob, gender)
    rejected_izs = []

    if izs and isinstance(izs, list):
        for iz in izs:
            resource = iz['resource']
            cvx_code = ''
            date_of_admin = ''
            if 'notGiven' in resource:
                if not resource['notGiven']:
                    for code in resource['vaccineCode']['coding']:
                        if code['system'] == iz_code_system:
                            cvx_code = code['code']
                        else:
                            print('mismatched vaccine code system: ' + code['system'])
                    date_of_admin = resource['date'].replace('-','')[0:8]
                else:
                    rejected_izs.append(resource)
                    print('Skipping vaccine as it was not given!')
            else:
                print('Warning - notGiven missing!')
            if len(cvx_code) > 0 and len(date_of_admin) > 0:
                vmr_body += pyiceclient.VMR_IZ % (str(uuid.uuid4()), str(uuid.uuid4()), cvx_code, date_of_admin, date_of_admin)

    vmr_body += pyiceclient.VMR_FOOTER
    return rejected_izs, vmr_body


