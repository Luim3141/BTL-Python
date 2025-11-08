"""
Part II.1: Flask RESTful API for querying player statistics
Endpoints:
  - /api/player/<player_name> : Get all stats for a specific player
  - /api/club/<club_name> : Get all stats for players in a club
"""

from flask import Flask, jsonify, request
import pandas as pd
import os

app = Flask(__name__)

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYER_STATS_FILE = os.path.join(SCRIPT_DIR, "results.csv")
TRANSFER_VALUES_FILE = os.path.join(SCRIPT_DIR, "transfer_values.csv")

# Load data into memory
player_stats_df = None
transfer_values_df = None

def load_data():
    """Load CSV data into pandas DataFrames"""
    global player_stats_df, transfer_values_df

    try:
        if os.path.exists(PLAYER_STATS_FILE):
            player_stats_df = pd.read_csv(PLAYER_STATS_FILE)
            print(f"✓ Loaded {len(player_stats_df)} players from {PLAYER_STATS_FILE}")
        else:
            print(f"⚠ Warning: {PLAYER_STATS_FILE} not found")
            player_stats_df = pd.DataFrame()

        if os.path.exists(TRANSFER_VALUES_FILE):
            transfer_values_df = pd.read_csv(TRANSFER_VALUES_FILE)
            print(f"✓ Loaded {len(transfer_values_df)} transfer values from {TRANSFER_VALUES_FILE}")
        else:
            print(f"⚠ Warning: {TRANSFER_VALUES_FILE} not found")
            transfer_values_df = pd.DataFrame()

    except Exception as e:
        print(f"Error loading data: {str(e)}")
        player_stats_df = pd.DataFrame()
        transfer_values_df = pd.DataFrame()

def merge_player_data(stats_data):
    """Merge player stats with transfer values"""
    if transfer_values_df is not None and not transfer_values_df.empty:
        # Merge on Player name
        merged = pd.merge(
            stats_data,
            transfer_values_df[['Player', 'Transfer_Value_2024_25']],
            on='Player',
            how='left'
        )
        return merged
    return stats_data

@app.route('/')
def index():
    """API documentation endpoint"""
    return jsonify({
        'message': 'Premier League Player Statistics API',
        'version': '1.0',
        'endpoints': {
            '/api/player/<player_name>': {
                'method': 'GET',
                'description': 'Get all statistics for a specific player',
                'example': '/api/player/Mohamed Salah'
            },
            '/api/club/<club_name>': {
                'method': 'GET',
                'description': 'Get all statistics for players in a specific club',
                'example': '/api/club/Liverpool'
            },
            '/api/stats': {
                'method': 'GET',
                'description': 'Get statistics summary',
                'example': '/api/stats'
            }
        },
        'total_players': len(player_stats_df) if player_stats_df is not None else 0,
        'total_clubs': player_stats_df['Team'].nunique() if player_stats_df is not None and 'Team' in player_stats_df.columns else 0
    })

@app.route('/api/player/<player_name>', methods=['GET'])
def get_player(player_name):
    """
    Get all statistics for a specific player

    Args:
        player_name: Name of the player (case-insensitive)

    Returns:
        JSON with player statistics and transfer value
    """
    if player_stats_df is None or player_stats_df.empty:
        return jsonify({
            'error': 'No data available',
            'message': 'Player statistics database is empty'
        }), 500

    # Case-insensitive search
    player_data = player_stats_df[
        player_stats_df['Player'].str.lower() == player_name.lower()
        ]

    if player_data.empty:
        # Try partial match
        player_data = player_stats_df[
            player_stats_df['Player'].str.contains(player_name, case=False, na=False)
        ]

        if player_data.empty:
            return jsonify({
                'error': 'Player not found',
                'message': f'No player found with name: {player_name}',
                'suggestion': 'Try using exact player name or check spelling'
            }), 404

    # Merge with transfer values
    merged_data = merge_player_data(player_data)

    # Convert to dictionary and handle NaN values
    result = merged_data.to_dict('records')

    # Replace NaN with 'N/A'
    for record in result:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = 'N/A'

    if len(result) == 1:
        return jsonify({
            'success': True,
            'player': result[0]
        })
    else:
        return jsonify({
            'success': True,
            'message': f'Found {len(result)} players matching "{player_name}"',
            'players': result
        })

