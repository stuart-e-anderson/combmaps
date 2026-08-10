"""
db -- connection + read queries for the browse/filter site.

Read-only. Pure browse-and-select-by-property is the site's minimal
requirement (agreed 2026-08-09) -- no writes, no auth needed here.
"""
import os

import psycopg

D_TYPES = [
    "SPSR", "SPSS", "SISR", "SISS", "CPSR", "CPSS", "CISR", "CISS",  # plane
    "SPSC", "SISC", "CPSC", "CISC",  # SPEC-7: cylinder
    "SPST", "SIST", "CPST", "CIST",  # SPEC-7: torus
]
PAGE_SIZE = 50


def get_conn():
    return psycopg.connect(
        host=os.environ.get("PGHOST", "localhost"),
        dbname=os.environ.get("PGDATABASE", "squaring_net"),
        user=os.environ.get("PGUSER", "squaring_admin"),
        password=os.environ["PGPASSWORD"],
    )


def orders_summary():
    """order_val -> total dissections + degn_count, for the landing page."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT oc.order_val, oc.graph_count, oc.degn_count,
                   coalesce(sum((kv.v)::int), 0) AS dissection_count
            FROM order_counts oc
            LEFT JOIN LATERAL jsonb_each_text(oc.d_type_counts) AS kv(k, v) ON true
            GROUP BY oc.order_val, oc.graph_count, oc.degn_count
            ORDER BY oc.order_val
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def dissections_for_order(order_val, d_type=None, page=1):
    """Paged list of dissections for one order, optionally filtered by d_type."""
    offset = (page - 1) * PAGE_SIZE
    where = "WHERE order_val = %s"
    params = [order_val]
    if d_type:
        where += " AND d_type = %s"
        params.append(d_type)

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(f"""
            SELECT dissection_id, d_type, width, height, is_crossed, corner_elements
            FROM dissections
            {where}
            ORDER BY dissection_id
            LIMIT %s OFFSET %s
        """, params + [PAGE_SIZE, offset])
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

        cur.execute(f"SELECT count(*) FROM dissections {where}", params)
        total = cur.fetchone()[0]

    return rows, total


def type_counts_for_order(order_val):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT d_type_counts FROM order_counts WHERE order_val = %s",
            (order_val,),
        )
        row = cur.fetchone()
        return row[0] if row else {}


def dissection_detail(dissection_id):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT dissection_id, order_val, graph_id, d_type, simple, perfect,
                   is_square, is_trivial_compound, width, height, bouwkamp_code,
                   is_crossed, corner_elements, boundary_square_indices
            FROM dissections WHERE dissection_id = %s
        """, (dissection_id,))
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cur.description]
        result = dict(zip(cols, row))
        result["elements"] = [int(x) for x in result["bouwkamp_code"].decode().split()]
        return result
