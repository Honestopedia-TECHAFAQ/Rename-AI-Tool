import os
import streamlit as st
from pathlib import Path
import requests
from pymediainfo import MediaInfo
import shutil

# Global variable to store renaming history
renaming_history = []

# Function to rename files based on media type
def rename_files(directory, media_type, details, naming_pattern, language_preference, move_files, destination_directory):
    renamed_files = []  # Store the list of renamed files for the history
    total_files = len(os.listdir(directory))
    
    with st.progress(0) as progress_bar:
        for i, filename in enumerate(os.listdir(directory), 1):
            old_path = os.path.join(directory, filename)

            # Create a new filename based on the media type
            new_filename = generate_new_filename(media_type, details, naming_pattern, language_preference, old_path)

            new_path = os.path.join(directory, new_filename)
            os.rename(old_path, new_path)

            # Generate and save .nfo files for Plex
            if media_type == "Movies":
                generate_plex_nfo(details, new_path)

            # Move files to the destination directory
            if move_files:
                move_file(new_path, destination_directory)

            renamed_files.append((old_path, new_path))  # Store old and new file paths for the history

            # Update progress bar
            progress_percentage = (i / total_files) * 100
            progress_bar.progress(progress_percentage)

    # Add the renamed files to the renaming history
    renaming_history.append(renamed_files)

# Function to undo the last renaming action
def undo_rename():
    if renaming_history:
        last_renamed_files = renaming_history.pop()
        for old_path, new_path in last_renamed_files:
            os.rename(new_path, old_path)

# Function to move a file to a specified directory
def move_file(file_path, destination_directory):
    destination_path = os.path.join(destination_directory, os.path.basename(file_path))
    shutil.move(file_path, destination_path)

# Function to generate a new filename based on media type and details
def generate_new_filename(media_type, details, naming_pattern, language_preference, file_path):
    # Get audio and video information using MediaInfo
    media_info = MediaInfo.parse(file_path)
    audio_info = media_info.audio_tracks[0] if media_info.audio_tracks else None
    video_info = media_info.video_tracks[0] if media_info.video_tracks else None

    # Extract relevant details
    audio_channels = f"{audio_info.channel_s}" if audio_info else ""
    video_resolution = f"{video_info.height}p" if video_info else ""
    codec_details = f"{video_info.codec_name}" if video_info else ""

    # Create a dictionary with details for formatting
    formatting_details = {
        "title": details.get("title", ""),
        "year": details.get("year", ""),
        "season": details.get("season", ""),
        "episode": details.get("episode", ""),
        "artist": details.get("artist", ""),
        "author": details.get("author", ""),
        "audio_channels": audio_channels,
        "video_resolution": video_resolution,
        "codec_details": codec_details,
        "language": language_preference
    }

    # Create a new filename based on the naming pattern
    new_filename = naming_pattern.format(**formatting_details)

    return new_filename

# Function to generate Plex .nfo file
def generate_plex_nfo(details, file_path):
    nfo_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<movie>
  <title>{details['title']}</title>
  <year>{details['year']}</year>
  <!-- Add more metadata as needed -->
</movie>
"""
    nfo_filename = os.path.splitext(file_path)[0] + ".nfo"
    with open(nfo_filename, "w", encoding="utf-8") as nfo_file:
        nfo_file.write(nfo_content)

# Function to fetch movie data from OMDb API
def fetch_movie_data(title, api_key):
    params = {'apikey': api_key, 't': title}
    response = requests.get('http://www.omdbapi.com/', params=params)
    data = response.json()
    return data

# Streamlit app
def main():
    global renaming_history  # Use the global variable

    st.set_page_config(
        page_title="Rename Tool",
        page_icon="✨",
        layout="wide"
    )

    st.title("File Rename Tool")

    # Sidebar
    st.sidebar.title("Settings")

    # Preferences Section
    st.sidebar.header("Preferences")
    contact_info = st.sidebar.text_input("Contact Information for Support", "support@example.com")
    st.sidebar.write(f"Contact Support at: {contact_info}")

    # File Selection
    st.sidebar.header("File Selection")
    uploaded_files = st.sidebar.file_uploader("Choose files to rename", type=["txt", "pdf", "jpg", "png", "mp3", "mp4"], accept_multiple_files=True)

    # Display selected file names
    if uploaded_files:
        st.sidebar.subheader("Selected Files:")
        for file in uploaded_files:
            st.sidebar.write(file.name)

    # Media Type Selection
    st.sidebar.header("Media Type")
    media_type = st.sidebar.selectbox("Select Media Type", ["Movies", "Series", "Animes", "Music", "Audiobooks", "eBooks"])

    # Details based on media type
    st.sidebar.header("Details")
    details = {}
    if media_type == "Movies":
        details["title"] = st.sidebar.text_input("Movie Title")
        details["year"] = st.sidebar.number_input("Release Year", min_value=1800, max_value=2100)
        # Fetch movie data from OMDb API if title is provided
        if details["title"]:
            api_key = st.sidebar.text_input("OMDb API Key")  # Get your API key from http://www.omdbapi.com/apikey.aspx
            if api_key:
                movie_data = fetch_movie_data(details["title"], api_key)
                details["title"] = movie_data.get("Title", details["title"])
                details["year"] = int(movie_data.get("Year", details.get("year", 0)))

    # Naming Pattern and Language Preferences
    st.sidebar.header("Naming Pattern and Language Preferences")
    naming_pattern = st.sidebar.text_input("Custom Naming Pattern", "{title} ({year})_{audio_channels}_{video_resolution}_{codec_details}_{language}")
    language_preference = st.sidebar.text_input("Language Preference", "English")

    # File Movement Options
    st.sidebar.header("File Movement Options")
    move_files = st.sidebar.checkbox("Move Files to Destination Directory")
    destination_directory = st.sidebar.text_input("Destination Directory", "")

    # Button to trigger the rename
    if st.sidebar.button("Rename Files"):
        if not uploaded_files or not details:
            st.warning("Please provide valid inputs.")
        else:
            try:
                # Save the uploaded files to the selected directory
                directory = st.text_input("Enter a directory path to save files (e.g., './uploads')")
                os.makedirs(directory, exist_ok=True)

                for file in uploaded_files:
                    file_path = os.path.join(directory, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getvalue())

                # Rename and move the files based on the media type and details
                rename_files(directory, media_type, details, naming_pattern, language_preference, move_files, destination_directory)
                st.success("Files successfully renamed and moved!")

                # Clear the renaming history after a successful rename
                renaming_history = []

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # Button to trigger undo functionality
    if st.sidebar.button("Undo Last Rename"):
        undo_rename()
        st.success("Undo successful!")

if __name__ == "__main__":
    main()
