import shareithub
import cloudscraper
import time
import threading
import datetime
import itertools
import sys
from fake_useragent import UserAgent
from colorama import init
from rich.console import Console
from rich.table import Table
from rich.progress import track
from shareithub import shareithub

shareithub()
init(autoreset=True)
console = Console()

position_url = "https://ceremony-backend.silentprotocol.org/ceremony/position"
ping_url = "https://ceremony-backend.silentprotocol.org/ceremony/ping"
token_file = "tokens.txt"

ua = UserAgent()  

def loading_animation(text="Processing"):
    for c in itertools.cycle(["|", "/", "-", "\\"]):
        sys.stdout.write(f"\r{Fore.CYAN}{text} {c} {Style.RESET_ALL}")
        sys.stdout.flush()
        time.sleep(0.2)

def load_tokens():
    try:
        with open(token_file, "r") as file:
            tokens = [line.strip() for line in file if line.strip()]
            if tokens:
                console.print(f"🎯 {len(tokens)} tokens loaded!\n")
            else:
                console.print("❌ No tokens found! Exiting...\n")
                sys.exit()
            return tokens
    except Exception as e:
        console.print(f"❌ Error loading tokens: {e}\n")
        return []

def get_scraper():
    return cloudscraper.create_scraper()

def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "*/*",
        "User-Agent": ua.random  
    }

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_position(scraper, token):
    try:
        response = scraper.get(position_url, headers=get_headers(token))
        if response.status_code == 200:
            data = response.json()
            return {"token": token[:6], "behind": data['behind'], "time_raiming": data['timeRemaining']}
        return {"token": token[:6], "error": f"Failed (Status {response.status_code})"}
    except Exception as e:
        return {"token": token[:6], "error": f"Error: {str(e)}"}

def ping_server(scraper, token):
    try:
        response = scraper.get(ping_url, headers=get_headers(token))
        if response.status_code == 200:
            data = response.json()
            return {"token": token[:6], "status": data}
        return {"token": token[:6], "error": f"Failed (Status {response.status_code})"}
    except Exception as e:
        return {"token": token[:6], "error": f"Error: {str(e)}"}

def run_automation(token):
    scraper = get_scraper()
    while True:

        sys.stdout.write(f"\r🔄 Checking position & ping for {token[:6]}... ")
        sys.stdout.flush()
        
        position_data = get_position(scraper, token)
        ping_data = ping_server(scraper, token)

        console.print(f"[cyan]Status for Token: {token[:6]}...[/cyan]")

        table = Table(show_lines=True)
        table.add_column("🔢 Token", style="cyan", justify="center")
        table.add_column("📌 Position", style="green", justify="center")
        table.add_column("⏳ Time Remaining", style="yellow", justify="center")
        table.add_column("📡 Ping Status", style="blue", justify="center")

        if "error" in position_data:
            table.add_row(position_data["token"], "[red]❌ Error[/red]", "-", "[red]❌ Error[/red]")
        else:
            table.add_row(position_data["token"], str(position_data["behind"]), str(position_data["time_raiming"]), str(ping_data["status"] if "status" in ping_data else "[red]❌ Error[/red]"))

        console.print(table)
        time.sleep(10)

def main():
    tokens = load_tokens()

    console.print("\n🔄 Processing tokens...\n")
    for _ in track(range(len(tokens)), description="Starting Automation..."):
        time.sleep(5)

    threads = []
    for token in tokens:
        thread = threading.Thread(target=run_automation, args=(token,))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
