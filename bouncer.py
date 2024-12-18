import sqlite3
import time
import os
import requests
import colorama
from colorama import Fore, Style
import json
import subprocess

################################## CUSTOMIZE YOUR BOUNCER ##################################

# Give your bouncer a secret word to look out for:
SHIBBOLETH = "gazooga"

# Give your bouncer some guidance on what's important for you:
GATEKEEPER_PROMPT = f"""
You are a helpful assistant that determines the importance of messages.

You can use your own judgement, but texts that are important are usually:
<rules>
- Time sensitive/urgent. For example, if the message is about a deadline, or includes a time constraint.
- Serious sounding. Like 'I'm in trouble' or 'Hey can we talk'
- Anything where the sender is asking for help.
- Anything where the sender includes the word '{SHIBBOLETH}' (case insensitive)
</rules>
"""
############################################################################################


DB_PATH = f"/Users/{os.getenv('USER')}/Library/Messages/chat.db"
MODEL = "llama3.2"
INTERVAL_SECONDS = 2

""" 
Health check: Ollama server is running and accessible
"""
def check_ollama_server():
    try:
        response = requests.get("http://localhost:11434")
        if response.status_code != 200:
            raise ConnectionError
    except (requests.exceptions.ConnectionError, ConnectionError):
        print(f"{Fore.RED}Error: Ollama server is not running{Style.RESET_ALL}")
        print("\nPlease install Ollama with `brew install ollama` and start it with `ollama serve`. \n\nThen run `ollama run llama3.2` to make sure llama3.2 is installed (this is configured in the MODEL variable).")
        exit(1)


""" 
Checks if the Messages database is accessible
"""
def check_db_access():
    if not os.path.isfile(DB_PATH):
        print(f"{Fore.RED}Error: Messages database not found at '{DB_PATH}'{Style.RESET_ALL}")
        exit(1)
    
    try:
        uri = f"file:{DB_PATH}?mode=ro"
        sqlite3.connect(uri, uri=True)
    except sqlite3.OperationalError:
        print(f"{Fore.RED}Error: Cannot access Messages database{Style.RESET_ALL}")
        print(f"Please grant Full Disk Access permission to the application that is running this script.")
        
        # Open System Settings to Full Disk Access
        subprocess.run([
            'open', 
            'x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles'
        ])
        exit(1)


""" 
Returns the maximum date value (integer) found in the 'message' table.
If the table is empty, returns 0.
"""
def get_current_max_date():
    if not os.path.isfile(DB_PATH):
        raise FileNotFoundError(f"Database not found at '{DB_PATH}'")

    uri = f"file:{DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    c = conn.cursor()
    c.execute("SELECT MAX(date) FROM message")
    result = c.fetchone()
    conn.close()

    return result[0] if result and result[0] else 0


""" 
Fetches messages with a 'date' > threshold_date.
Only new messages that arrived after threshold_date will appear.
"""
def get_new_messages_since(threshold_date):
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


""" 
Sends a request to the local AI to determine if a message is important.
"""
def determine_importance(text):
    prompt = f"""
    {GATEKEEPER_PROMPT}

    Text: {text}
    """

    request_payload = {
        "model": MODEL,
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

""" 
Sends a system notification using osascript (macOS only) with a button to open iMessage
"""
def send_notification(title, message, sender):
    """
    Sends a system notification using osascript (macOS only) with a button to open iMessage
    """
    # Escape double quotes in the message and title
    message = message.replace('"', '\\"')
    title = title.replace('"', '\\"')
    sender = sender.replace('"', '\\"')
    
    apple_script = '''
    display alert "{}" message "{}" buttons {{"Ignore", "Open iMessage"}} default button "Open iMessage"
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
    
    # Add initial checks
    check_ollama_server()
    check_db_access()
    
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

            # Process new message
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
        time.sleep(INTERVAL_SECONDS) 
