import shareithub
import cloudscraper
import time
import sys
import json
from shareithub import shareithub
from concurrent.futures import ThreadPoolExecutor
from fake_useragent import UserAgent
from rich.console import Console
from rich.table import Table
from rich.progress import track
import requests

console = Console()

shareithub()
position_url = "https://ceremony-backend.silentprotocol.org/ceremony/position"
ping_url = "https://ceremony-backend.silentprotocol.org/ceremony/ping"
token_file = "tokens.txt"
config_file = "config.json"

ua = UserAgent()  # Initialize fake_useragent

def load_config():
    """Load configuration from file."""
    try:
        with open(config_file, "r") as file:
            config = json.load(file)
            return config
    except Exception as e:
        console.print(f"[red]❌ Error loading config: {e}[/red]\n")
        sys.exit()

def load_tokens():
    """Load tokens from file."""
    try:
        with open(token_file, "r") as file:
            tokens = [line.strip() for line in file if line.strip()]
            if tokens:
                console.print(f"[cyan]🎯 {len(tokens)} tokens loaded![/cyan]\n")
            else:
                console.print("[red]❌ No tokens found! Exiting...[/red]\n")
                sys.exit()
            return tokens
    except Exception as e:
        console.print(f"[red]❌ Error loading tokens: {e}[/red]\n")
        sys.exit()

def get_scraper():
    """Create scraper with Cloudflare bypass."""
    return cloudscraper.create_scraper()

def get_headers(token):
    """Return headers with token and random user-agent."""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "*/*",
        "User-Agent": ua.random
    }

def get_position(scraper, token):
    """Get queue position for a specific token."""
    try:
        response = scraper.get(position_url, headers=get_headers(token))
        if response.status_code == 200:
            data = response.json()
            return {"token": token[:6], "behind": data.get('behind', '?'), "time_remaining": data.get('timeRemaining', '?')}
        return {"token": token[:6], "error": f"Failed (Status {response.status_code})"}
    except Exception as e:
        return {"token": token[:6], "error": f"Error: {str(e)}"}

def ping_server(scraper, token):
    """Ping the server with a specific token."""
    try:
        response = scraper.get(ping_url, headers=get_headers(token))
        if response.status_code == 200:
            data = response.json()
            return {"token": token[:6], "status": data}
        return {"token": token[:6], "error": f"Failed (Status {response.status_code})"}
    except Exception as e:
        return {"token": token[:6], "error": f"Error: {str(e)}"}

def send_telegram_message(bot_token, chat_id, message):
    """Send a message to a Telegram chat."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            console.print(f"[red]❌ Failed to send message: {response.text}[/red]\n")
    except Exception as e:
        console.print(f"[red]❌ Error sending message: {str(e)}[/red]\n")

def run_automation(token, bot_token, chat_id):
    """Main loop to check position and ping continuously."""
    scraper = get_scraper()
    while True:
        position_data = get_position(scraper, token)
        ping_data = ping_server(scraper, token)

        # Header token
        console.print(f"\n[cyan]Status for Token: {token[:6]}[/cyan]")

        # Create table
        table = Table(show_lines=True)
        table.add_column("🔢 Token", style="cyan", justify="center")
        table.add_column("📌 Position", style="green", justify="center")
        table.add_column("⏳ Time Remaining", style="yellow", justify="center")
        table.add_column("📡 Ping Status", style="blue", justify="center")

        if "error" in position_data:
            table.add_row(position_data["token"], "[red]❌ Error[/red]", "-", "[red]" + position_data["error"] + "[/red]")
        else:
            table.add_row(position_data["token"], str(position_data["behind"]), str(position_data["time_remaining"]),
                          str(ping_data["status"] if "status" in ping_data else "[red]❌ Error[/red]"))

        # Display table
        console.print(table)

        # Send Telegram update
        message = f"Token: {position_data['token']}\nPosition: {position_data.get('behind', '-')}\nTime Remaining: {position_data.get('time_remaining', '-')}\nPing Status: {ping_data.get('status', 'Error')}"
        send_telegram_message(bot_token, chat_id, message)

        # Speed up the process with shorter sleep
        time.sleep(3)  # Originally 10 seconds, now 3 seconds

def main():
    config = load_config()
    tokens = load_tokens()

    bot_token = config["TELEGRAM_BOT_TOKEN"]
    chat_id = config["TELEGRAM_CHAT_ID"]

    console.print("\n🔄 Processing tokens...\n")
    for _ in track(range(len(tokens)), description="Starting Automation..."):
        time.sleep(0.2)  # Speed up progress bar

    # Use ThreadPoolExecutor for faster and more efficient processing
    with ThreadPoolExecutor(max_workers=len(tokens)) as executor:
        executor.map(lambda token: run_automation(token, bot_token, chat_id), tokens)

if __name__ == "__main__":
    main()
