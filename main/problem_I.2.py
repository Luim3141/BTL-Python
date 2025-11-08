"""
Part I.2: Collect transfer values for Premier League players from footballtransfers.com
Reads from results.csv (from Part I.1) and saves to transfer_values.csv
IMPROVED VERSION with better CAPTCHA handling and alternative data sources
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import re
import requests

#
# 1. Setup ChromeDriver with enhanced anti-detection
#
def setup_driver():
    """Initialize Chrome driver with options to avoid detection"""
    options = webdriver.ChromeOptions()

    # Enhanced anti-detection measures
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')

    # Rotate user agents
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    options.add_argument(f'user-agent={random.choice(user_agents)}')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Execute scripts to hide webdriver property
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": random.choice(user_agents)
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

#
# 2. Alternative: Use Transfermarkt as backup source
#
def get_transfermarkt_value(player_name, team_name):
    """
    Backup method: Get value from Transfermarkt using requests
    This is more reliable and less likely to trigger CAPTCHA
    """
    try:
        # Clean player name
        search_name = player_name.lower().replace(' ', '-')

        # Search URL for Transfermarkt
        search_url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={player_name.replace(' ', '+')}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        response = requests.get(search_url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for market value
            value_elem = soup.find('td', class_='rechts hauptlink')
            if value_elem:
                value = value_elem.get_text(strip=True)
                return value

        return 'N/A'
    except:
        return 'N/A'

#
# 3. Improved search with better CAPTCHA detection
#
def search_player_value(driver, player_name, team_name, use_backup=False):
    """
    Search for a player's transfer value

    Args:
        driver: Selenium WebDriver instance
        player_name: Name of the player
        team_name: Team name for verification
        use_backup: If True, use Transfermarkt instead

    Returns:
        str: Transfer value or 'N/A' if not found
    """

    # Use backup source if requested
    if use_backup:
        print(f"  Using Transfermarkt for: {player_name}...", end=' ')
        value = get_transfermarkt_value(player_name, team_name)
        if value != 'N/A':
            print(f"✓ Found: {value}")
        else:
            print("✗ Not found")
        return value

    try:
        # Clean player name
        clean_name = player_name.strip()

        # Method 1: Try direct player page URL construction
        # footballtransfers.com uses format: /en/players/firstname-lastname/club
        name_parts = clean_name.lower().split()
        if len(name_parts) >= 2:
            url_name = '-'.join(name_parts)
            team_slug = team_name.lower().replace(' ', '-')
            direct_url = f"https://www.footballtransfers.com/en/players/{url_name}"

            try:
                driver.get(direct_url)
                time.sleep(random.uniform(3, 5))

                # Check if page loaded successfully (not 404)
                if "404" not in driver.title and "not found" not in driver.page_source.lower()[:1000]:
                    soup = BeautifulSoup(driver.page_source, 'html.parser')

                    # Extract value from player page
                    value = extract_value_from_page(soup)
                    if value:
                        print(f"  {clean_name}: ✓ {value}")
                        return value
            except:
                pass

        # Method 2: Use search if direct URL fails
        print(f"  Searching: {clean_name}...", end=' ')

        search_query = clean_name.replace(' ', '+')
        search_url = f"https://www.footballtransfers.com/en/search?q={search_query}"

        driver.get(search_url)
        time.sleep(random.uniform(3, 5))

        # Check for CAPTCHA immediately
        if check_for_captcha(driver):
            print("⚠ CAPTCHA detected!")
            return 'CAPTCHA'

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Look for player links in search results
        player_links = soup.find_all('a', href=re.compile(r'/en/players/[^/]+/?$'))

        if not player_links:
            print("✗ No results")
            return 'N/A'

        # Try first result
        first_link = player_links[0]
        player_url = first_link.get('href')
        if not player_url.startswith('http'):
            player_url = f"https://www.footballtransfers.com{player_url}"

        driver.get(player_url)
        time.sleep(random.uniform(3, 5))

        # Check for CAPTCHA again
        if check_for_captcha(driver):
            print("⚠ CAPTCHA detected!")
            return 'CAPTCHA'

        player_soup = BeautifulSoup(driver.page_source, 'html.parser')
        value = extract_value_from_page(player_soup)

        if value:
            print(f"✓ {value}")
            return value
        else:
            print("✗ Not found")
            return 'N/A'

    except Exception as e:
        print(f"✗ Error: {str(e)[:50]}")
        return 'N/A'

def extract_value_from_page(soup):
    """Extract transfer value from a player page"""

    # Try multiple methods to find value
    methods = [
        # Method 1: Look for specific value classes
        lambda: soup.find('div', class_=re.compile(r'.*market.*value.*', re.I)),
        lambda: soup.find('span', class_=re.compile(r'.*value.*', re.I)),

        # Method 2: Look for text with currency symbols
        lambda: soup.find(string=re.compile(r'€\s*[\d.]+\s*[Mm]')),
        lambda: soup.find(string=re.compile(r'\$\s*[\d.]+\s*[Mm]')),
        lambda: soup.find(string=re.compile(r'£\s*[\d.]+\s*[Mm]')),

        # Method 3: Look in data attributes
        lambda: soup.find(attrs={'data-value': re.compile(r'[\d.]+')})
    ]

    for method in methods:
        try:
            result = method()
            if result:
                if hasattr(result, 'get_text'):
                    text = result.get_text(strip=True)
                else:
                    text = str(result).strip()

                # Extract value with regex
                match = re.search(r'[€$£]\s*[\d.]+\s*[MmKk]', text)
                if match:
                    return match.group(0)
        except:
            continue

    return None

#
# 4. Enhanced CAPTCHA detection
#
def check_for_captcha(driver):
    """Check if CAPTCHA is present on the page"""
    try:
        page_source = driver.page_source.lower()
        captcha_indicators = [
            'captcha' in page_source,
            'recaptcha' in page_source,
            'cloudflare' in driver.title.lower(),
            'just a moment' in page_source,
            'checking your browser' in page_source,
            'verify you are human' in page_source
        ]
        return any(captcha_indicators)
    except:
        return False

def wait_for_captcha_solve(driver):
    """Wait for user to solve CAPTCHA"""
    print("\n" + "="*60)
    print("⚠ CAPTCHA DETECTED!")
    print("="*60)
    print("Please solve the CAPTCHA in the browser window.")
    print("The script will automatically continue when solved.")
    print("="*60)

    # Wait for CAPTCHA to disappear
    max_wait = 300  # 5 minutes max
    start_time = time.time()

    while time.time() - start_time < max_wait:
        time.sleep(5)
        if not check_for_captcha(driver):
            print("✓ CAPTCHA solved! Continuing...\n")
            return True
        print(".", end='', flush=True)

    print("\n⚠ Timeout waiting for CAPTCHA. Switching to backup method.")
    return False

#
# 5. Main execution with improved error handling
#
def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "results.csv")
    output_file = os.path.join(script_dir, "transfer_values.csv")
    checkpoint_file = os.path.join(script_dir, "transfer_checkpoint.csv")

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return

    # Read player data
    print("Reading player data from results.csv...")
    df = pd.read_csv(input_file)
    print(f"Found {len(df)} players to process\n")

    # Check for checkpoint file (resume capability)
    start_idx = 0
    transfer_data = []

    if os.path.exists(checkpoint_file):
        print("Found checkpoint file. Do you want to resume? (y/n): ", end='')
        if input().lower() == 'y':
            checkpoint_df = pd.read_csv(checkpoint_file)
            transfer_data = checkpoint_df.to_dict('records')
            start_idx = len(transfer_data)
            print(f"Resuming from player {start_idx + 1}\n")

    # Initialize driver
    driver = setup_driver()

    try:
        for idx in range(start_idx, len(df)):
            row = df.iloc[idx]
            player_name = row['Player']
            team_name = row.get('Team', 'Unknown')

            print(f"[{idx + 1}/{len(df)}]", end=' ')

            # Always try FootballTransfers first (use_backup=False)
            transfer_value = search_player_value(driver, player_name, team_name, use_backup=False)

            # Handle CAPTCHA - switch to Transfermarkt for THIS player only
            if transfer_value == 'CAPTCHA':
                print("⚠ CAPTCHA! Switching to Transfermarkt for this player...")
                print(f"[{idx + 1}/{len(df)}] Using Transfermarkt for: {player_name}...", end=' ')
                transfer_value = get_transfermarkt_value(player_name, team_name)
                if transfer_value != 'N/A':
                    print(f"✓ {transfer_value}")
                else:
                    print("✗ Not found")

                # Add extra delay before returning to FootballTransfers
                print("  Waiting before returning to FootballTransfers...")
                time.sleep(random.uniform(10, 20))

            # Store result
            transfer_data.append({
                'Player': player_name,
                'Team': team_name,
                'Transfer_Value_2024_25': transfer_value
            })

            # Save checkpoint every 10 players
            if (idx + 1) % 10 == 0:
                checkpoint_df = pd.DataFrame(transfer_data)
                checkpoint_df.to_csv(checkpoint_file, index=False, encoding='utf-8')
                print(f"  [Checkpoint saved]")

            # Random delay between requests
            time.sleep(random.uniform(1, 3))

            # Longer pause every 15 players
            if (idx + 1) % 15 == 0:
                pause_time = random.uniform(15, 30)
                print(f"\n--- Break ({pause_time:.1f}s) ---\n")
                time.sleep(pause_time)

        # Save final results
        transfer_df = pd.DataFrame(transfer_data)
        transfer_df.to_csv(output_file, index=False, encoding='utf-8')

        # Remove checkpoint file
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)

        print(f"\n{'='*60}")
        print(f"✓ Transfer values saved to: {output_file}")
        print(f"{'='*60}")
        print(f"Total players: {len(transfer_data)}")
        print(f"Values found: {sum(1 for d in transfer_data if d['Transfer_Value_2024_25'] != 'N/A')}")
        print(f"Not found: {sum(1 for d in transfer_data if d['Transfer_Value_2024_25'] == 'N/A')}")

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted. Saving progress...")
        transfer_df = pd.DataFrame(transfer_data)
        transfer_df.to_csv(checkpoint_file, index=False, encoding='utf-8')
        print(f"Progress saved to: {checkpoint_file}")
        print("Run script again to resume.")

    finally:
        driver.quit()

if __name__ == "__main__":
    print("="*60)
    print("Transfer Value Scraper - Part I.2 (SMART SWITCH)")
    print("="*60)
    print("\nCAPTCHA Handling Strategy:")
    print("  ✓ Try FootballTransfers first for each player")
    print("  ✓ If CAPTCHA → Switch to Transfermarkt for that player only")
    print("  ✓ Return to FootballTransfers for next player")
    print("  ✓ Resume capability via checkpoint file")
    print("\n" + "="*60 + "\n")

    # Install requests if not available
    try:
        import requests
    except ImportError:
        print("Installing requests library...")
        os.system("pip install requests")
        import requests

    main()