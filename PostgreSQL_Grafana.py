import requests
import psycopg2
from configparser import ConfigParser
from datetime import datetime, timedelta

# Read configuration from config.ini
config = ConfigParser()
config.read('config.ini')

# Jira API credentials and URL
JIRA_SERVER = config['JIRA']['server']
JIRA_SEARCH_ENDPOINT = f'{JIRA_SERVER}/rest/api/2/search'
JIRA_USER = config['JIRA']['user']
JIRA_PASSWORD = config['JIRA']['password']
JQL_QUERY = config['JIRA']['jql_query']

# PostgreSQL database credentials
DB_HOST = config['DATABASE']['host']
DB_NAME = config['DATABASE']['dbname']
DB_USER = config['DATABASE']['user']
DB_PASSWORD = config['DATABASE']['password']

# Function to fetch tickets from Jira
def fetch_tickets():
    headers = {
        'Content-Type': 'application/json',
    }
    params = {
        'jql': JQL_QUERY,
        'fields': 'key,summary,status,created,updated'
    }
    response = requests.get(JIRA_SEARCH_ENDPOINT, auth=(JIRA_USER, JIRA_PASSWORD), headers=headers, params=params)
    
    # Print the status code and the response for debugging
    print("Status Code:", response.status_code)
    print("Response:", response.json())
    
    response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
    
    # Check if 'issues' key exists in the response
    if 'issues' not in response.json():
        raise KeyError("The 'issues' key is not found in the response.")
    
    return response.json()['issues']

# Function to initialize the PostgreSQL database
def init_db():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (
                        ticket_id TEXT PRIMARY KEY,
                        summary TEXT,
                        status TEXT,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP)''')
    conn.commit()
    cursor.close()
    conn.close()

# Function to store tickets in the PostgreSQL database
def store_tickets(tickets):
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()

    # Debugging: Print the column names in the tickets table
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='tickets'")
    columns = cursor.fetchall()
    print("Columns in tickets table:", columns)

    for ticket in tickets:
        ticket_id = ticket.get('key')
        summary = ticket['fields']['summary']
        status = ticket['fields']['status']['name']
        created_at = ticket['fields']['created']
        updated_at = ticket['fields']['updated']
        cursor.execute('''INSERT INTO tickets (ticket_id, summary, status, created_at, updated_at)
                          VALUES (%s, %s, %s, %s, %s)
                          ON CONFLICT (ticket_id) DO UPDATE 
                          SET summary = EXCLUDED.summary,
                              status = EXCLUDED.status,
                              created_at = EXCLUDED.created_at,
                              updated_at = EXCLUDED.updated_at''', 
                          (ticket_id, summary, status, created_at, updated_at))
    conn.commit()
    cursor.close()
    conn.close()

# Main function to execute the workflow
def main():
    init_db()
    tickets = fetch_tickets()
    store_tickets(tickets)

if __name__ == '__main__':
    main()
