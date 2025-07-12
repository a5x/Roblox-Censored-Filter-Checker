import os
import ctypes
import time
import asyncio
import aiohttp
from colorama import Fore, Style, init

init(autoreset=True)

ROBLOX_VALIDATE_URL = "https://auth.roblox.com/v1/usernames/validate?Username={}&Birthday=2000-01-01"
VALID_FILE = "valid.txt"
REQUEST_DELAY = 0.02
START_TIME = time.time()

# 🔗 Ton Webhook Discord ici
WEBHOOK_URL = "h"

def set_console_title(title):
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    except:
        pass

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

BANNER = Fore.RED + r"""
                 _____________   _______ ____  ____  __________ 
                / ____/ ____/ | / / ___// __ \/ __ \/ ____/ __ \
               / /   / __/ /  |/ /\__ \/ / / / /_/ / __/ / / / /
              / /___/ /___/ /|  /___/ / /_/ / _, _/ /___/ /_/ / 
              \____/_____/_/ |_//____/\____/_/ |_/_____/_____/  
                                                                                   
""" + Style.RESET_ALL + Fore.RED + "\n                              RBX Censored Filter Checker\n" + Style.RESET_ALL

stats = {
    "valid": 0,
    "taken": 0,
    "censored": 0,
    "unknown": 0,
    "total": 0,
    "checked": 0,
    "times": []
}

async def send_to_discord_webhook(session, message):
    if not WEBHOOK_URL:
        return
    payload = {"content": message}
    try:
        async with session.post(WEBHOOK_URL, json=payload) as response:
            if response.status not in (200, 204):
                print(Fore.RED + f"[WEBHOOK ERROR] HTTP {response.status}")
    except Exception as e:
        print(Fore.RED + f"[WEBHOOK EXCEPTION] {e}")

async def check_username(session, username):
    url = ROBLOX_VALIDATE_URL.format(username)
    try:
        start_time = time.time()
        async with session.get(url) as response:
            if response.status == 429:
                set_console_title("Rate limited... retrying in 5s")
                await asyncio.sleep(5)
                return await check_username(session, username)

            if response.status != 200:
                print(Fore.RED + f"[HTTP {response.status}] {username}")
                stats["unknown"] += 1
                return

            data = await response.json()
            code = data.get("code")
            stats["checked"] += 1

            elapsed_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - START_TIME))

            if stats["checked"] > 0 and len(stats["times"]) > 0:
                avg_time_per_request = sum(stats["times"]) / len(stats["times"])
            else:
                avg_time_per_request = 0.1

            remaining_time_seconds = (stats["total"] - stats["checked"]) * avg_time_per_request
            remaining_time = time.strftime("%H:%M:%S", time.gmtime(remaining_time_seconds))
            eta_timestamp = time.time() + remaining_time_seconds
            eta_formatted = time.strftime("%H:%M:%S", time.localtime(eta_timestamp))

            progress_percentage = (stats["checked"] / stats["total"]) * 100
            set_console_title(
                f"Progress: {progress_percentage:.2f}% | Checked {stats['checked']}/{stats['total']} | "
                f"Valid: {stats['valid']} | Elapsed: {elapsed_time} | Remaining: {remaining_time} | ETA: {eta_formatted}"
            )

            stats["times"].append(time.time() - start_time)

            if code == 0:
                stats["valid"] += 1
                print(Fore.GREEN + f"[VALID]    {username}")
                with open(VALID_FILE, "a") as f:
                    f.write(username + "\n")
            elif code == 1:
                stats["taken"] += 1
                print(Fore.LIGHTWHITE_EX + f"[TAKEN]    {username}")
            elif code == 2:
                stats["censored"] += 1
                print(Fore.RED + f"[CENSORED] {username}")
                await send_to_discord_webhook(session, f"-u {username}")
            else:
                stats["unknown"] += 1
                print(Fore.BLUE + f"[UNKNOWN:{code}] {username}")

    except Exception as e:
        print(Fore.MAGENTA + f"[ERROR]    {username}: {e}")
        stats["unknown"] += 1

    await asyncio.sleep(REQUEST_DELAY)

async def run_check(usernames):
    stats.update({"valid": 0, "taken": 0, "censored": 0, "unknown": 0, "checked": 0, "total": len(usernames)})
    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        for username in usernames:
            await check_username(session, username)

    elapsed_time = time.time() - start_time
    elapsed_formatted = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
    avg_time_per_username = elapsed_time / stats["checked"] if stats["checked"] > 0 else 0

    set_console_title(f"Valid: {stats['valid']} | Taken: {stats['taken']} | Elapsed: {elapsed_formatted}")

    print(Fore.BLUE + f"\nDone!\nChecked: {stats['checked']} | Valid: {stats['valid']} | Taken: {stats['taken']} | Censored: {stats['censored']} | Errors: {stats['unknown']}")
    print(Fore.YELLOW + f"Time taken: {elapsed_formatted} ({elapsed_time:.2f} seconds)" + Style.RESET_ALL)
    print(Fore.YELLOW + f"Average time per username: {avg_time_per_username:.2f} seconds" + Style.RESET_ALL)

    input(Fore.CYAN + "\nPress Enter to return to the menu..." + Style.RESET_ALL)
    clear_screen()
    print(BANNER)

def print_menu(current_delay):
    print(Fore.YELLOW + "\n=========== Options ===========" + Style.RESET_ALL)
    print("1 - Check from usernames.txt")
    print(f"2 - Modify Speed Checking")
    print("3 - Exit")

async def main():
    global REQUEST_DELAY
    clear_screen()
    print(BANNER)

    while True:
        print_menu(REQUEST_DELAY)
        choice = input(Fore.CYAN + "Choose an option: " + Style.RESET_ALL)

        if choice == "1":
            clear_screen()
            if not os.path.exists("usernames.txt"):
                print(Fore.RED + "File 'usernames.txt' not found!")
                continue
            with open("usernames.txt", "r") as f:
                usernames = f.read().splitlines()

            clear_choice = input(Fore.YELLOW + "Do you want to clear 'valid.txt' before checking? (y/n): " + Style.RESET_ALL).lower()
            if clear_choice == 'y':
                open(VALID_FILE, "w").close()
                print(Fore.GREEN + "'valid.txt' has been cleared.")
                await asyncio.sleep(1)

            await run_check(usernames)

        elif choice == "2":
            try:
                delay = float(input(Fore.CYAN + "New delay (e.g. 0.05): " + Style.RESET_ALL))
                REQUEST_DELAY = max(0.01, delay)
                print(Fore.GREEN + f"Delay set to {REQUEST_DELAY:.2f}s")
                await asyncio.sleep(1.5)
                clear_screen()
            except ValueError:
                print(Fore.RED + "Invalid number.")

        elif choice == "3":
            print(Fore.GREEN + "Goodbye!")
            break
        else:
            print(Fore.RED + "Invalid option.")

if __name__ == "__main__":
    asyncio.run(main())