@app.route('/api/club/<club_name>', methods=['GET'])
def get_club(club_name):
    """
    Get all statistics for players in a specific club

    Args:
        club_name: Name of the club (case-insensitive)

    Returns:
        JSON with all players' statistics from that club
    """
    if player_stats_df is None or player_stats_df.empty:
        return jsonify({
            'error': 'No data available',
            'message': 'Player statistics database is empty'
        }), 500

    # Case-insensitive search
    club_data = player_stats_df[
        player_stats_df['Team'].str.lower() == club_name.lower()
        ]

    if club_data.empty:
        # Try partial match
        club_data = player_stats_df[
            player_stats_df['Team'].str.contains(club_name, case=False, na=False)
        ]

        if club_data.empty:
            # Get list of available clubs
            available_clubs = sorted(player_stats_df['Team'].unique().tolist())
            return jsonify({
                'error': 'Club not found',
                'message': f'No club found with name: {club_name}',
                'available_clubs': available_clubs
            }), 404

    # Merge with transfer values
    merged_data = merge_player_data(club_data)

    # Sort by player name
    merged_data = merged_data.sort_values('Player')

    # Convert to dictionary and handle NaN values
    result = merged_data.to_dict('records')

    # Replace NaN with 'N/A'
    for record in result:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = 'N/A'

    return jsonify({
        'success': True,
        'club': club_data['Team'].iloc[0],
        'total_players': len(result),
        'players': result
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get general statistics about the database"""
    if player_stats_df is None or player_stats_df.empty:
        return jsonify({
            'error': 'No data available'
        }), 500

    stats = {
        'total_players': len(player_stats_df),
        'total_clubs': player_stats_df['Team'].nunique(),
        'clubs': sorted(player_stats_df['Team'].unique().tolist()),
        'total_goals': int(player_stats_df['Standard_Gls'].sum()) if 'Standard_Gls' in player_stats_df.columns else 'N/A',
        'total_assists': int(player_stats_df['Standard_Ast'].sum()) if 'Standard_Ast' in player_stats_df.columns else 'N/A',
        'top_scorer': {
            'player': player_stats_df.loc[player_stats_df['Standard_Gls'].idxmax(), 'Player'] if 'Standard_Gls' in player_stats_df.columns else 'N/A',
            'goals': int(player_stats_df['Standard_Gls'].max()) if 'Standard_Gls' in player_stats_df.columns else 'N/A'
        } if 'Standard_Gls' in player_stats_df.columns else 'N/A',
        'top_assists': {
            'player': player_stats_df.loc[player_stats_df['Standard_Ast'].idxmax(), 'Player'] if 'Standard_Ast' in player_stats_df.columns else 'N/A',
            'assists': int(player_stats_df['Standard_Ast'].max()) if 'Standard_Ast' in player_stats_df.columns else 'N/A'
        } if 'Standard_Ast' in player_stats_df.columns else 'N/A'
    }

    return jsonify(stats)

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist',
        'available_endpoints': [
            '/api/player/<player_name>',
            '/api/club/<club_name>',
            '/api/stats'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500

if __name__ == '__main__':
    print("="*60)
    print("Premier League Player Statistics API")
    print("="*60)

    # Load data
    load_data()

    print("\n" + "="*60)
    print("Starting Flask server...")
    print("API will be available at: http://127.0.0.1:5000")
    print("="*60)
    print("\nAvailable endpoints:")
    print("  • GET /api/player/<player_name>")
    print("  • GET /api/club/<club_name>")
    print("  • GET /api/stats")
    print("\nExamples:")
    print("  • http://127.0.0.1:5000/api/player/Mohamed%20Salah")
    print("  • http://127.0.0.1:5000/api/club/Liverpool")
    print("  • http://127.0.0.1:5000/api/stats")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")

    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)