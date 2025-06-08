
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import uuid
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
CHART_FOLDER = 'charts'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHART_FOLDER, exist_ok=True)

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

        chart_path = os.path.join(CHART_FOLDER, f"{file_id}_chart.png")

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

        return jsonify({
            "message": f"Performed {analysis_type} based on your objective",
            "chart_url": f"/chart/{file_id}_chart.png",
            "columns_used": cols
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chart/<filename>")
def get_chart(filename):
    return send_file(os.path.join(CHART_FOLDER, filename), mimetype='image/png')

if __name__ == "__main__":
    app.run(debug=True)
