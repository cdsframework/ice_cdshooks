# -*- coding: utf-8 -*-

"""FHIR extension to Python ICE client (pyiceclient):

A Python 3 module to convert FHIR data structure to vMR suitable for sending to ICE. 

Could be incorporated into pyiceclient but keeping separate for now.

"""

__author__      = "HLN Consulting, LLC"
__copyright__   = "Copyright 2018, HLN Consulting, LLC"

import pyiceclient
import uuid

def fhir2vmr(gender, birthDate, izs):
    """Take a FHIR data structure with a patient and immunization resource
    and transform it into a vMR. Return vMR. (Limitation: does not
    include evidence of disease/immunity)

    """

    dob = birthDate.replace('-','')
    gender = gender[0].upper()
    vmr_body = pyiceclient.VMR_HEADER % (str(uuid.uuid4()), dob, gender)

    if izs and isinstance(izs, list):
        for iz in izs:
            resource = iz['resource']
            cvx_code = ''
            date_of_admin = ''
            if 'notGiven' not in resource or resource['notGiven'] == False:
                for code in resource['vaccineCode']['coding']:
                    if code['system'] == 'http://www2a.cdc.gov/vaccines/IIS/IISStandards/vaccines.asp?rpt=cvx':
                        cvx_code = code['code']
                date_of_admin = resource['date'].replace('-','')[0:8]
            if len(cvx_code) > 0 and len(date_of_admin) > 0:
                vmr_body += pyiceclient.VMR_IZ % (str(uuid.uuid4()), str(uuid.uuid4()), cvx_code, date_of_admin, date_of_admin)

    vmr_body += pyiceclient.VMR_FOOTER
    return vmr_body


