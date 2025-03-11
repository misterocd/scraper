from flask import Flask, render_template, request, redirect, url_for
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

BASE_URL = "https://steuerberaterverzeichnis.berufs-org.de/"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get form data
        last_name = request.form.get("last_name", "").strip()
        first_name = request.form.get("first_name", "").strip()
        place = request.form.get("place", "").strip()
        street = request.form.get("street", "").strip()
        chamber = request.form.get("chamber", "").strip()

        # Perform search
        results = search_steuerberater(last_name, first_name, place, street, chamber)
        return render_template("results.html", results=results)
    
    return render_template("index.html")

def search_steuerberater(last_name, first_name, place, street, chamber):
    session = requests.Session()
    search_params = {
        "nachnameOrFirmenname": last_name,
        "vorname": first_name,
        "plzOrOrt": place,
        "strasse": street,
        "kammer": chamber,
        "lang": "de"
    }
    response = session.post(BASE_URL, data=search_params)
    soup = BeautifulSoup(response.content, 'html.parser')
    results = soup.find_all('a', class_='link-to-detail')
    return results

@app.route("/details/<path:detail_link>")
def details(detail_link):
    session = requests.Session()
    detail_url = BASE_URL + detail_link
    details = scrape_details(session, detail_url)
    return render_template("details.html", details=details)

def scrape_details(session, url):
    response = session.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    def get_text_or_default(element, default="N/A"):
        return element.get_text(strip=True) if element else default
    
    details = {
        "Profession": get_text_or_default(soup.find('p', id='beruf')),
        "Academic Title": get_text_or_default(soup.find('p', id='akademische-grade')),
        "Name": get_text_or_default(soup.find('p', id='vorname-and-nachname')),
        "Address": get_text_or_default(soup.find('p', id='adresse'), default="").replace("<br>", "\n"),
        "Phone": get_text_or_default(soup.find('p', id='telefon')).replace("Telefon:", "").strip(),
        "Email": get_text_or_default(soup.find('p', id='email')).replace("E-Mail:", "").strip(),
        "Website": get_text_or_default(soup.find('p', id='internetseite')).replace("Internet:", "").strip(),
        "Appointment Date": get_text_or_default(soup.find('span', id='bestelldatum-order-date').find_next('span') if soup.find('span', id='bestelldatum-order-date') else None),
        "Chamber": get_text_or_default(soup.find('section', id='regionalkammerSection').find_all('span')[1] if soup.find('section', id='regionalkammerSection') else None),
        "Chamber Address": get_text_or_default(soup.find('section', id='regionalkammerSection').find_all('span')[2] if soup.find('section', id='regionalkammerSection') else None),
    }
    return details

if __name__ == "__main__":
    app.run(debug=True)
