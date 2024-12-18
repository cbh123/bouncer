import sqlite3
import time
import os
import requests
import colorama
from colorama import Fore, Style
import json
import subprocess

DB_PATH = "/Users/charlie/Library/Messages/chat.db"

def get_current_max_date():
    """
    Returns the maximum date value (integer) found in the 'message' table.
    If the table is empty, returns 0.
    """
    if not os.path.isfile(DB_PATH):
        raise FileNotFoundError(f"Database not found at '{DB_PATH}'")

    uri = f"file:{DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    c = conn.cursor()
    c.execute("SELECT MAX(date) FROM message")
    result = c.fetchone()
    conn.close()

    return result[0] if result and result[0] else 0

def get_new_messages_since(threshold_date):
    """
    Fetches messages with a 'date' > threshold_date.
    This way, only new messages that arrived after threshold_date will appear.
    """
    if not os.path.isfile(DB_PATH):
        raise FileNotFoundError(f"Database not found at '{DB_PATH}'")

    uri = f"file:{DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    c = conn.cursor()

    query = """
    SELECT message.date, message.text, handle.id
    FROM message
    JOIN handle ON message.handle_id = handle.rowid
    WHERE message.date > ?
      AND message.text IS NOT NULL
    ORDER BY message.date ASC
    """
    c.execute(query, (threshold_date,))
    results = c.fetchall()
    conn.close()
    return results

def determine_importance(text):
    prompt = f"Is the following text important? Please answer yes or no, then explain briefly.\n\nText: {text}"

    request_payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False,
        "format": {
            "type": "object",
            "properties": {
                "important": {
                    "type": "boolean",
                    "description": "Whether the message is important"
                },
                "explanation": {
                    "type": "string",
                    "description": "A brief explanation for why the message is important"
                }
            },
            "required": ["important", "explanation"]
        }
    }
    response = requests.post(
        "http://localhost:11434/api/generate",
        headers={"Content-Type": "application/json"},
        json=request_payload
    )
    response_json = response.json()
    parsed_response = json.loads(response_json['response'])
    return parsed_response

def send_notification(title, message, sender):
    """
    Sends a system notification using osascript (macOS only) with a button to open iMessage
    """
    # Escape double quotes in the message and title
    message = message.replace('"', '\\"')
    title = title.replace('"', '\\"')
    sender = sender.replace('"', '\\"')
    
    apple_script = '''
    display alert "{}" message "{}" buttons {{"Open iMessage", "OK"}}
    if button returned of result = "Open iMessage" then
        tell application "Messages"
            activate
            set targetService to 1st service whose service type = iMessage
            send "{}" to participant "{}" of targetService
        end tell
    end if
    '''.format(title, message, "", sender)
    
    subprocess.run(['osascript', '-e', apple_script])

if __name__ == "__main__":
    colorama.init(autoreset=True)
    
    # Capture the current max 'date' from DB so we only listen for new arrivals
    last_date_fetched = get_current_max_date()

    read_messages = set()
    while True:
        # Get new messages since the last_date_fetched
        msgs = get_new_messages_since(last_date_fetched)

        if msgs:
            # Update last_date_fetched so we won't see these messages again
            # We'll use the largest date from the newly fetched messages.
            max_date_in_new_msgs = max(msg[0] for msg in msgs)
            if max_date_in_new_msgs > last_date_fetched:
                last_date_fetched = max_date_in_new_msgs

            # Process each new message
            for msg_date, text, sender in msgs:
                if (text, sender) not in read_messages:
                    print(f"{Fore.GREEN}New message from {sender}:{Style.RESET_ALL} {text}")

                    response = determine_importance(text)
                    if response['important']:
                        print(f"{Fore.YELLOW}{response['explanation']}{Style.RESET_ALL}")
                        send_notification(
                            title=f"Message from {sender}",
                            message=text,
                            sender=sender
                        )
                    else:
                        print(f"{Fore.BLUE}Message is not important{Style.RESET_ALL}")

                    read_messages.add((text, sender))

        print(f"{Fore.CYAN}Listening for new messages...{Style.RESET_ALL}")
        time.sleep(2)  # Check every 2 seconds
