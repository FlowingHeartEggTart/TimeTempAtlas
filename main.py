from sanic import Sanic
from sanic.response import json, html, HTTPResponse
import xml.etree.ElementTree as ET
from xml.dom import minidom
import csv
import io

app = Sanic("GlobalTemperatureApp")

# 读取数据
def read_data(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    data = []
    for line in lines:
        if line.startswith("#") or not line.strip():
            continue
        year, no_smoothing, lowess = line.split()
        data.append({
            "year": int(year),
            "no_smoothing": float(no_smoothing),
            "lowess": float(lowess)
        })
    return data

data = read_data("graph.txt")

# 按年份查询数据
@app.route("/query", methods=["GET"])
async def query(request):
    start_year = int(request.args.get("start", 1880))
    end_year = int(request.args.get("end", 2022))
    sort_order = request.args.get("sort", "asc")
    output_format = request.args.get("format", "json")

    filtered_data = [d for d in data if start_year <= d["year"] <= end_year]
    
    # 排序
    if sort_order == "asc":
        filtered_data.sort(key=lambda x: x["no_smoothing"])
    else:
        filtered_data.sort(key=lambda x: x["no_smoothing"], reverse=True)

    # 输出格式处理
    if output_format == "json":
        return json(filtered_data)
    elif output_format == "xml":
        root = ET.Element("data")
        for entry in filtered_data:
            year_element = ET.SubElement(root, "entry")
            ET.SubElement(year_element, "year").text = str(entry["year"])
            ET.SubElement(year_element, "no_smoothing").text = str(entry["no_smoothing"])
            ET.SubElement(year_element, "lowess").text = str(entry["lowess"])

        xml_str = ET.tostring(root, encoding="unicode")
        parsed_xml = minidom.parseString(xml_str)
        pretty_xml_str = parsed_xml.toprettyxml(indent="  ")
        
        return html(f"<pre><code>{pretty_xml_str}</code></pre>")
    elif output_format == "csv":
        # 创建CSV文件数据流
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        csv_writer.writerow(["Year", "No_Smoothing", "Lowess"])
        for entry in filtered_data:
            csv_writer.writerow([entry["year"], entry["no_smoothing"], entry["lowess"]])
        
        # 获取CSV数据并返回为 HTTPResponse
        csv_buffer.seek(0)
        csv_data = csv_buffer.getvalue()
        
        return HTTPResponse(csv_data, headers={
            "Content-Disposition": "attachment; filename=temperature_data.csv",
            "Content-Type": "text/csv"
        })

# 页面展示
@app.route("/")
async def index(request):
    return html("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Global Temperature Query</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
        <style>
            body { background: #f4f6f9; color: #34495e; font-family: 'Poppins', sans-serif; }
            .container { margin-top: 50px; max-width: 900px; }
            h1 { text-align: center; font-size: 2.5rem; margin-bottom: 30px; font-weight: 600; }
            .form-group { margin-bottom: 20px; }
            .form-control, .btn { border-radius: 10px; }
            .form-control:focus { box-shadow: 0 0 10px rgba(52, 152, 219, 0.8); border-color: #3498db; }
            .btn-primary { background-color: #3498db; border-color: #2980b9; font-weight: 600; }
            .btn-primary:hover { background-color: #2980b9; border-color: #3498db; }
            .card { background: #fff; border-radius: 15px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); padding: 30px; margin-top: 20px; }
            .card-title { font-size: 1.8rem; font-weight: 600; }
            .btn-group { display: flex; justify-content: center; margin-top: 20px; }
            .btn-group .btn { margin: 0 10px; }
            footer { text-align: center; margin-top: 40px; font-size: 0.9rem; color: #7f8c8d; }
            pre, code { background-color: #f8f9fa; padding: 20px; border-radius: 10px; font-size: 14px; border: 1px solid #ccc; white-space: pre-wrap; word-wrap: break-word; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Global Temperature Data Query</h1>
            <div class="card">
                <h2 class="card-title">Enter Your Query</h2>
                <form action="/query" method="get">
                    <div class="form-group">
                        <label for="start">Start Year</label>
                        <input type="number" id="start" name="start" class="form-control" value="1880" required>
                    </div>
                    <div class="form-group">
                        <label for="end">End Year</label>
                        <input type="number" id="end" name="end" class="form-control" value="2022" required>
                    </div>
                    <div class="form-group">
                        <label for="sort">Sort Order</label>
                        <select id="sort" name="sort" class="form-control">
                            <option value="asc">Ascending</option>
                            <option value="desc">Descending</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="format">Output Format</label>
                        <select id="format" name="format" class="form-control">
                            <option value="json">JSON</option>
                            <option value="xml">XML</option>
                            <option value="csv">CSV (Download)</option>
                        </select>
                    </div>
                    <div class="btn-group">
                        <button type="submit" class="btn btn-primary">Submit Query</button>
                    </div>
                </form>
            </div>
            <footer>&copy; 2024 Global Temperature Query - Data by [Your Source]</footer>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
