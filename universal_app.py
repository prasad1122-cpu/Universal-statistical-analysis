from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from fpdf import FPDF
import uuid
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
CHART_FOLDER = 'static/charts'
REPORT_FOLDER = 'static/reports'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHART_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

def guess_analysis(objective_text, df):
    objective_text = objective_text.lower()
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()

    if "relationship" in objective_text or "correlation" in objective_text:
        return "correlation", numeric_cols
    elif "impact" in objective_text or "effect" in objective_text:
        return "regression", numeric_cols[:2] if len(numeric_cols) >= 2 else numeric_cols
    elif "distribution" in objective_text or "pattern" in objective_text:
        return "descriptive", numeric_cols
    else:
        return "default", numeric_cols

@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files['file']
    objective = request.form.get('research_objective', 'relationship analysis')
    file_id = str(uuid.uuid4())

    filepath = os.path.join(UPLOAD_FOLDER, file_id + "_" + file.filename)
    file.save(filepath)

    try:
        df = pd.read_excel(filepath) if file.filename.endswith('.xlsx') else pd.read_csv(filepath)
        analysis_type, cols = guess_analysis(objective, df)

        chart_filename = f"{file_id}_chart.png"
        chart_path = os.path.join(CHART_FOLDER, chart_filename)

        if analysis_type == "correlation":
            plt.figure(figsize=(6, 4))
            sns.heatmap(df[cols].corr(), annot=True, cmap='coolwarm')
            plt.title("Correlation Matrix")
        elif analysis_type == "regression" and len(cols) >= 2:
            plt.figure(figsize=(6, 4))
            sns.regplot(x=cols[0], y=cols[1], data=df)
            plt.title(f"Regression: {cols[0]} vs {cols[1]}")
        else:
            plt.figure(figsize=(6, 4))
            df[cols].hist(bins=10)
            plt.tight_layout()
            plt.suptitle("Descriptive Distribution", y=1.02)

        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close()

        # Generate PDF report
        pdf_filename = f"{file_id}_report.pdf"
        report_path = os.path.join(REPORT_FOLDER, pdf_filename)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Research Objective:", ln=True)
        pdf.multi_cell(0, 10, txt=objective)
        pdf.cell(200, 10, txt="Analysis Type: " + analysis_type, ln=True)
        pdf.cell(200, 10, txt="Columns Used: " + ', '.join(cols), ln=True)
        pdf.image(chart_path, x=10, y=50, w=180)
        pdf.output(report_path)

        return jsonify({
            "message": f"Performed {analysis_type} based on your objective.",
            "chart_url": f"/chart/{chart_filename}",
            "report_url": f"/report/{pdf_filename}",
            "columns_used": cols
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chart/<filename>")
def get_chart(filename):
    return send_file(os.path.join(CHART_FOLDER, filename), mimetype='image/png')

@app.route("/report/<filename>")
def get_report(filename):
    return send_file(os.path.join(REPORT_FOLDER, filename), mimetype='application/pdf')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

