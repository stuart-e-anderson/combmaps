from flask import Blueprint, render_template

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/order/<int:order_n>")
def by_order(order_n):
    # TODO: query tilings table
    return render_template("order.html", order_n=order_n, tilings=[])
