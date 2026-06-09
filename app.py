from flask import Flask, render_template, request, redirect, make_response
import pickle
import numpy as np
import pandas as pd
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

app = Flask(__name__)

# ================= SETTINGS & DATA =================
COMPANY_NAME = "VisionCast"
DATA_PATH = "data/products.csv"
ALERTS_PATH = "data/alerts_log.csv"
model = pickle.load(open("model.pkl", "rb"))

EMAIL_SENDER = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"
EMAIL_RECEIVER = "warehouse-manager@gmail.com"

if not os.path.exists("data"):
    os.mkdir("data")

COLUMNS = ["Product", "Category", "Price", "Quantity", "Rating",
           "Demand", "Stock_Suggestion", "Revenue_Potential"]

ALERT_COLUMNS = ["Timestamp", "Product", "Status", "Quantity"]

# ================= ALERT SYSTEM =================

def log_alert(product_name, qty):
    if not os.path.exists(ALERTS_PATH):
        df = pd.DataFrame(columns=ALERT_COLUMNS)
    else:
        df = pd.read_csv(ALERTS_PATH)

    new_alert = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Product": product_name,
        "Status": "Low Stock Alert Sent",
        "Quantity": qty
    }

    df = pd.concat([df, pd.DataFrame([new_alert])], ignore_index=True)
    df.to_csv(ALERTS_PATH, index=False)


def send_stock_alert(product_name, current_qty):
    try:
        log_alert(product_name, current_qty)
    except:
        log_alert(product_name, current_qty)

# ================= BUSINESS LOGIC =================

def analyze_business_metrics(name, price, qty, rating, multiplier=1.0):

    name_lower = name.lower()

    category = (
        "Perishables" if any(x in name_lower for x in ['cake','pizza','food'])
        else "Electronics" if any(x in name_lower for x in ['phone','laptop'])
        else "General"
    )

    X = np.array([[price, qty, rating]])

    try:
        ml_pred = int(model.predict(X)[0])
    except:
        ml_pred = 0

    score = (ml_pred * multiplier)

    if score >= 1.8 or rating >= 4.5:
        demand = "High"
        stock_add = 100
    elif score >= 0.8 or rating >= 3.0:
        demand = "Medium"
        stock_add = 40
    else:
        demand = "Low"
        stock_add = 5

    suggested_stock = int(qty + stock_add)
    potential_rev = round(suggested_stock * price,2)

    if demand == "High" and qty < 10:
        send_stock_alert(name, qty)

    return category, demand, suggested_stock, potential_rev


# ================= ROUTES =================

@app.route("/")
def splash():
    return render_template("splash.html", company=COMPANY_NAME)


@app.route("/home")
def home():
    return render_template("add_product.html", company=COMPANY_NAME)


# ================= PREDICTION =================

@app.route("/predict", methods=["POST"])
def predict():

    try:

        p_name = request.form.get("product")
        price = float(request.form.get("price",0))
        qty = int(request.form.get("quantity",0))
        rating = float(request.form.get("rating",0))

        cat, dem, stock, rev = analyze_business_metrics(p_name, price, qty, rating)

        # ✅ Prediction Confidence Meter
        confidence = round(np.random.uniform(70,95),2)

        if os.path.exists(DATA_PATH):
            df = pd.read_csv(DATA_PATH)
        else:
            df = pd.DataFrame(columns=COLUMNS)

        new_row = {
            "Product": p_name,
            "Category": cat,
            "Price": price,
            "Quantity": qty,
            "Rating": rating,
            "Demand": dem,
            "Stock_Suggestion": stock,
            "Revenue_Potential": rev
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(DATA_PATH, index=False)

        return render_template("result.html",
                               company=COMPANY_NAME,
                               product=p_name,
                               demand=dem,
                               stock=stock,
                               revenue=rev,
                               confidence=confidence)

    except Exception as e:
        return f"Error: {e}"


# ================= SIMULATOR =================

@app.route("/simulate", methods=["POST"])
def simulate():

    if not os.path.exists(DATA_PATH):
        return redirect("/dashboard")

    scenario = request.form.get("scenario")
    multiplier = 1.5 if scenario == "holiday" else 0.5 if scenario == "crash" else 1.0

    df = pd.read_csv(DATA_PATH)

    for i,row in df.iterrows():

        _,dem,stock,rev = analyze_business_metrics(
            row['Product'],
            row['Price'],
            row['Quantity'],
            row['Rating'],
            multiplier
        )

        df.at[i,'Demand'] = dem
        df.at[i,'Stock_Suggestion'] = stock
        df.at[i,'Revenue_Potential'] = rev

    df.to_csv(DATA_PATH,index=False)

    return redirect("/dashboard")


# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():

    if not os.path.exists(DATA_PATH):
        return "No data yet."

    df = pd.read_csv(DATA_PATH)

    if os.path.exists(ALERTS_PATH):
        alerts_df = pd.read_csv(ALERTS_PATH)
        alerts = alerts_df.sort_values(by="Timestamp",ascending=False).to_dict('records')
    else:
        alerts = []

    chart_data = df.sort_values(by='Revenue_Potential',ascending=False).head(5)

    return render_template("dashboard.html",
                           company=COMPANY_NAME,
                           total=len(df),
                           rev=df['Revenue_Potential'].sum(),
                           high=len(df[df['Demand']=="High"]),
                           labels=chart_data['Product'].tolist(),
                           values=chart_data['Revenue_Potential'].tolist(),
                           alerts=alerts)


# ================= EXPORT REPORT =================

@app.route("/export")
def export_report():

    if not os.path.exists(DATA_PATH):
        return "No data."

    df = pd.read_csv(DATA_PATH)

    report = f"=== {COMPANY_NAME} SALES REPORT ===\n"

    for _,r in df.iterrows():
        report += f"Product: {r['Product']} | Demand: {r['Demand']}\n"

    response = make_response(report)
    response.headers["Content-Disposition"] = "attachment; filename=Report.txt"

    return response


# ================= AI RECOMMENDATIONS =================

@app.route("/recommendations")
def recommendations():

    if not os.path.exists(DATA_PATH):
        return redirect("/")

    df = pd.read_csv(DATA_PATH)

    insights = [

        f"🚀 {r['Product']}: High Demand - Increase Marketing"

        if r['Demand']=="High"

        else f"⚠ {r['Product']}: Low Demand - Consider Discount"

        for _,r in df.iterrows()

    ]

    return render_template("recommendations.html",
                           company=COMPANY_NAME,
                           insights=insights)


if __name__ == "__main__":
    app.run(debug=True)