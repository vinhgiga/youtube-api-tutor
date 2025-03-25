import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd

# Update scopes to allow playlist modification
scopes = ["https://www.googleapis.com/auth/youtube"]


def read_video_ids_from_excel(excel_file_path):
    """Read video IDs from an Excel file."""
    df = pd.read_excel(excel_file_path)
    # Adjust column name based on your Excel file structure
    video_ids = df['Video ID'].tolist()
    return video_ids


def find_music_video_playlist(youtube):
    """Find the 'music video' playlist ID or create it if it doesn't exist."""
    request = youtube.playlists().list(part="snippet,id", mine=True)
    response = request.execute()

    for item in response.get('items', []):
        if item['snippet']['title'] == 'music video':
            return item['id']

    # If no playlist was found, create a new one
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "music video",
                "description": "A playlist for music videos",
            },
            "status": {
                "privacyStatus": "private"  # or 'public' or 'unlisted'
            },
        },
    )
    response = request.execute()
    return response['id']


def add_videos_to_playlist(youtube, playlist_id, video_ids):
    """Add videos to the specified playlist."""
    for video_id in video_ids:
        try:
            request = youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id},
                    }
                },
            )
            response = request.execute()
            print(f"Added video {video_id} to playlist")
        except googleapiclient.errors.HttpError as e:
            print(f"Error adding video {video_id}: {e}")


def main():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "client_secret.json"
    excel_file_path = "youtube_mix_playlists.xlsx"  # Path to your Excel file

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes
    )
    credentials = flow.run_local_server(port=0)
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials
    )

    # Read video IDs from Excel file
    video_ids = read_video_ids_from_excel(excel_file_path)

    # Find or create the 'music video' playlist
    playlist_id = find_music_video_playlist(youtube)

    # Add videos to the playlist
    add_videos_to_playlist(youtube, playlist_id, video_ids)


if __name__ == "__main__":
    main()
