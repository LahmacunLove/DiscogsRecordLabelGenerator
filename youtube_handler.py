from rapidfuzz import fuzz
from yt_dlp import YoutubeDL
import os
from datetime import datetime

class YouTubeMatcher:
    def __init__(self):
        self.ytdl_opts = {
            'quiet': True,
            'skip_download': True,
            'nocheckcertificate': True,
            'format': 'bestaudio/best',
        }

    def fetch_single_metadata(self, url):
        print("receiving single metadata")
        with YoutubeDL(self.ytdl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                return {
                    "url": url,
                    "title": info.get("title"),
                    "tags":  info.get("tags"),
                    "author": info.get("uploader"),
                    "length": info.get("duration")
                }
            except Exception as e:
                print(f"⚠️ Fehler bei {url}: {e}")
                return {
                    "url": url,
                    "title": None,
                    "author": None,
                    "length": None
                }

            
    def fetch_release_metadata(self, video_urls):
        self.youtube_release_metadata = []
        
        for url in video_urls:
            self.youtube_release_metadata.append(self.fetch_single_metadata(url))
        
        return self.youtube_release_metadata
    
    
    def duration_to_seconds(self, duration_str):
        try:
            parts = duration_str.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        except:
            return None
    
    
    def match_discogs_release_youtube(self, discogs_metadata, youtube_metadata):
        video_urls = discogs_metadata["videos"]
        youtube_metadata = self.fetch_release_metadata(video_urls)
        
        self.matches = []
        
        for track in discogs_metadata["tracklist"]:
            best_match = None
            best_score = 0
    
            track_title = track['title']
            track_duration = self.duration_to_seconds(track['duration'])
            track_artist = track['artist']
            track_position = track['position']
            
            for video in youtube_metadata:
                video_title = video['title']
                video_duration = video['length']
    
                # Titel-Ähnlichkeit
                title_score = fuzz.token_sort_ratio(track_title.lower(), video_title.lower()) / 100.0
                title_artist_score = fuzz.token_sort_ratio(\
                                       " - ".join([track_title.lower(), track_artist.lower()]),
                                       " ".join([video_title.lower()]))
                    
                # Dauer-Vergleich
                if track_duration and video_duration:
                    diff = abs(track_duration - video_duration)
                    duration_score = max(0, 1 - (diff / max(track_duration, 1)))  # Normiert
                else:
                    duration_score = 0  # Default wenn keine Daten
    
                # Kombinierter Score
                score = title_score + duration_score + title_artist_score
    
                if score > best_score:
                    best_score = score
                    best_match = video
            
            self.matches.append({
                'discogs_track': track_title,
                'discogs_duration': track_duration,
                'track_position' : track_position,
                'youtube_match': best_match,
                'match_score': round(best_score, 3)
            })
            
        return
            
    
    def download(self,  release_metadata, output_path):
        
        self.fetch_release_metadata(release_metadata["videos"])
        
        self.match_discogs_release_youtube(release_metadata, self.youtube_release_metadata)
        
        for match in self.matches:
            print(match)
        

