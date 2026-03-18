import os
import random
from faker import Faker
from jinja2 import Template
import pdfkit
from pdf2image import convert_from_path
import cv2
from datetime import datetime, timedelta

fake = Faker('fr_FR')


vendors_count = 20
documents_per_vendor = ["quote", "invoice", "urssaf", "kbis", "rib"]
bank_list = ["BNP Paribas", "Société Générale", "Crédit Agricole",
             "La Banque Postale", "LCL", "HSBC France"]
output_dir = "dataset"


WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
POPLER_PATH = r"C:\Users\Nomade\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"

def realistic_company():
    formats = [
        f"{fake.last_name()} & {fake.last_name()}",
        f"{fake.last_name()} Consulting",
        f"{fake.last_name()} Services",
        f"{fake.last_name()} Industrie",
        f"{fake.last_name()} SARL",
        f"{fake.last_name()} SAS"
    ]
    return random.choice(formats)

product_list = [
    "Office Chair", "Desk Lamp", "Wooden Table", "Leather Sofa",
    "Wall Painting", "Carpet Rug", "Coffee Table", "Bookshelf",
    "Dining Chair", "Ceiling Lamp", "Curtains", "Desk Organizer",
    "Smart Thermostat", "Floor Lamp", "Sideboard", "Vase", 
    "Mirror", "Decorative Cushion", "LED Panel", "Storage Cabinet"
]


