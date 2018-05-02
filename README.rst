CDS Hooks Implementation for ICE
================================

A Python 3 + Flask implementation of CDS Hooks for ICE (Immunization
Calculation Engine).

Based on example CDS Hooks Service in Python + Flask provided by the
CDS Hooks project at
https://github.com/cds-hooks/cds-service-example-python

What it does:
-------------

Provides a CDS Hook on 'patient-view' that requests prefetched
patient+immunization data from the EHR and then returns cards for each
vaccine group currently recommended.

For more information on CDS Hooks, see: http://cds-hooks.org/

LICENSE
=======

License TBD.

This software is based on sample code provided by the CDS Hooks
project with the following license:

.. code-block::


    The MIT License
    
    Copyright (c) 2016 Matt Berther, https://matt.berther.io
    
    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


ICE Software
============

This module requiers ICE server software to be accessible via a URL
specified in pyiceclient.SERVER_ENDPOINT.

The ICE server software is open source software with an open source
license available at www.cdsframework.org > ICE > Documentation > Open
Source License.

New ICE releases include schedule updates/new vaccines, new features,
and bug fixes; release notes are available at www.cdsframework.org >
ICE > Release Notes; and the software is available for download at
www.cdsframework.org > ICE > Downloads. 


The ICE Default Immunization Schedule
=====================================

The ICE Default Immunization schedule was developed by a group of
Subject Matter Experts, based on ACIP recommendations and informed by
CDC's Clinical Decision Support for Immunizations (CDSi) - but its
rules do differ in some ways from CDSi, and its output may not always
match what an individual clinician may expect. Users are advised to be
familiar with the rules and decisions documented at
www.cdsframework.org > ICE > Documentation > Default Immunization
Schedule, and, of course, to use their clinical judgement in
interpreting the recommendations.

Limitations
===========

* No support for evidence of immunity/disease


Installation
============

System:
-------

* Install a working Python 3.5+ environment with pip
* Install ICE on the localhost

Python:
-------

* pip install xmltodict
* pip install flask
* pip install flask_cors
* pip install requests

pyiceclient:
------------

* git clone https://bitbucket.org/cdsframework/pyiceclient

This project:
-------------

* Download release and unzip to project directory, or git clone <project url>; cd into project directory
* Copy pyiceclient.py (see above) into project directory
* Modify options in source code as needed
* Run:

.. code-block::

   $ python ice_cdshooks.py


* Invoke the hooks from a CDS Hooks Sandbox Environment (see below)


Using in a CDS Hooks Sandbox Environment
========================================

* Create an account at the HSP Consortium sandbox at https://sandbox.hspconsortium.org and then log in to the sandbox

* In the sandbox, locate at least one patient with immunizations. You can do this by going to "Data Manager" in the sandbox, typing "Immunization" in the FHIR Query textbox and pressing Enter. Then scroll through the JSON results and jot down some of the patient IDs.

* In the sandbox, go to Apps and launch the CDS Hooks Sandbox app; give it the permissions it asks for

* In the CDS Hooks Sandbox app, click on CDS Services in the upper-right, click Add CDS Service, and then enter the discovery URL of the service: http://localhost:5000/cds-services

* In the CDS Hooks Sandbox app, click Change Patient and enter one of the patient IDs you jotted down earlier

* The ICE cards should appear (assuming the patient needs any immunizations)
