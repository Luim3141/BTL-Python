"""
Part II.2: Lookup script to query player data from Flask API
Usage:
    python lookup.py --name <player_name>
    python lookup.py --club <club_name>
    python lookup.py --name "Mohamed Salah" --club "Liverpool"
"""

import requests
import pandas as pd
import argparse
import sys
import os
from tabulate import tabulate

# API Configuration
API_BASE_URL = "http://127.0.0.1:5000"

def print_separator():
    """Print a separator line"""
    print("=" * 100)

def query_player(player_name):
    """
    Query player data from API

    Args:
        player_name: Name of the player

    Returns:
        dict: API response data
    """
    try:
        url = f"{API_BASE_URL}/api/player/{player_name}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            error_data = response.json()
            print(f"\n❌ Error: {error_data.get('message', 'Player not found')}")
            if 'suggestion' in error_data:
                print(f"💡 {error_data['suggestion']}")
            return None
        else:
            print(f"\n❌ Error: Server returned status code {response.status_code}")
            return None

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API server")
        print("💡 Make sure the Flask API is running (python flask_api.py)")
        return None
    except requests.exceptions.Timeout:
        print("\n❌ Error: Request timeout")
        return None
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None

def query_club(club_name):
    """
    Query club data from API

    Args:
        club_name: Name of the club

    Returns:
        dict: API response data
    """
    try:
        url = f"{API_BASE_URL}/api/club/{club_name}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            error_data = response.json()
            print(f"\n❌ Error: {error_data.get('message', 'Club not found')}")
            if 'available_clubs' in error_data:
                print(f"\n📋 Available clubs:")
                for club in error_data['available_clubs']:
                    print(f"   • {club}")
            return None
        else:
            print(f"\n❌ Error: Server returned status code {response.status_code}")
            return None

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API server")
        print("💡 Make sure the Flask API is running (python flask_api.py)")
        return None
    except requests.exceptions.Timeout:
        print("\n❌ Error: Request timeout")
        return None
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return None

def format_table_display(data, max_cols=10):
    """
    Format data for pretty table display

    Args:
        data: List of dictionaries
        max_cols: Maximum columns to display

    Returns:
        DataFrame formatted for display
    """
    df = pd.DataFrame(data)

    # Select important columns first
    priority_cols = ['Player', 'Team', 'Pos', 'Age', 'Standard_Min',
                     'Standard_Gls', 'Standard_Ast', 'Standard_xG',
                     'Standard_xAG', 'Transfer_Value_2024_25']

    # Get existing priority columns
    display_cols = [col for col in priority_cols if col in df.columns]

    # Add remaining columns if space allows
    remaining_cols = [col for col in df.columns if col not in display_cols]
    display_cols.extend(remaining_cols[:max(0, max_cols - len(display_cols))])

    return df[display_cols]

def display_player_data(data):
    """Display player data in table format"""
    if 'player' in data:
        # Single player
        player_data = [data['player']]
        df = pd.DataFrame(player_data)

        print(f"\n{'='*100}")
        print(f"🔍 Player Information: {data['player']['Player']}")
        print(f"{'='*100}\n")

        # Display as transposed table (vertical)
        for col in df.columns:
            value = df[col].iloc[0]
            print(f"{col:35s}: {value}")

        return df

    elif 'players' in data:
        # Multiple players (partial match)
        players_data = data['players']
        df = format_table_display(players_data)

        print(f"\n{'='*100}")
        print(f"🔍 Found {len(players_data)} players")
        print(f"{'='*100}\n")

        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))

        return pd.DataFrame(players_data)

    return None

def display_club_data(data):
    """Display club data in table format"""
    if 'players' in data:
        players_data = data['players']
        df = format_table_display(players_data, max_cols=12)

        print(f"\n{'='*100}")
        print(f"🏆 Club: {data['club']}")
        print(f"👥 Total Players: {data['total_players']}")
        print(f"{'='*100}\n")

        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))

        return pd.DataFrame(players_data)

    return None

def save_to_csv(df, filename):
    """
    Save DataFrame to CSV file

    Args:
        df: DataFrame to save
        filename: Output filename
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, filename)

        df.to_csv(filepath, index=False, encoding='utf-8')

        print(f"\n{'='*100}")
        print(f"✅ Data saved to: {filepath}")
        print(f"📊 Total rows: {len(df)}")
        print(f"📋 Total columns: {len(df.columns)}")
        print(f"{'='*100}\n")

    except Exception as e:
        print(f"\n❌ Error saving CSV: {str(e)}\n")

def sanitize_filename(name):
    """
    Sanitize filename by removing invalid characters

    Args:
        name: Original filename

    Returns:
        str: Sanitized filename
    """
    # Replace spaces with underscores
    name = name.replace(' ', '_')

    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '')

    return name

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Query Premier League player statistics from API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python lookup.py --name "Mohamed Salah"
  python lookup.py --club "Liverpool"
  python lookup.py --name "Salah"
  python lookup.py --club "Manchester City"
        """
    )

    parser.add_argument('--name', type=str, help='Player name to search')
    parser.add_argument('--club', type=str, help='Club name to search')

    args = parser.parse_args()

    # Check if at least one argument is provided
    if not args.name and not args.club:
        parser.print_help()
        print("\n❌ Error: Please provide either --name or --club argument\n")
        sys.exit(1)

    print_separator()
    print("Premier League Player Statistics Lookup")
    print_separator()

    result_df = None
    output_filename = None

    # Query by player name
    if args.name:
        print(f"\n🔍 Searching for player: {args.name}...")
        data = query_player(args.name)

        if data and data.get('success'):
            result_df = display_player_data(data)
            output_filename = f"{sanitize_filename(args.name)}_stats.csv"

    # Query by club name
    elif args.club:
        print(f"\n🔍 Searching for club: {args.club}...")
        data = query_club(args.club)

        if data and data.get('success'):
            result_df = display_club_data(data)
            output_filename = f"{sanitize_filename(args.club)}_players.csv"

    # Save to CSV if data was retrieved
    if result_df is not None and output_filename:
        save_to_csv(result_df, output_filename)
    else:
        print("\n⚠ No data to save\n")
        sys.exit(1)

if __name__ == "__main__":
    main()