templates = {
    "quote": """<style>
body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 40px; color: #333; }
header { text-align: center; margin-bottom: 30px; }
header h1 { margin: 0; font-size: 32px; color: #2c3e50; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th, td { padding: 10px 12px; border: 1px solid #ccc; text-align: left; }
th { background-color: #f5f5f5; }
.label { font-weight: bold; width: 180px; }
footer { text-align: center; margin-top: 40px; font-size: 12px; color: #888; }
</style>
<header><h1>Quote</h1></header>
<table>
<tr><th>Field</th><th>Value</th></tr>
<tr><td class="label">Company</td><td>{{company_name}}</td></tr>
<tr><td class="label">SIRET</td><td>{{siret}}</td></tr>
<tr><td class="label">Quote Number</td><td>{{quote_number}}</td></tr>
<tr><td class="label">Product</td><td>{{product}}</td></tr>
<tr><td class="label">Amount HT</td><td>{{amount_ht}} €</td></tr>
<tr><td class="label">VAT</td><td>{{vat_rate}}%</td></tr>
<tr><td class="label">Total TTC</td><td>{{total_ttc}} €</td></tr>
<tr><td class="label">Quote Date</td><td>{{quote_date}}</td></tr>
<tr><td class="label">Validity Date</td><td>{{validity_date}}</td></tr>
</table>
<footer>Généré par groupe 31 IPSSI.</footer>""",
    
    "invoice": """<style>
body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 40px; color: #333; }
header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
header h1 { font-size: 32px; color: #2c3e50; margin: 0; }
header .date { font-size: 16px; color: #555; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th, td { padding: 10px 12px; border: 1px solid #ccc; text-align: left; }
th { background-color: #f5f5f5; }
.label { font-weight: bold; width: 180px; }
footer { text-align: center; margin-top: 40px; font-size: 12px; color: #888; }
</style>
<header>
<h1>Invoice</h1>
<div class="date">Date: {{invoice_date}}</div>
</header>
<table>
<tr><th>Field</th><th>Value</th></tr>
<tr><td class="label">Company</td><td>{{company_name}}</td></tr>
<tr><td class="label">SIRET</td><td>{{siret}}</td></tr>
<tr><td class="label">Invoice Number</td><td>{{invoice_number}}</td></tr>
<tr><td class="label">Product</td><td>{{product}}</td></tr>
<tr><td class="label">Amount HT</td><td>{{amount_ht}} €</td></tr>
<tr><td class="label">VAT</td><td>{{vat_rate}}%</td></tr>
<tr><td class="label">Total TTC</td><td>{{total_ttc}} €</td></tr>
</table>
<footer>Généré par groupe 31 IPSSI.</footer>""",

    "urssaf": """<style>
body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 40px; color: #333; }
header { text-align: center; margin-bottom: 30px; }
header h1 { margin: 0; font-size: 28px; color: #2c3e50; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th, td { padding: 10px 12px; border: 1px solid #ccc; text-align: left; }
th { background-color: #f5f5f5; }
.label { font-weight: bold; width: 180px; }
footer { text-align: center; margin-top: 40px; font-size: 12px; color: #888; }
</style>
<header><h1>URSSAF Certificate</h1></header>
<table>
<tr><th>Field</th><th>Value</th></tr>
<tr><td class="label">Company</td><td>{{company_name}}</td></tr>
<tr><td class="label">SIRET</td><td>{{siret}}</td></tr>
<tr><td class="label">Certificate Number</td><td>{{certificate_number}}</td></tr>
<tr><td class="label">Issue Date</td><td>{{issue_date}}</td></tr>
<tr><td class="label">Expiration Date</td><td>{{expiration_date}}</td></tr>
</table>
<footer>Généré par groupe 31 IPSSI.</footer>""",

    "kbis": """<style>
body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 40px; color: #333; }
header { text-align: center; margin-bottom: 30px; }
header h1 { margin: 0; font-size: 28px; color: #2c3e50; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th, td { padding: 10px 12px; border: 1px solid #ccc; text-align: left; }
th { background-color: #f5f5f5; }
.label { font-weight: bold; width: 180px; }
footer { text-align: center; margin-top: 40px; font-size: 12px; color: #888; }
</style>
<header><h1>Kbis Extract</h1></header>
<table>
<tr><th>Field</th><th>Value</th></tr>
<tr><td class="label">Company</td><td>{{company_name}}</td></tr>
<tr><td class="label">SIRET</td><td>{{siret}}</td></tr>
<tr><td class="label">Legal Form</td><td>{{legal_form}}</td></tr>
<tr><td class="label">Creation Date</td><td>{{creation_date}}</td></tr>
<tr><td class="label">Address</td><td>{{address}}</td></tr>
</table>
<footer>Généré par groupe 31 IPSSI.</footer>""",

    "rib": """<style>
body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 40px; color: #333; }
header { text-align: center; margin-bottom: 30px; }
header h1 { margin: 0; font-size: 28px; color: #2c3e50; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th, td { padding: 10px 12px; border: 1px solid #ccc; text-align: left; }
th { background-color: #f5f5f5; }
.label { font-weight: bold; width: 180px; }
footer { text-align: center; margin-top: 40px; font-size: 12px; color: #888; }
</style>
<header><h1>RIB</h1></header>
<table>
<tr><th>Field</th><th>Value</th></tr>
<tr><td class="label">Bank</td><td>{{bank_name}}</td></tr>
<tr><td class="label">IBAN</td><td>{{iban}}</td></tr>
<tr><td class="label">BIC</td><td>{{bic}}</td></tr>
<tr><td class="label">Account Holder</td><td>{{account_holder}}</td></tr>
<tr><td class="label">Company</td><td>{{company_name}}</td></tr>
</table>
<footer>Généré par groupe 31 IPSSI.</footer>"""
}

vendors = []
for i in range(1, vendors_count + 1):
    vendors.append({
        "vendor_id": f"V{i:02}",
        "company_name": realistic_company(),
        "siret": fake.siret(),
        "iban": fake.iban(),
        "bank_name": random.choice(bank_list),
        "bic": fake.swift(),
        "address": fake.address()
    })


scenario_counts = {
    "perfect": 6,
    "blur": 3,
    "rotate": 3,
    "expired_urssaf": 2,
    "siret_mismatch": 2,
    "price_mismatch": 2,
    "wrong_rib": 1,
    "multiple": 1
}

all_scenarios = []
for scenario, count in scenario_counts.items():
    all_scenarios.extend([scenario] * count)
random.shuffle(all_scenarios)

for i, vendor in enumerate(vendors):
    vendor["scenario"] = all_scenarios[i]

os.makedirs(output_dir, exist_ok=True)
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

def apply_blur(img_path):
    img = cv2.imread(img_path)
    blurred = cv2.GaussianBlur(img, (15, 15), 0)
    cv2.imwrite(img_path, blurred)

