from rapidfuzz import fuzz
from yt_dlp import YoutubeDL
import os, json
import numpy as np
from scipy.optimize import linear_sum_assignment
import subprocess
import librosa

class YouTubeMatcher:
    def __init__(self, release_folder, debug):
        self.release_folder = release_folder
        self.debug = debug
        self.ytdl_opts = {
            'quiet': True,
            'skip_download': True,
            'nocheckcertificate': True,
            'format': 'ogg/bestaudio/best',
            # ℹ️ See help(yt_dlp.postprocessor) for a list of av(ailable Postprocessors and their arguments
            'postprocessors': [{  # Extract audio using ffmpeg
                'key': 'FFmpegExtractAudio',
                # 'preferredcodec': 'm4a',
            }]
        }
        
    def fetch_single_metadata(self, url):
        print("receiving single metadata from youtube")
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

            
    def fetch_release_YTmetadata(self, video_urls):
        self.youtube_release_metadata = []
        
        for url in video_urls:
            toAppend = self.fetch_single_metadata(url)
            if toAppend["title"] != None:
                self.youtube_release_metadata.append(toAppend)
            else:
                pass
            
        return self.youtube_release_metadata
    
    
    def duration_to_seconds(self, duration_str):
        try:
            parts = duration_str.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        except:
            return None
    
    
    def match_discogs_release_youtube(self, discogs_metadata):
        
        if os.path.isfile(os.path.join(self.release_folder, "yt_matches.json")) and self.debug==False:
           with open(os.path.join(self.release_folder, "yt_matches.json"), "r", encoding="utf-8") as f:
               self.matches = json.load(f)
        else:
        
            video_urls = discogs_metadata["videos"]
            youtube_metadata = self.fetch_release_YTmetadata(video_urls)
            
            self.matches = []
            
            tracklist = discogs_metadata["tracklist"]
            videos = youtube_metadata
            
            num_tracks = len(tracklist)
            num_videos = len(videos)
            
            # Score-Matrix (initial 0)
            score_matrix = np.zeros((num_tracks, num_videos))
            
            # Hilfslisten zum Zugriff später
            track_info = []
            video_info = []
            
            # Baue Score-Matrix
            for i, track in enumerate(tracklist):
                track_title = track['title']
                track_duration = self.duration_to_seconds(track['duration'])
                track_artist = track['artist']
                track_position = track['position']
                track_info.append((track_title, track_duration, track_position))
            
                for j, video in enumerate(videos):
                    video_title = video['title']
                    video_duration = video['length']
                    if i == 0:
                        video_info.append(video)
            
                    title_score = fuzz.WRatio(track_title.lower(), video_title.lower())
                    title_artist_score = fuzz.WRatio(f"{track_title.lower()} - {track_artist.lower()}", video_title.lower())
                    if track_duration and video_duration:
                        diff = abs(track_duration - video_duration)
                        duration_score = max(0, 1 - (diff / max(track_duration, 1)))
                        score = title_score + title_artist_score + duration_score
                    else:
                        score = title_score + title_artist_score
            
                    score_matrix[i][j] = -score  # Achtung: scipy sucht Minimum → wir negieren
            
            # Optimales Matching berechnen
            track_indices, video_indices = linear_sum_assignment(score_matrix)
            
            # Ergebnis speichern
            for i, j in zip(track_indices, video_indices):
                track_title, track_duration, track_position = track_info[i]
                matched_video = video_info[j]
                final_score = -score_matrix[i][j]  # wieder positiv machen
            
                self.matches.append({
                    'discogs_track': track_title,
                    'discogs_duration': track_duration,
                    'track_position': track_position,
                    'youtube_match': matched_video,
                    'match_score': round(final_score, 3)
                })

            # Speichern als JSON
            with open(os.path.join(self.release_folder,"yt_matches.json"), "w", encoding="utf-8") as f:
                json.dump(self.matches, f, indent=2, ensure_ascii=False)
            
        return
    
    
    
    def audioDWNLDAnalyse(self,  release_metadata):
        # erstelle matches:
            
        # self.match_discogs_release_youtube(release_metadata)
        
        ytdl_opts = {
            'quiet': True,
            'skip_download': False,
            'nocheckcertificate': True,
            'format': 'ogg/bestaudio/best',
            # ℹ️ See help(yt_dlp.postprocessor) for a list of av(ailable Postprocessors and their arguments
            'postprocessors': [{  # Extract audio using ffmpeg
                'key': 'FFmpegExtractAudio',
                # 'preferredcodec': 'm4a',
            }]
    }
        
        # # gehe track für track durch:
        for i, match in enumerate(self.matches):
            if match["youtube_match"] !=  None:
                
                if match["track_position"] == None:
                    match["track_position"] = str(i)
                else:
                    pass
                
                if self.matches[i]["discogs_duration"] ==  None:
                    self.matches[i]["discogs_duration"] = match["youtube_match"]["length"]
                
                track_filename = os.path.join(self.release_folder, match["track_position"])
                ytdl_opts['outtmpl'] = track_filename  # Zielverzeichnis + Dateiname
                url = match["youtube_match"]["url"]
                
                with YoutubeDL(ytdl_opts) as ydl:
                    info = ydl.extract_info(url, download=True, process=True, force_generic_extractor=False)
                    
                # self.download_and_stream_audio(url)
                    
                    
        # downloade nach tracklist, wenn mgl. nur audio:
        
        
        return
    


    def download_and_stream_audio(self, youtube_url, output_path="output.ogg"):
        # 1. Nur Info extrahieren, keine Datei speichern
        ytdl_opts = {
            'quiet': True,
            'format': 'bestaudio/best',
            'noplaylist': True,
            'skip_download': True,
        }
    
        with YoutubeDL(ytdl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            stream_url = info['url']
            print("Direct stream URL:", stream_url)
        
        # 2. ffmpeg: PCM + Save als OGG gleichzeitig
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', stream_url,
            '-map', '0:a',
            '-f', 'ogg',
            '-acodec', 'libvorbis',
            output_path,
            '-f', 'f32le',           # PCM: 32-bit float little endian
            '-acodec', 'pcm_f32le',
            '-ac', '1',              # Mono
            '-ar', '22050',          # Sample rate für librosa (kleiner = schneller)
            'pipe:1'                 # PCM an stdout
        ]
             
        print("Running ffmpeg...")
         
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
         
        # 3. PCM-Daten lesen & in NumPy-Array umwandeln
        raw_audio = process.stdout.read()
        audio_array = np.frombuffer(raw_audio, dtype=np.float32)
         
        # 4. BPM mit librosa berechnen
        print("Analyzing BPM...")
        tempo, _ = librosa.beat.beat_track(y=audio_array, sr=22050)
        print(f"Estimated BPM: {round(tempo)}")
         
        process.stdout.close()
        process.wait()
         
        return round(tempo)
