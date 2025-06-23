from flask import Flask, render_template, request, send_file
import requests
import csv
import time

app = Flask(__name__)

# 🔐 Replace with your actual API key and search engine ID
API_KEY = "AIzaSyCiSrq6pK4mU94kz9xgY9tYQN6vbh0hdJ4"
CX = "859e28b397b204d50"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check_rank():
    keywords = [request.form.get(f'keyword{i}') for i in range(1, 11)]
    keywords = [kw.strip() for kw in keywords if kw and kw.strip()]
    target_domain = request.form.get('target_domain').strip()

    filename = 'rank_results.csv'
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Keyword", "Found", "Rank", "URL"])

        for keyword in keywords:
            found = False
            found_rank = "Not found"
            found_url = ""

            for start in range(1, 31, 10):  # Pages 1–3 (top 30)
                url = f"https://www.googleapis.com/customsearch/v1?q={keyword}&key={API_KEY}&cx={CX}&start={start}"

                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()
                    items = data.get("items", [])

                    for i, item in enumerate(items):
                        rank = start + i
                        link = item.get("link", "")
                        if target_domain in link:
                            found = True
                            found_rank = rank
                            found_url = link
                            break

                    if found:
                        break

                except Exception as e:
                    print(f"❌ Error: {e}")
                    break

                time.sleep(1)  # Respect rate limits

            writer.writerow([keyword, "Yes" if found else "No", found_rank, found_url])

    return send_file(filename, as_attachment=True)


import os

if __name__ == "__main__":
    # Get port from environment (Render sets this), default to 5000 locally
    port = int(os.environ.get("PORT", 5000))
    # Listen on all interfaces (0.0.0.0) so Render can route to it
    app.run(host="0.0.0.0", port=port, debug=True)