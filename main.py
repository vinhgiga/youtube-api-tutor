import os
import re

import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

api_key = os.getenv("YOUTUBE_API_KEY")


def extract_video_id(url):
    """Extract the video ID from a YouTube URL."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/|v\/|youtu.be\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_video_info(video_id):
    """Get video information using the YouTube API."""
    youtube = build('youtube', 'v3', developerKey=api_key)

    request = youtube.videos().list(
        part="snippet,contentDetails,statistics", id=video_id
    )
    response = request.execute()

    if not response['items']:
        return None

    video_data = response['items'][0]

    info = {
        'title': video_data['snippet']['title'],
        'channel': video_data['snippet']['channelTitle'],
        'published_at': video_data['snippet']['publishedAt'],
        'view_count': video_data['statistics'].get('viewCount', 'N/A'),
        'like_count': video_data['statistics'].get('likeCount', 'N/A'),
        'comment_count': video_data['statistics'].get('commentCount', 'N/A'),
        'duration': video_data['contentDetails']['duration'],
    }

    return info


def generate_mix_playlist_url(video_id):
    """Generate a YouTube mix playlist URL from a video ID."""
    return f"https://www.youtube.com/watch?v={video_id}&list=RD{video_id}"


def get_mix_playlist(video_id, max_results=10):
    """Fetch videos from a YouTube mix playlist using the YouTube API."""
    youtube = build('youtube', 'v3', developerKey=api_key)

    # Mix playlists have the format "RD" + video_id
    playlist_id = f"RD{video_id}"

    try:
        # Get playlist items
        request = youtube.playlistItems().list(
            part="snippet", maxResults=max_results, playlistId=playlist_id
        )
        response = request.execute()

        # Process the results
        playlist_items = []
        for item in response.get('items', []):
            if 'snippet' in item:
                snippet = item['snippet']
                video_data = {
                    'title': snippet.get('title', 'Unknown Title'),
                    'channel': snippet.get('videoOwnerChannelTitle', 'Unknown Channel'),
                    'video_id': snippet.get('resourceId', {}).get(
                        'videoId', 'Unknown ID'
                    ),
                }
                playlist_items.append(video_data)

        return playlist_items
    except Exception as e:
        print(f"Error fetching mix playlist: {e}")
        return None


def extract_playlist_id(url):
    """Extract the playlist ID from a YouTube URL."""
    playlist_pattern = r'(?:list=)([a-zA-Z0-9_-]+)'
    match = re.search(playlist_pattern, url)
    if match:
        return match.group(1)
    return None


def get_playlist_videos(playlist_id, max_results=50):
    """Get all videos from a YouTube playlist."""
    youtube = build('youtube', 'v3', developerKey=api_key)

    videos = []
    next_page_token = None

    while True:
        # Get playlist items
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            maxResults=min(max_results, 50),  # API limit is 50 per request
            playlistId=playlist_id,
            pageToken=next_page_token,
        )
        response = request.execute()

        # Process items
        for item in response.get('items', []):
            if 'snippet' in item and 'contentDetails' in item:
                video_id = item['contentDetails']['videoId']
                videos.append(
                    {
                        'video_id': video_id,
                        'title': item['snippet'].get('title', 'Unknown'),
                        'channel_id': item['snippet'].get('channelId', 'Unknown'),
                        'channel_title': item['snippet'].get('channelTitle', 'Unknown'),
                        'position': item['snippet'].get('position', 0),
                    }
                )

        # Check if there are more pages
        next_page_token = response.get('nextPageToken')
        if not next_page_token or len(videos) >= max_results:
            break

    return videos


def get_detailed_video_stats(video_ids):
    """Get detailed stats for a list of videos."""
    if not video_ids:
        return []

    youtube = build('youtube', 'v3', developerKey=api_key)

    # Process videos in batches of 50 (API limit)
    all_video_data = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]

        request = youtube.videos().list(part="snippet,statistics", id=",".join(batch))
        response = request.execute()

        for item in response.get('items', []):
            video_data = {
                'video_id': item['id'],
                'title': item['snippet'].get('title', 'Unknown'),
                'channel_id': item['snippet'].get('channelId', 'Unknown'),
                'channel_title': item['snippet'].get('channelTitle', 'Unknown'),
                'view_count': item['statistics'].get('viewCount', 'N/A'),
                'like_count': item['statistics'].get('likeCount', 'N/A'),
                'comment_count': item['statistics'].get('commentCount', 'N/A'),
                'published_at': item['snippet'].get('publishedAt', 'Unknown'),
            }
            all_video_data.append(video_data)

    return all_video_data


def export_to_excel(video_data, filename='youtube_playlist_data.xlsx'):
    """Export video data to Excel file."""
    # Process data for Excel
    excel_data = []
    for video in video_data:
        excel_data.append(
            {
                'Video ID': video['video_id'],
                'Title': video['title'],
                'Channel ID': video['channel_id'],
                'Channel': video['channel_title'],
                'View Count': video['view_count'],
                'Like Count': video['like_count'],
                'Comment Count': video['comment_count'],
                'Published Date': video['published_at'],
                'Video URL': f"https://www.youtube.com/watch?v={video['video_id']}",
            }
        )

    # Create DataFrame and export to Excel
    df = pd.DataFrame(excel_data)
    df.to_excel(filename, index=False)

    return filename


def read_videos_from_excel(filename):
    """Read video IDs from an Excel file."""
    try:
        df = pd.read_excel(filename)

        # Check if 'Video ID' column exists
        if 'Video ID' in df.columns:
            video_ids = df['Video ID'].tolist()
            return video_ids
        print("Error: Excel file does not contain 'Video ID' column.")
        return []
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []


def get_mix_playlists_for_videos(video_ids, max_results_per_mix=10):
    """Get mix playlists for multiple video IDs."""
    all_mix_playlists = []

    for i, video_id in enumerate(video_ids, 1):
        print(f"Processing video {i}/{len(video_ids)}: {video_id}")

        try:
            mix_playlist = get_mix_playlist(video_id, max_results_per_mix)
            if mix_playlist:
                for video in mix_playlist:
                    video['source_video_id'] = video_id  # Add source video ID reference
                all_mix_playlists.extend(mix_playlist)
            else:
                print(
                    f"Warning: Could not retrieve mix playlist for video ID: {video_id}"
                )
        except Exception as e:
            print(f"Error getting mix playlist for video ID {video_id}: {e}")

    return all_mix_playlists


def export_mix_playlists_to_excel(mix_playlists, filename='youtube_mix_playlists.xlsx'):
    """Export mix playlists data to Excel file."""
    # Process data for Excel
    excel_data = []
    for video in mix_playlists:
        excel_data.append(
            {
                'Source Video ID': video.get('source_video_id', 'Unknown'),
                'Video ID': video.get('video_id', 'Unknown'),
                'Title': video.get('title', 'Unknown'),
                'Channel': video.get('channel', 'Unknown'),
                'Video URL': f"https://www.youtube.com/watch?v={video.get('video_id', '')}",
            }
        )

    # Create DataFrame and export to Excel
    df = pd.DataFrame(excel_data)
    df.to_excel(filename, index=False)

    return filename


def main():
    # Get YouTube URL from user
    url = input("Enter YouTube URL (or press Enter to skip for option 4): ")

    # Ask user what they want to do
    print("\nOptions:")
    print("1. Get video information")
    print("2. Get mix playlist videos")
    print("3. Export playlist videos to Excel")
    print("4. Get mix playlists for videos in Excel file")
    choice = input("Enter your choice (1, 2, 3, or 4): ")

    if choice in ['1', '2', '3'] and not url:
        print("Error: URL is required for options 1-3.")
        return

    if choice == '1':
        # Extract video ID
        video_id = extract_video_id(url)
        if not video_id:
            print("Error: Could not extract video ID from the provided URL.")
            return

        # Get video information
        video_info = get_video_info(video_id)
        if not video_info:
            print(f"Error: Could not retrieve information for video ID: {video_id}")
            return

        # Display video information
        print("\nVideo Information:")
        print(f"Title: {video_info['title']}")
        print(f"Channel: {video_info['channel']}")
        print(f"Published: {video_info['published_at']}")
        print(f"Views: {video_info['view_count']}")
        print(f"Likes: {video_info['like_count']}")
        print(f"Comments: {video_info['comment_count']}")
        print(f"Duration: {video_info['duration']}")

    elif choice == '2':
        # Extract video ID
        video_id = extract_video_id(url)
        if not video_id:
            print("Error: Could not extract video ID from the provided URL.")
            return

        # Fetch and display mix playlist videos
        print("\nFetching mix playlist videos...")
        playlist_items = get_mix_playlist(video_id)

        if not playlist_items:
            print("Error: Could not retrieve mix playlist or playlist is empty.")
            return

        print(f"\nMix Playlist Based on Video ID: {video_id}")
        print("=" * 50)

        for i, item in enumerate(playlist_items, 1):
            print(f"{i}. {item['title']}")
            print(f"   Channel: {item['channel']}")
            print(f"   Video ID: {item['video_id']}")
            print(f"   URL: https://www.youtube.com/watch?v={item['video_id']}")
            print("-" * 50)

        print(
            f"\nPlaylist URL: https://www.youtube.com/watch?v={video_id}&list=RD{video_id}"
        )

    elif choice == '3':
        # Extract playlist ID
        playlist_id = extract_playlist_id(url)
        if not playlist_id:
            print("Error: Could not extract playlist ID from the provided URL.")
            return

        print(f"\nFetching videos from playlist ID: {playlist_id}")

        # Get all videos in the playlist
        playlist_videos = get_playlist_videos(playlist_id)
        if not playlist_videos:
            print(
                "Error: Could not retrieve videos from the playlist or playlist is empty."
            )
            return

        print(f"Found {len(playlist_videos)} videos in the playlist.")

        # Get video IDs for detailed stats
        video_ids = [video['video_id'] for video in playlist_videos]

        print("Fetching detailed statistics for each video...")
        video_stats = get_detailed_video_stats(video_ids)

        # Export to Excel
        filename = input(
            "Enter filename for Excel export (default: youtube_playlist_data.xlsx): "
        )
        if not filename:
            filename = "youtube_playlist_data.xlsx"

        if not filename.endswith('.xlsx'):
            filename += '.xlsx'

        fullpath = export_to_excel(video_stats, filename)
        print(f"Data exported successfully to: {fullpath}")

    elif choice == '4':
        # Get input Excel file
        input_file = input("Enter path to Excel file containing video IDs: ")
        if not os.path.exists(input_file):
            print(f"Error: File '{input_file}' not found.")
            return

        # Read video IDs from Excel
        video_ids = read_videos_from_excel(input_file)
        if not video_ids:
            print("No valid video IDs found in the Excel file.")
            return

        print(f"Found {len(video_ids)} videos in the Excel file.")

        # Get max results per mix playlist
        try:
            max_results = int(
                input("Enter maximum number of videos per mix playlist (default: 10): ")
                or 10
            )
        except ValueError:
            max_results = 10

        # Get mix playlists for each video
        print(f"\nFetching mix playlists for {len(video_ids)} videos...")
        mix_playlists = get_mix_playlists_for_videos(video_ids, max_results)

        if not mix_playlists:
            print("Error: Could not retrieve any mix playlists.")
            return

        print(
            f"Successfully fetched {len(mix_playlists)} videos across all mix playlists."
        )

        # Export to Excel
        output_file = input(
            "Enter filename for Excel export (default: youtube_mix_playlists.xlsx): "
        )
        if not output_file:
            output_file = "youtube_mix_playlists.xlsx"

        if not output_file.endswith('.xlsx'):
            output_file += '.xlsx'

        fullpath = export_mix_playlists_to_excel(mix_playlists, output_file)
        print(f"Mix playlists data exported successfully to: {fullpath}")

    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
