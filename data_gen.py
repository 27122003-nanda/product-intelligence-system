"""
Generates synthetic data across 4 source types with recurring themes so
aggregation questions ("most common complaint", "most requested feature")
have real signal.
"""
import json, os, random
from datetime import datetime, timedelta

random.seed(42)
OUT = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(OUT, exist_ok=True)

THEMES = [
    ("checkout_bug", "Checkout page fails intermittently with payment gateway timeout errors."),
    ("dark_mode", "Users are requesting a dark mode / theme option for the dashboard."),
    ("slow_reports", "Report generation for large accounts takes over 60 seconds and often times out."),
    ("sso_login", "Enterprise customers want SAML-based SSO login support."),
    ("mobile_app", "Customers ask for a native mobile app instead of the mobile web view."),
    ("export_csv", "Bulk CSV export is missing several columns compared to the UI table."),
    ("notification_spam", "Users complain about receiving too many email notifications with no granular controls."),
    ("api_rate_limit", "Developers hit API rate limits too quickly on the standard plan."),
]

CUSTOMERS = ["Acme Corp", "Globex", "Initech", "Umbrella Inc", "Stark Industries",
             "Wayne Enterprises", "Hooli", "Soylent", "Vandelay Industries", "Pied Piper"]

def rand_date(days_back=180):
    return (datetime.now() - timedelta(days=random.randint(0, days_back))).strftime("%Y-%m-%d")

def gen_tickets(n=30):
    docs = []
    for i in range(n):
        theme_key, theme_desc = random.choice(THEMES)
        cust = random.choice(CUSTOMERS)
        date = rand_date()
        resolved = random.random() < 0.4
        status = "RESOLVED" if resolved else "OPEN"
        text = (f"Support Ticket #{1000+i}\n"
                f"Customer: {cust}\nDate: {date}\nStatus: {status}\nTheme: {theme_key}\n\n"
                f"Description: {theme_desc} Reported by {cust}. "
                f"{'This was fixed in a later release after engineering investigation.' if resolved else 'Still awaiting a fix; customer has followed up twice.'}")
        docs.append({"id": f"ticket_{i}", "source_type": "support_ticket", "date": date,
                     "customer": cust, "theme": theme_key, "status": status, "text": text})
    return docs

def gen_feature_requests(n=15):
    docs = []
    for i in range(n):
        theme_key, theme_desc = random.choice(THEMES)
        cust = random.choice(CUSTOMERS)
        date = rand_date()
        prioritized = random.random() < 0.3
        text = (f"Feature Request #{i}\nCustomer: {cust}\nDate: {date}\n"
                f"Theme: {theme_key}\nPrioritized: {prioritized}\n\n"
                f"Request: {cust} is asking for: {theme_desc}")
        docs.append({"id": f"feature_{i}", "source_type": "feature_request", "date": date,
                     "customer": cust, "theme": theme_key, "prioritized": prioritized, "text": text})
    return docs

def gen_prds(n=5):
    docs = []
    picked_themes = random.sample(THEMES, n)
    for i, (theme_key, theme_desc) in enumerate(picked_themes):
        date = rand_date()
        text = (f"PRD: {theme_key.replace('_',' ').title()}\nDate: {date}\n\n"
                f"Problem: {theme_desc}\nGoal: Address this to reduce support burden and improve NPS.\n"
                f"Scope: Design, implementation, and rollout plan for {theme_key}.")
        docs.append({"id": f"prd_{i}", "source_type": "prd", "date": date,
                     "theme": theme_key, "text": text})
    return docs

def gen_meeting_notes(n=5):
    docs = []
    for i in range(n):
        date = rand_date()
        mentioned = random.sample(THEMES, 3)
        bullets = "\n".join([f"- Discussed {t[0].replace('_',' ')}: {t[1]}" for t in mentioned])
        text = f"Product Meeting Notes\nDate: {date}\n\n{bullets}\n\nAction items assigned to engineering leads."
        docs.append({"id": f"meeting_{i}", "source_type": "meeting_note", "date": date,
                     "themes": [t[0] for t in mentioned], "text": text})
    return docs

def main():
    all_docs = gen_tickets() + gen_feature_requests() + gen_prds() + gen_meeting_notes()
    with open(os.path.join(OUT, "corpus.jsonl"), "w") as f:
        for d in all_docs:
            f.write(json.dumps(d) + "\n")
    print(f"Generated {len(all_docs)} documents -> {OUT}/corpus.jsonl")

if __name__ == "__main__":
    main()
