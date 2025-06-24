from flask import Flask, render_template, request, send_file
import requests, csv, time, os, json
from datetime import datetime

app = Flask(__name__)

API_KEYS = [
    "AIzaSyDGdP1pBqzkn0Hzf391629-he0iXob-CEQ",
    "AIzaSyB-Phs6TysIJflwxRtBWup5RJ1bJ4fQ3sQ",
    "AIzaSyCtc0DoHkxbbqIdUDcYV8zI_rmZOJWh96g",
    "AIzaSyBZXbZfQQ6p8wrZl_DTYnCFP_1iF2XUSkg"
]
CX = "859e28b397b204d50"
QUOTA_FILE = "quota_tracker.json"
RESET_FILE = "last_reset.txt"


def reset_daily_quota_if_needed():
    today = str(datetime.now().date())
    if not os.path.exists(RESET_FILE) or open(RESET_FILE).read() != today:
        with open(QUOTA_FILE, "w") as f:
            json.dump({key: 0 for key in API_KEYS}, f)
        with open(RESET_FILE, "w") as f:
            f.write(today)


def load_quota():
    if not os.path.exists(QUOTA_FILE):
        return {key: 0 for key in API_KEYS}
    with open(QUOTA_FILE, "r") as f:
        return json.load(f)


def save_quota(quota):
    with open(QUOTA_FILE, "w") as f:
        json.dump(quota, f)


def get_available_api_key():
    quota = load_quota()
    for key in API_KEYS:
        if quota.get(key, 0) < 100:
            return key, quota
    return None, quota


@app.route("/")
def index():
    reset_daily_quota_if_needed()
    quota = load_quota()
    usage_display = "\n".join([
        f"🔑 ...{key[-4:]} used {count}/100 requests" for key, count in quota.items()
    ])
    return render_template("index.html", quota_info=quota, usage_display=usage_display)


@app.route("/check", methods=["POST"])
def check_rank():
    reset_daily_quota_if_needed()
    raw_keywords = request.form.get('keywords', '')
    keywords = [kw.strip() for kw in raw_keywords.split('\n') if kw.strip()][:10]
    target_domain = request.form.get('target_domain').strip()
    search_domain = request.form.get('search_domain') or "google.com"

    filename = 'rank_results.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Keyword", "Found", "Rank", "URL"])

        for keyword in keywords:
            found = False
            found_rank = "Not found"
            found_url = ""

            for start in range(1, 31, 10):
                api_key, quota = get_available_api_key()
                if not api_key:
                    return "❌ All API keys are exhausted."

                url = f"https://www.googleapis.com/customsearch/v1?q={keyword}&key={api_key}&cx={CX}&start={start}&gl={search_domain.split('.')[-1]}"
                print(f"🔑 Using API Key ending in: {api_key[-4:]}")

                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()
                    items = data.get("items", [])

                    quota[api_key] += 1
                    save_quota(quota)

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

                time.sleep(1)

            writer.writerow([keyword, "Yes" if found else "No", found_rank, found_url])

    return send_file(filename, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)