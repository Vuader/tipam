================================
Tachyonic Project's IPAM (TIPAM)
================================

TIPAM is a very fast RESTFul IPv4/IPv6 Address management Tool.


Required Python Packages:
=========================

* luxon
* pyipcalc


Installation
============

..code:: bash

    $ pip3 install tipam


Setup
=====

..code:: bash

    $ mkdir tipam
    $ luxon -i tipam tipam
    $ luxon -d tipam

Then serve with Apache2, nginx, `luxon -s`, or your favourite WSGI compliant server.


Terminology and Usage
=====================

With regards to creation, you can do the following to/with prefixes in the IPAM:

* Add Prefixes
* Allocate Prefixes
* Find Prefixes

As a first step, you have to *Add* a prefix. You can't *allocate* or *find* prefixes before you have *add*ed a prefix.

..code:: bash

    $ curl -X POST \
      http://$TIPAM_URL/v1/prefix \
      -H 'Content-Type: application/json' \
      -d '{
        "prefix": "192.0.2.0/24",
        "name": "My First IP block"
        }'


Adding a prefix, creates the prefix in the IPAM, and always makes it available by setting `free=True`.

Now that a prefix has been added to the IPAM, you can *allocate* a prefix from it:

..code:: bash

    $ curl -X POST \
      http://$TIPAM_URL/v1/allocate \
      -H 'Content-Type: application/json' \
      -d '{
	    "prefix": "192.0.2.0/30",
	    "name": "Customer 1"
        }'

Allocating a prefix set's `free=False`, which means no more prefixes can be added/allocated from the allcoated prefix.

You can associate tags with prefixes:

..code:: bash

    $ curl -X POST \
      http://$TIPAM_URL/v1/tag \
      -H 'Content-Type: application/json' \
      -d '{
        "prefix": "58e27f46-7376-4147-a7d0-a31c05fe2b34",
        "tag": "doc_example"
        }'

You can use *find* to search for, and allocate the first available prefix of a specific length. The tag is used to
indicate from which range to allocate:


..code:: bash


    $ curl -X POST \
      http://localhost:8005/v1/find \
      -H 'Content-Type: application/json' \
      -d '{
        "prefix_len": 29,
        "name": "Customer 2",
        "tag": "doc_example"
        }'
