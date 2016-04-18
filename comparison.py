#!/usr/bin/env python
"""
Compare query performance for adjacency-list vs. materialized path querying
of arbitrarily-deep nested items in MySQL.

Adjacency list is the simplest, most naive way of representing tree data in
SQL. Each child carries a reference to its parent. This necessitates
recursive queries when you want to get a whole subtree.

Materialized path is an approach that involves concatenating references
into a delimited string. This is useful for certain types of query, such
as an ancestors for a leaf -- the path contains all the information you
need. Subtree queries use a wildcard search, which is able to leverage
the index.
"""

import MySQLdb
import string
import time

BASE36_CHARS = string.digits + string.uppercase


class Timer(object):
    def __enter__(self):
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.interval = self.end - self.start
        print "timed at %s" % self.interval


def base36encode(number):
    """Converts an integer to a base36 string."""
    base36 = ''
    sign = ''

    if number < 0:
        sign = '-'
        number = -number

    if 0 <= number < len(BASE36_CHARS):
        return sign + BASE36_CHARS[number]

    while number != 0:
        number, i = divmod(number, len(BASE36_CHARS))
        base36 = BASE36_CHARS[i] + base36

    return sign + base36


def base36decode(number):
    return int(number, 36)


def clear_db(c):
    c.execute('''DELETE FROM nested_a''')
    c.execute('''DELETE FROM nested_b''')


def insert_adjacent(c, item_id, parent_id):
    c.execute('''
INSERT INTO nested_a (id, foo, parent_id)
values (%s, "blah", %s)
    ''', (item_id, parent_id))


def generate_adjacent(c, number, children=5, grandchildren=2):
    for i in range(1, number):
        insert_adjacent(c, i, None)
        for j in range(children):
            j_id = i * (number + 1) + j
            insert_adjacent(c, j_id, i)
            for k in range(grandchildren):
                k_id = j_id * (number + 1) + k
                insert_adjacent(c, k_id, j_id)


def insert_mpath(c, item_id, parent_path):
    c.execute('''
INSERT INTO nested_b (id, foo, path)
values (%s, "blerg", %s)
    ''', (item_id, parent_path))


def generate_mpath(c, number, children=5, grandchildren=2):
    for i in range(1, number):
        i_path = base36encode(i)
        insert_mpath(c, i, i_path)
        for j in range(children):
            j_id = i * (number + 1) + j
            j_path = ".".join([i_path, base36encode(j_id)])
            insert_mpath(c, j_id, j_path)
            for k in range(grandchildren):
                k_id = j_id * (number + 1) + k
                k_path = ".".join([j_path, base36encode(j_id)])
                insert_mpath(c, k_id, k_path)


def query_a(c, top_level_ids):
    """
    Just a naive get by id/parent_id with application side recursion.

    You can also do self-join in sql with a maximum depth. Some other
    databases support recursive queries but not mysql.
    """
    c.execute('''
    SELECT * FROM nested_a WHERE id IN %s;
    ''', (top_level_ids, ))
    acc = c.fetchall()

    def _inner(c, acc, new_ids):
        c.execute('''
select * from nested_a where parent_id in %s;
        ''', (new_ids, ))
        got = c.fetchall()
        new_ids = [i[0] for i in got]
        if not got:
            return acc
        return _inner(c, list(acc) + list(got), new_ids)

    return _inner(c, acc, top_level_ids)


def query_b(c, top_level_ids):
    """

    """
    top_level_paths = [base36encode(top_id) + "%" for top_id in top_level_ids]
    ors = " OR ".join(['path LIKE "%s"' % path for path in top_level_paths])
    sql = "SELECT * FROM nested_b WHERE %s;" % ors
    c.execute(sql)
    return c.fetchall()


def run_comparison(c,
                   db,
                   top_level_items=1000,
                   children=5,
                   grandchildren=2):
    print "inserting %s into adjacency list" % top_level_items
    with Timer():
        generate_adjacent(c,
                          1000,
                          children=children,
                          grandchildren=grandchildren)
        db.commit()

    print "inserting %s into materialized path" % top_level_items
    with Timer():
        generate_mpath(c,
                       1000,
                       children=children,
                       grandchildren=grandchildren)
        db.commit()

    for per_request in [1, 3, 5, 13]:
        print "comparing for %s items" % per_request
        top_level_ids = [i for i in range(per_request)]
        with Timer():
            for i in range(1000):
                query_a(c, top_level_ids)

        with Timer():
            for i in range(1000):
                query_b(c, top_level_ids)


if __name__ == "__main__":

    db = MySQLdb.connect(db="nested_tmp")
    c = db.cursor()
    run_comparison(c,
                   db,
                   top_level_items=1000000,
                   children=4,
                   grandchildren=2)

    clear_db(c)
    db.commit()
