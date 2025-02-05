import shareithub
import cloudscraper
import time
import threading
import datetime
import sys
from shareithub import shareithub
from concurrent.futures import ThreadPoolExecutor
from fake_useragent import UserAgent
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()

shareithub()
position_url = "https://ceremony-backend.silentprotocol.org/ceremony/position"
ping_url = "https://ceremony-backend.silentprotocol.org/ceremony/ping"
token_file = "tokens.txt"

ua = UserAgent()  # Inisialisasi fake_useragent

def load_tokens():
    """Memuat token dari file."""
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
        return []

def get_scraper():
    """Membuat scraper dengan Cloudflare bypass."""
    return cloudscraper.create_scraper()

def get_headers(token):
    """Mengembalikan headers dengan token dan user-agent acak."""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "*/*",
        "User-Agent": ua.random
    }

def get_position(scraper, token):
    """Mengambil posisi antrean untuk token tertentu."""
    try:
        response = scraper.get(position_url, headers=get_headers(token))
        if response.status_code == 200:
            data = response.json()
            return {"token": token[:6], "behind": data.get('behind', '?'), "time_remaining": data.get('timeRemaining', '?')}
        return {"token": token[:6], "error": f"Failed (Status {response.status_code})"}
    except Exception as e:
        return {"token": token[:6], "error": f"Error: {str(e)}"}

def ping_server(scraper, token):
    """Melakukan ping ke server dengan token tertentu."""
    try:
        response = scraper.get(ping_url, headers=get_headers(token))
        if response.status_code == 200:
            data = response.json()
            return {"token": token[:6], "status": data}
        return {"token": token[:6], "error": f"Failed (Status {response.status_code})"}
    except Exception as e:
        return {"token": token[:6], "error": f"Error: {str(e)}"}

def run_automation(token):
    """Loop utama untuk mengecek posisi dan ping secara terus-menerus."""
    scraper = get_scraper()
    while True:
        position_data = get_position(scraper, token)
        ping_data = ping_server(scraper, token)

        # Header token
        console.print(f"\n[cyan]Status for Token: {token[:6]}[/cyan]")

        # Membuat tabel
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

        # Menampilkan tabel
        console.print(table)
        
        # Mempercepat proses dengan sleep lebih singkat
        time.sleep(3)  # Awalnya 10 detik, sekarang 3 detik

def main():
    tokens = load_tokens()

    console.print("\n🔄 Processing tokens...\n")
    for _ in track(range(len(tokens)), description="Starting Automation..."):
        time.sleep(0.2)  # Mempercepat progress bar

    # Menggunakan ThreadPoolExecutor agar lebih cepat dan efisien
    with ThreadPoolExecutor(max_workers=len(tokens)) as executor:
        executor.map(run_automation, tokens)

if __name__ == "__main__":
    main()
