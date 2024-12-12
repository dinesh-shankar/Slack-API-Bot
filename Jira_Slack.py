import requests
import json
from slack_sdk import WebClient

# Jira server URL
jira_server = 'https' -> Jira API End point

# Read configurations from file
with open('config.json') as config_file:
    config = json.load(config_file)


# Retrieve Jira credentials from config
jira_username = config['jira_username']
jira_password = config['jira_password']

# Filter ID FDR-RDK_ALL_QA_Reproduced
filter_id = '' #-> Filter ID 

# Construct the request URL with filter ID
url = f"{jira_server}/rest/api/2/search?jql=filter={filter_id}"

# Define headers for basic authentication
headers = {
    'Content-Type': 'application/json'
}

# Make the request to Jira
response = requests.get(url, headers=headers, auth=(jira_username, jira_password))

# Initialize issues_data
issues_data = []

# Check if the request was successful
if response.status_code == 200:
    # Extract issues data from the response
    issues_data = response.json()['issues']
else:
    print(f"Failed to retrieve issues from Jira. Status code: {response.status_code}")

# Prepare Slack message
slack_message = {
    "text": "FDR Issue",
    "attachments": []
}

# Initialize issue count
issue_count = 0

# Format each issue as an attachment
for index, issue in enumerate(issues_data, start=1):
    # Customize attachment fields as needed
    issue_key = issue['key']
    issue_summary = issue['fields']['summary']
    issue_status = issue['fields']['status']['name']
    issue_priority = issue['fields']['priority']['name']  # Extract priority of the issue
    issue_link = f"{jira_server}/browse/{issue_key}"  # Construct Jira issue URL with the new base URL
    attachment_text = f"{index}. <{issue_link}|{issue_key}> - {issue_summary}\nPriority: {issue_priority}"  # Include serial number, issue details, and priority with Jira link
    slack_message["attachments"].append({"text": attachment_text})

    # Increment issue count
    issue_count += 1

# Join the attachment texts with newline characters
formatted_attachments = "\n".join([attachment["text"] for attachment in slack_message["attachments"]])
slack_message["text"] = formatted_attachments

# Add the message at the end of the Slack message
slack_message["text"] += "\n\n:alert: - Please find the below reproduced tickets from FDR Team\n======================================================================\n:robot_face:BOTsupportcontact: DineshShankar666@gmail.com"

# Define your Slack bot token
SLACK_BOT_TOKEN = ''

# Initialize Slack WebClient
slack_client = WebClient(token=SLACK_BOT_TOKEN)

# Send the message to a specific channel
channel_id = "fdr-reproduced-ticket-alert"  # Replace with your desired channel ID
response_slack = slack_client.chat_postMessage(channel=channel_id, text=slack_message["text"])

if response_slack["ok"]:
    print("Message sent successfully to Slack!")
else:
    print("Failed to send message to Slack:", response_slack["error"])
