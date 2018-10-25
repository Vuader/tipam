# -*- coding: utf-8 -*-
# Copyright (c) 2018 Christiaan Frans Rademan.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holders nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.

from luxon import register
from luxon import router
from luxon import db

from luxon.exceptions import HTTPNotFound, FieldMissing, ValidationError

from pyipcalc import (int_to_ip,
                      int_32_to_128,
                      IPNetwork)

from psychokinetic.utils.api import sql_list, obj

from tipam import IPAM
from tipam.models.ipam import tipam_prefix_tag

ipam = IPAM()


def format_prefix(prefix):
    pf = prefix
    if prefix['version'] == 4:
        pf['prefix'] = int_to_ip(prefix['a4'])
    else:
        ipdec = int_32_to_128(prefix['a1'],
                              prefix['a2'],
                              prefix['a3'],
                              prefix['a4'], )
        pf['prefix'] = int_to_ip(ipdec, 6)
    for p in ('a1', 'a2', 'a3', 'a4'):
        del pf[p]
    return pf


@register.resources()
class IPam:
    def __init__(self):
        router.add('GET', '/v1/prefixes/{version}',
                   self.list_prefixes,
                   tag='infrastructure:view')

        router.add('GET', '/v1/prefix/{pid}',
                   self.view_prefix,
                   tag='infrastructure:view')

        router.add('POST', '/v1/prefix',
                   self.add_prefix,
                   tag='infrastructure:admin')

        router.add(['PUT', 'PATCH'], '/v1/prefix/{pid}',
                   self.update_prefix,
                   tag='infrastructure:admin')

        router.add('DELETE', '/v1/prefix/{pid}',
                   self.delete_prefix,
                   tag='infrastructure:admin')

    def list_prefixes(self, req, resp, version):

        prefixes = []

        with db() as conn:
            crsr = conn.execute("SELECT * FROM tipam_prefix WHERE "
                                "prefix_type != 'hidden' AND VERSION=?",
                                version)
            results = crsr.fetchall()

        for pf in results:
            prefixes.append(format_prefix(pf))

        return prefixes

    def add_prefix(self, req, resp):

        fields = ('name', 'prefix', 'prefix_type', 'rib', 'description')
        prefix = {i: req.json.get(i) for i in fields if i in req.json}

        if 'prefix_type' in prefix and prefix['prefix_type'] == "hidden":
            raise ValidationError("'hidden' is a reserved prefix_type")

        return format_prefix(ipam.add_prefix(**prefix).dict)

    def view_prefix(self, req, resp, pid):

        with db() as conn:
            crsr = conn.execute("SELECT * FROM tipam_prefix"
                                " WHERE id=?", pid)
            result = crsr.fetchone()

        if not result:
            raise HTTPNotFound("Prefix with id '%s' not found" % pid)

        return format_prefix(result)

    def update_prefix(self, req, resp, pid):

        with db() as conn:
            crsr = conn.execute("SELECT * FROM tipam_prefix"
                                " WHERE id=?", pid)
            result = crsr.fetchone()

        if not result:
            raise HTTPNotFound("Prefix with id '%s' not found" % pid)

        fprefix = format_prefix(result)
        fields = ('name', 'prefix_type', 'description')
        prefix = {i: req.json.get(i) for i in fields if i in req.json}
        prefix['prefix'] = '%s/%s' % (
        fprefix['prefix'], fprefix['prefix_len'],)

        if 'prefix_type' in prefix and prefix['prefix_type'] == "hidden":
            raise ValidationError("'hidden' is a reserved prefix_type")

        return format_prefix(ipam.add_prefix(**prefix).dict)

    def delete_prefix(self, req, resp, pid):

        pf = self.view_prefix(req, resp, pid)

        return ipam.delete_prefix('%s/%s' % (pf['prefix'], pf['prefix_len']),
                                  pf['rib'])


@register.resources()
class Find:
    def __init__(self):
        router.add('POST', '/v1/find',
                   self.find,
                   tag='infrastructure:view')

    def find(self, req, resp):

        fields = ('name', 'tag', 'prefix_len')
        try:
            find = {i: req.json[i] for i in fields}
            find['prefix_len'] = req.json['prefix_len']
        except KeyError as e:
            raise FieldMissing(field=e, label="", description=e)

        return format_prefix(ipam.find(**find))


@register.resources()
class Allocate:
    def __init__(self):
        router.add('POST', '/v1/allocate/',
                   self.allocate,
                   tag='infrastructure:view')

        router.add('POST', '/v1/release/',
                   self.release,
                   tag='infrastructure:view')

    def allocate(self, req, resp):
        fields = ('name', 'prefix', 'prefix_type', 'rib', 'description')
        prefix = {i: req.json.get(i) for i in fields if i in req.json}

        return format_prefix(ipam.allocate_prefix(**prefix).dict)

    def release(self, req, resp):
        fields = ('prefix', 'rib')
        prefix = {i: req.json.get(i) for i in fields if i in req.json}

        return ipam.release_prefix(**prefix)


@register.resources()
class Tag:
    def __init__(self):
        router.add('POST', '/v1/tag', self.add_tag,
                   tag='infrastructure:admin')
        router.add('GET', '/v1/tag/{id}', self.view_tag,
                   tag='infrastructure:view')
        router.add('GET', '/v1/tags', self.list_tags,
                   tag='infrastructure:view')
        router.add(['PUT', 'PATCH'], '/v1/tag/{id}', self.update_tag,
                   tag='infrastructure:admin')
        router.add('DELETE', '/v1/tag/{id}', self.delete_tag,
                   tag='infrastructure:admin')

    def add_tag(self, req, resp):
        tag = obj(req, tipam_prefix_tag)
        tag.commit()
        return tag

    def view_tag(self, req, resp, id):
        return obj(req, tipam_prefix_tag, sql_id=id)

    def list_tags(self, req, resp):
        return sql_list(req, 'tipam_prefix_tag', ('id', 'tag', 'prefix'))

    def update_tag(self, req, resp, id):
        tag = obj(req, tipam_prefix_tag, sql_id=id)
        tag.commit()
        return tag

    def delete_tag(self, req, resp, id):
        tag = obj(req, tipam_prefix_tag, sql_id=id)
        tag.commit()
        return tag


@register.resources()
class Query:
    def __init__(self):
        router.add('GET', 'v1/query/{address}/{prefix_len}', self.query,
                   tag='infrastructure:view')

    def query(self, req, resp, address, prefix_len):
        rib = req.query_params.get('rib', 'default')
        prefix = IPNetwork('%s/%s' % (address, prefix_len))
        prefix = ipam.get_prefix(prefix, rib)
        if not prefix:
            raise HTTPNotFound("Prefix '%s/%s' not found in rib '%s'"
                               % (address, prefix_len, rib))
        return format_prefix(prefix.dict)
