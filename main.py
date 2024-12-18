import sqlite3
import time
import os

DB_PATH = "/Users/charlie/Library/Messages/chat.db"
print(os.path.isfile(DB_PATH))

def get_unread_messages():
    import os
    import sqlite3

    if not os.path.isfile(DB_PATH):
        raise FileNotFoundError(f"Database not found at '{DB_PATH}'")

    # OPEN IN READ-ONLY MODE
    uri = f"file:{DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    c = conn.cursor()
    query = """
    SELECT text, handle.id 
    FROM message
    JOIN handle ON message.handle_id = handle.rowid
    WHERE is_read = 0 AND text IS NOT NULL
    ORDER BY date DESC;
    """
    c.execute(query)
    results = c.fetchall()
    conn.close()
    return results

if __name__ == "__main__":
    known = set()
    while True:
        msgs = get_unread_messages()
        # Filter out messages we've already seen
        new_msgs = [m for m in msgs if m not in known]
        if new_msgs:
            for text, sender in new_msgs:
                # Pass message 'text' to AI for processing
                print(f"New message from {sender}: {text}")
                known.add((text, sender))
        print(f"Checking... {len(known)} known messages")
        time.sleep(10)  # Check every 10 seconds
