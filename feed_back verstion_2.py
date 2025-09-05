from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from xhtml2pdf import pisa
from io import BytesIO
import mysql.connector
from mysql.connector import Error
import os

app = Flask(__name__)
CORS(app)

# Database configuration (secure with env vars in production)
db_config = {
    'host': os.getenv("DB_HOST", "106.51.181.21"),
    'user': os.getenv("DB_USER", "root"),
    'port': int(os.getenv("DB_PORT", 3306)),
    'password': os.getenv("DB_PASSWORD", "Arun@7188"),
    'database': os.getenv("DB_NAME", "concrete_oem")
}


@app.route('/')
def index():
    """Serve feedback HTML form"""
    return render_template('feed_v2.html')


@app.route('/submit', methods=['POST'])
def submit_feedback():
    """Handle feedback form submission and store in database"""
    data = request.get_json()
    if not data:
        return jsonify({"status": "fail", "message": "No JSON data received"}), 400

    try:
        # Extract and sanitize form values
        values = (
            data.get("customer_name"),
            data.get("supervisor_name"),
            data.get("contact_number"),
            data.get("email_id"),
            data.get("date"),
            data.get("start_time"),
            data.get("end_time"),
            data.get("pump"),
            data.get("dump"),
            int(data.get("site_sup", 0)),
            int(data.get("tm_driver", 0)),
            int(data.get("fse", 0)),
            int(data.get("pumping_staff", 0)),
            int(data.get("order_taker", 0)),
            int(data.get("plant_staff", 0)),
            int(data.get("safety", 0)),
            int(data.get("performance", 0)),
            data.get("suggestions"),
            data.get("recommend")
        )

        # SQL query to insert data
        query = """
            INSERT INTO feedbacks (
                customer_name, supervisor_name, contact_number, email_id,
                date, start_time, end_time, pump, dump,
                site_sup, tm_driver, fse, pumping_staff,
                order_taker, plant_staff, safety, performance,
                suggestions, recommend
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        # Insert into database
        with mysql.connector.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                conn.commit()

        return jsonify({"status": "success", "message": "Feedback submitted successfully"}), 200

    except Error as err:
        print("❌ Database Error:", err)
        return jsonify({"status": "fail", "message": str(err)}), 500

    except Exception as ex:
        print("❌ General Error:", ex)
        return jsonify({"status": "fail", "message": str(ex)}), 500


@app.route('/download', methods=['POST'])
def download_pdf():
    """Generate feedback summary PDF from JSON data"""
    data = request.get_json()
    if not data:
        return jsonify({"status": "fail", "message": "No JSON data received"}), 400

    html_template = f"""
    <html>
    <head>
      <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; }}
        h2 {{ color: #2E86C1; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin-bottom: 5px; }}
      </style>
    </head>
    <body>
      <h2>Concrete OEM - Feedback Summary</h2>
      <p><strong>Customer Name:</strong> {data.get("customer_name")}</p>
      <p><strong>Supervisor:</strong> {data.get("supervisor_name")}</p>
      <p><strong>Contact Number:</strong> {data.get("contact_number")}</p>
      <p><strong>Email:</strong> {data.get("email_id")}</p>
      <p><strong>Date:</strong> {data.get("date")}</p>
      <p><strong>Start Time:</strong> {data.get("start_time")}</p>
      <p><strong>End Time:</strong> {data.get("end_time")}</p>
      <p><strong>Pump:</strong> {data.get("pump")}</p>
      <p><strong>Dump:</strong> {data.get("dump")}</p>

      <h4>Ratings:</h4>
      <ul>
        <li><strong>Site Supervisor:</strong> {data.get("site_sup")}</li>
        <li><strong>TM Driver:</strong> {data.get("tm_driver")}</li>
        <li><strong>FSE:</strong> {data.get("fse")}</li>
        <li><strong>Pumping Staff:</strong> {data.get("pumping_staff")}</li>
        <li><strong>Order Taker:</strong> {data.get("order_taker")}</li>
        <li><strong>Plant Staff:</strong> {data.get("plant_staff")}</li>
        <li><strong>Safety:</strong> {data.get("safety")}</li>
        <li><strong>Performance:</strong> {data.get("performance")}</li>
      </ul>

      <p><strong>Suggestions:</strong> {data.get("suggestions")}</p>
      <p><strong>Recommended?:</strong> {data.get("recommend")}</p>
    </body>
    </html>
    """

    # Convert HTML to PDF
    pdf_buffer = BytesIO()
    result = pisa.CreatePDF(html_template, dest=pdf_buffer)

    if result.err:
        print("❌ PDF generation error")
        return jsonify({"status": "error", "message": "PDF generation failed."}), 500

    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name="feedback_summary.pdf",
        mimetype="application/pdf"
    )


if __name__ == '__main__':
    app.run(debug=True)
