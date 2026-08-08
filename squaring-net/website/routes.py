from flask import Blueprint, abort, render_template, request

from squaringlib.render import render_svg

from . import db

main = Blueprint("main", __name__)


@main.route("/")
def index():
    orders = db.orders_summary()
    return render_template("index.html", orders=orders)


@main.route("/order/<int:order_val>")
def by_order(order_val):
    d_type = request.args.get("type") or None
    page = max(1, request.args.get("page", 1, type=int))

    dissections, total = db.dissections_for_order(order_val, d_type=d_type, page=page)
    type_counts = db.type_counts_for_order(order_val)
    total_pages = max(1, -(-total // db.PAGE_SIZE))

    return render_template(
        "order.html",
        order_val=order_val, dissections=dissections, total=total,
        d_types=db.D_TYPES, active_type=d_type, type_counts=type_counts,
        page=page, total_pages=total_pages,
    )


@main.route("/dissection/<int:dissection_id>")
def dissection_detail(dissection_id):
    d = db.dissection_detail(dissection_id)
    if d is None:
        abort(404)
    svg = render_svg(d["elements"], d["width"], d["height"])
    return render_template("dissection.html", d=d, svg=svg)
