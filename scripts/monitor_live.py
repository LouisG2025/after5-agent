import sys
import os
import time

# Add the project root to sys.path so we can import 'app'
sys.path.append(os.getcwd())

from app.tracker import AlbertTracker
from app.supabase_client import supabase_client

def fetch_live_logs(phone: str, limit: int = 20, watch: bool = False):
    print(f"📡 Connecting to Supabase for {phone}...")
    tracker = AlbertTracker()
    
    try:
        lead = tracker.get_lead_by_phone(phone)
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    if not lead:
        print(f"❌ Lead with phone {phone} not found in Supabase.")
        return

    lead_id = lead["id"]
    print(f"✅ Monitoring: {lead.get('first_name', 'Unknown')} {lead.get('last_name', '')}")
    print(f"📊 Signal Score: {lead.get('signal_score', 0)}/10 | Outcome: {lead.get('outcome', 'In Progress')}")
    print("-" * 50)

    last_seen_id = None

    def print_messages(msg_limit, reset=False):
        nonlocal last_seen_id
        try:
            query = supabase_client.client.table("messages")\
                .select("*")\
                .eq("lead_id", lead_id)\
                .order("created_at", desc=True)\
                .limit(msg_limit)
            
            result = query.execute()
            messages = result.data
            
            if not messages:
                if reset: print("📭 No messages yet.")
                return

            # Reverse to show chronological order
            new_msgs = []
            for msg in reversed(messages):
                if last_seen_id is None or msg["id"] > last_seen_id:
                    new_msgs.append(msg)
            
            for msg in new_msgs:
                direction = "👤 Lead" if msg["direction"] == "inbound" else "🤖 Albert"
                time_str = msg.get("created_at", "").split(".")[0].replace("T", " ")
                print(f"[{time_str}] {direction}: {msg['content']}")
                last_seen_id = msg["id"]
                
        except Exception as e:
            print(f"❌ Error: {e}")

    # Initial fetch
    print(f"📜 Latest History (Last {limit}):")
    print_messages(limit, reset=True)

    if watch:
        print("\n👀 WATCH MODE ACTIVE (Press Ctrl+C to stop)")
        print("Waiting for new messages...")
        try:
            while True:
                time.sleep(2) # Poll every 2 seconds
                print_messages(5)
        except KeyboardInterrupt:
            print("\n🛑 Stopped monitoring.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Monitor Albert Live Chats")
    parser.add_get_lead_status = parser.add_argument("phone", help="Phone number in format 'whatsapp:+123456789'")
    parser.add_argument("--limit", type=int, default=20, help="Number of messages to show initially")
    parser.add_argument("--watch", action="store_true", help="Keep running and watch for new messages")
    
    # Simple direct sys.argv fallback if parser is too complex for user
    phone = sys.argv[1] if len(sys.argv) > 1 else "whatsapp:+918160178327"
    watch_mode = "--watch" in sys.argv
    limit_val = 20
    
    # Extract limit if exists
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i+1 < len(sys.argv):
            limit_val = int(sys.argv[i+1])

    fetch_live_logs(phone, limit=limit_val, watch=watch_mode)
