import time
from notifications.telegram import notify, getUpdates

last_update_id = None

def wait_for_user_action(timeout=600, retry_count=0):

    global last_update_id

    notify(
        f"⚠️ Bot paused (retry {retry_count})\n\n"
        "0 = refresh page\n"
        "1 = retry action\n\n"
        "Waiting 10 minutes..."
    )

    start = time.time()

    while time.time() - start < timeout:

        r = getUpdates()

        print("acá r", r)

        for update in r.get("result", []):

            update_id = update["update_id"]

            if last_update_id and update_id <= last_update_id:
                continue

            last_update_id = update_id

            text = update["message"]["text"].strip()

            if text == "1":
                notify("🔁 Retrying action")
                return "retry"

            if text == "0":
                notify("🔄 Refreshing page")
                return "refresh"

        time.sleep(5)

    notify("❌ Timeout reached. Bot shutting down.")
    return "abort"