def apply_rotate(img_path):
    img = cv2.imread(img_path)
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    angle = random.choice([10, -10, 15, -15])
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h))
    cv2.imwrite(img_path, rotated)

for vendor in vendors:
    vendor_dir = os.path.join(output_dir, vendor["vendor_id"])
    os.makedirs(vendor_dir, exist_ok=True)
    
    selected_docs = random.sample(documents_per_vendor, 5)
    

    quote_total = None
    
    for doc_type in selected_docs:
    
        quote_date = fake.date_this_year()
        validity_date = fake.date_this_year()
        invoice_date = fake.date_this_year()
        issue_date = fake.date_this_year()
        expiration_date = fake.date_between(start_date='-1y', end_date='+1y')
        creation_date = fake.date_between(start_date='-10y', end_date='today')
        
        data = {
            "company_name": vendor["company_name"],
            "siret": vendor["siret"],
            "quote_number": f"Q-{random.randint(1000,9999)}",
            "invoice_number": f"INV-{random.randint(1000,9999)}",
            "product": random.choice(product_list),
            "amount_ht": round(random.uniform(500, 5000), 2),
            "vat_rate": 20,
            "total_ttc": 0,
            "quote_date": quote_date.strftime("%Y-%m-%d"),
            "validity_date": validity_date.strftime("%Y-%m-%d"),
            "invoice_date": invoice_date.strftime("%Y-%m-%d"),
            "certificate_number": f"URSSAF-{random.randint(10000,99999)}",
            "issue_date": issue_date.strftime("%Y-%m-%d"),
            "expiration_date": expiration_date.strftime("%Y-%m-%d"),
            "legal_form": random.choice(["SAS","SARL","EURL"]),
            "creation_date": creation_date.strftime("%Y-%m-%d"),
            "address": vendor["address"],
            "bank_name": vendor["bank_name"],
            "iban": vendor["iban"],
            "bic": vendor["bic"],
            "account_holder": vendor["company_name"]
        }
        
        data["total_ttc"] = round(data["amount_ht"] * (1 + data["vat_rate"]/100), 2)
        if doc_type == "quote":
            quote_total = data["total_ttc"]
        
        scenario = vendor["scenario"]
        if scenario == "expired_urssaf" and doc_type == "urssaf":
            data["expiration_date"] = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if scenario == "siret_mismatch" and doc_type in ["quote", "invoice"]:
            data["siret"] = fake.siret()
        if scenario == "price_mismatch" and doc_type == "invoice" and quote_total:
            data["total_ttc"] = quote_total + random.randint(10, 100)
        if scenario == "wrong_rib" and doc_type == "rib":
            data["iban"] = fake.iban()
            data["bic"] = fake.swift()
        if scenario == "multiple":
            if doc_type == "urssaf":
                data["expiration_date"] = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            if doc_type in ["quote", "invoice"]:
                data["siret"] = fake.siret()
                if doc_type == "invoice" and quote_total:
                    data["total_ttc"] = quote_total + random.randint(10, 100)
            if doc_type == "rib":
                data["iban"] = fake.iban()
                data["bic"] = fake.swift()
        
        template = Template(templates[doc_type])
        html_out = template.render(**data)
        
        save_as_image = random.choice([True, False])
        file_ext = "jpg" if save_as_image else "pdf"
        file_path = os.path.join(vendor_dir, f"{doc_type}.{file_ext}")
        
        if save_as_image:
            tmp_pdf = os.path.join(vendor_dir, f"{doc_type}_tmp.pdf")
            pdfkit.from_string(html_out, tmp_pdf, configuration=config, options={'encoding':'UTF-8'})
            images = convert_from_path(tmp_pdf, poppler_path=POPLER_PATH)
            images[0].save(file_path, "JPEG")
            os.remove(tmp_pdf)
            
            if scenario == "blur" and doc_type in ["quote", "invoice"]:
                apply_blur(file_path)
            if scenario == "rotate" and doc_type in ["quote", "invoice"]:
                apply_rotate(file_path)
            if scenario == "multiple" and doc_type in ["quote", "invoice"]:
                apply_rotate(file_path)
                apply_blur(file_path)
        else:
            pdfkit.from_string(html_out, file_path, configuration=config, options={'encoding':'UTF-8'})

print("Dataset generation complete")