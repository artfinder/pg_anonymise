#!/usr/bin/env python
# This assumes an id on each field.
import logging
import random


log = logging.getLogger('anonymize')
common_hash_secret = "%016x" % (random.getrandbits(128))

listify = lambda x: x if isinstance(x, list) else [x]


def get_truncates(config):
    database = config.get('database', {})
    truncates = database.get('truncate', [])
    sql = []
    for truncate in truncates:
        sql.append('TRUNCATE \"%s\" CASCADE' % truncate)
    return sql


def get_deletes(config):
    database = config.get('database', {})
    tables = database.get('tables', {})
    sql = []
    for table, data in tables.iteritems():
        if 'delete' in data:
            fields = []
            for f, v in data['delete'].iteritems():
                fields.append('\"%s\" = "%s"' % (f, v))
            statement = 'DELETE FROM \"%s\" WHERE ' % table + ' AND '.join(fields) + ' CASCADE'
            sql.append(statement)
    return sql


def get_updates(config):
    global common_hash_secret

    database = config.get('database', {})
    tables = database.get('tables', {})
    sql = []
    for table, data in tables.iteritems():
        updates = []
        for operation, details in data.iteritems():
            if operation == 'nullify':
                for field in listify(details):
                    updates.append("\"%s\" = NULL" % field)
            elif operation == 'random_int':
                for field in listify(details):
                    updates.append("\"%s\" = (random()*1000000000)::int" % field)
            elif operation == 'random_ip':
                for field in listify(details):
                    updates.append("\"%s\" = '0.0.0.0'::inet + (random()*1000000000)::int" % field)
            elif operation == 'random_email':
                for field in listify(details):
                    updates.append("\"%s\" = CONCAT(id, '@artfinder.com')"
                                   % field)
            elif operation == 'random_username':
                for field in listify(details):
                    updates.append("\"%s\" = CONCAT('_user_', id)" % field)
            elif operation == 'hash_value':
                for field in listify(details):
                    updates.append("\"%(field)s\" = MD5(CONCAT('{hash}', \"{field}\"))".format(
                        field=field,
                        hash=common_hash_secret
                    ))
            elif operation == 'hash_email':
                for field in listify(details):
                    updates.append(
                        "\"{field}\" = CONCAT("
                        "SUBSTR("
                        "   MD5(LEFT(email, position('@' in {field}) - 1)),"
                        "   0, LENGTH(LEFT(email, position('@' in {field})))"
                        "),"
                        "RIGHT({field}, char_length({field}) - position('@' in {field}) + 1)"
                        ")".format(
                            field=field
                        )
                    )
            elif operation == 'delete':
                continue
            else:
                log.warning('Unknown operation.')
        if updates:
            sql.append('UPDATE \"%s\" SET %s' % (table, ', '.join(updates)))
    return sql


def anonymize(config):
    sql = []
    sql.extend(get_truncates(config))
    sql.extend(get_deletes(config))
    sql.extend(get_updates(config))
    for stmt in sql:
        print stmt + ';'


if __name__ == '__main__':

    import yaml
    import sys

    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        files = ['anonymise.yml']

    for f in files:
        print "--"
        print "-- %s" % f
        print "--"
        print ""
        cfg = yaml.load(open(f), Loader=yaml.FullLoader)
        if 'databases' not in cfg:
            anonymize(cfg)
        else:
            databases = cfg.get('databases')
            for name, sub_cfg in databases.items():
                print "USE \"%s\";" % name
                anonymize({'database': sub_cfg})
