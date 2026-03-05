from flask import Flask, render_template, request
import math


app = Flask(__name__)


def pizza_area(diameter: float) -> float:
    r = diameter / 2.0
    return math.pi * (r ** 2)


def price_per_sq_in(price: float, diameter: float) -> float:
    area = pizza_area(diameter)
    return price / area if area > 0 else float("inf")


@app.route("/", methods=["GET", "POST"])
def index():
    rows = [
        {"name": "Small", "diameter": 10.0, "price": 8.99},
        {"name": "Medium", "diameter": 12.0, "price": 10.99},
        {"name": "Large", "diameter": 16.0, "price": 14.99},
    ]
    result = []

    if request.method == "POST":
        names = request.form.getlist("name")
        diams = request.form.getlist("diameter")
        prices = request.form.getlist("price")

        rows = []
        for n, d, p in zip(names, diams, prices):
            if not (n or d or p):
                continue
            try:
                d_val = float(d)
                p_val = float(p)
            except (TypeError, ValueError):
                # skip invalid rows
                continue
            rows.append({"name": n or "Pizza", "diameter": d_val, "price": p_val})

    # compute results
    for r in rows:
        ppsi = price_per_sq_in(r["price"], r["diameter"])  # price per square inch
        result.append({
            "name": r["name"],
            "diameter": r["diameter"],
            "price": r["price"],
            "ppsi": ppsi,
        })

    # find best value (min ppsi)
    best_idx = None
    if result:
        best_idx = min(range(len(result)), key=lambda i: result[i]["ppsi"])

    return render_template("index.html", rows=rows, result=result, best_idx=best_idx)


if __name__ == "__main__":
    app.run(debug=True)

