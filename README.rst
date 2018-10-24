================================
Tachyonic Project's IPAM (TIPAM)
================================

TIPAM is a very fast RESTFul IPv4/IPv6 Address Management tool.

It supports IPv4 and IPV6, and can find and allocate prefixes of arbitrary sizes.

Required Python Packages:
=========================

* luxon
* pyipcalc


Installation
============

::

    $ pip3 install tipam


Setup
=====

::

    $ mkdir tipam
    $ luxon -i tipam tipam
    $ luxon -d tipam

Then serve with Apache2, nginx, `luxon -s`, or your favourite WSGI compliant server.


Terminology and Usage
=====================

Creation
--------

With regards to creation, you can do the following to/with prefixes in the IPAM:

* Add Prefixes
* Allocate Prefixes
* Find Prefixes

As a first step, you have to *Add* a prefix. You can't *allocate* or *find* prefixes before you have *add* -ed a prefix::

    $ curl -X POST \
      http://$TIPAM_URL/v1/prefix \
      -H 'Content-Type: application/json' \
      -d '{
        "prefix": "192.0.2.0/24",
        "name": "My First IP block"
       }'


Adding a prefix creates the prefix in the IPAM, and makes it available by setting ``free=True``.

Now that a prefix has been added to the IPAM, you can *allocate* a prefix from it::


    $ curl -X POST \
      http://$TIPAM_URL/v1/allocate \
      -H 'Content-Type: application/json' \
      -d '{
	    "prefix": "192.0.2.0/30",
	    "name": "Customer 1"
       }'

Allocating a prefix sets ``free=False``, which means no more prefixes can be added/allocated from the allocated prefix.

You can associate tags with prefixes::


    $ curl -X POST \
      http://$TIPAM_URL/v1/tag \
      -H 'Content-Type: application/json' \
      -d '{
        "prefix": "58e27f46-7376-4147-a7d0-a31c05fe2b34",
        "tag": "doc_example"
       }'

You can use *find* (``v1/find``) to search for, and allocate the first available/free prefix of a specific length.
The tag is used to indicate from which range to allocate::


    $ curl -X POST \
      http://$TIPAM_URL/v1/find \
      -H 'Content-Type: application/json' \
      -d '{
        "prefix_len": 29,
        "name": "Customer 2",
        "tag": "doc_example"
       }'

If the search was successful, the found prefix is returned, and is also allocated automatically. A tag may reference
multiple prefixes, in such a case all prefixes will be searched, and the first free one of the requested size will
be allocated and returned.

You can add the same prefix in multiple *rib*'s (Routing Information Base)::

    $ curl -X POST \
      http://$TIPAM_URL/v1/prefix \
      -H 'Content-Type: application/json' \
      -d '{
        "prefix": "192.0.2.0/24",
        "name": "SAME prefix, different rib",
        "rib": "other_context"
       }'

When ``rib`` is omitted during prefix creation, prefixes are created in the default rib called "default".
You can't add the same prefix in the same rib:- Adding a prefix that already exists in a rib will result in an update
of the existing prefix.

You can add prefixes underneath prefixes (e.g. 192.0.2.128/25), as well as prefixes over prefixes (e.g. 192.0.0.0/16).
This can be useful for reserving ranges to tag and allocate from.


Reading
-------

To get a list of all created/allocated prefixes, perform a ``GET`` to ``/vi/prefixes/{version}``, where ``version`` is
"4" for IPv4 and "6" for IPv6::

    $ curl http://$TIPAM_URL/v1/prefixes/4

To view the data for a specific prefix, perform a ``GET`` to ``/vi/prefix/{id}``, where ``id`` is the UUID of the
prefix in question::

    $ curl http://$TIPAM_URL/v1/prefix/a7f22bd8-3791-4346-a167-8f329c576e0b

If the ID is not know, you can query the IPAM for the details of a prefix by sending a ``GET`` to
``/v1/query/{ip}/{prefix_len}``, where ``ip`` is the address in question, and ``prefix_len`` the prefix length::

    $ curl http://$TIPAM_URL/v1/query/192.0.2.0/24

By default, the "default" rib will be queried. To query another rib, add the query params ``?rib=XXX``::

    $ curl http://$TIPAM_URL/v1/query/192.0.2.0/24?rib=other_context


Updating
--------

After prefixes have been added or allocated, they can be modified with ``PUT`` or ``PATCH`` methods::


    $ curl -X PUT \
      http://$TIPAM_URL/v1/prefix/a7f22bd8-3791-4346-a167-8f329c576e0b \
      -H 'Content-Type: application/json' \
      -d '{
        "name": "updated_name"
      }'

Note that ``PUT`` on ``/v1/prefix/{id}`` is equavalent to ``POST`` on ``/v1/prefix`` when the values for ``prefix``
and ``rib`` is equal to that of prefix with UUID of ``id``.

Deletion
--------

Allocated prefixes can be un-allocated by ``release`` -ing them::

    $ curl -X POST \
      http://$TIPAM_URL/v1/release \
      -H 'Content-Type: application/json' \
      -d '{
        "prefix": "192.0.2.0/30"
      }'

This will set ``free=True`` again, making it available for allocation again.

To completely remove a prefix from the IPAM, perform a ``DELETE`` method to ``/v1/prefix/{id}``::

    $ curl -X DELETE http://$TIPAM_URL/v1/prefix/a7f22bd8-3791-4346-a167-8f329c576e0b
