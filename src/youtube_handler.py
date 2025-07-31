from rapidfuzz import fuzz
from yt_dlp import YoutubeDL
import os, json
import numpy as np
from scipy.optimize import linear_sum_assignment
import subprocess
import librosa
from analyzeSoundFile import analyzeAudioFileOrStream
from logger import logger
import concurrent.futures
import threading
from utils import sanitize_filename

def _analyze_track_standalone(task):
    """Standalone-Funktion für parallele Track-Analyse"""
    import time
    import os
    from analyzeSoundFile import analyzeAudioFileOrStream
    from logger import logger
    
    audio_file = task['audio_file']
    track_filename_base = task['track_filename_base']
    track_position = task['track_position']
    
    try:
        start_time = time.time()
        
        json_file = f"{track_filename_base}.json"
        waveform_file = f"{track_filename_base}_waveform.png"
        
        analysis_needed = not os.path.exists(json_file)
        waveform_needed = not os.path.exists(waveform_file)
        
        if not analysis_needed and not waveform_needed:
            return {
                'track': track_position,
                'success': True,
                'duration': 0,
                'error': 'Already analyzed'
            }
        
        # Erstelle Analyzer
        analyzer = analyzeAudioFileOrStream(
            fileOrStream=audio_file,
            sampleRate=44100,
            plotWaveform=False,
            musicExtractor=True,
            plotSpectogram=True,
            debug=False
        )
        
        # Führe Essentia-Analyse durch
        if analysis_needed:
            analyzer.readAudioFile(ffmpegUsage=False)
            analyzer.analyzeMusicExtractor()
        
        # Führe Waveform-Generierung durch
        if waveform_needed:
            try:
                analyzer.generate_waveform_gnuplot()
            except Exception as e:
                logger.warning(f"Waveform generation failed for {track_position}: {e}")
        
        duration = time.time() - start_time
        return {
            'track': track_position,
            'success': True,
            'duration': duration,
            'error': None
        }
        
    except Exception as e:
        return {
            'track': track_position,
            'success': False,
            'duration': 0,
            'error': str(e)
        }

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
        logger.debug(f"Fetching metadata from: {url}")
        with YoutubeDL(self.ytdl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                title = info.get("title")
                logger.debug(f"✓ Metadata fetched: {title}")
                return {
                    "url": url,
                    "title": title,
                    "tags":  info.get("tags"),
                    "author": info.get("uploader"),
                    "length": info.get("duration")
                }
            except Exception as e:
                logger.warning(f"✗ Error fetching {url}: {e}")
                return {
                    "url": url,
                    "title": None,
                    "author": None,
                    "length": None
                }

            
    def fetch_release_YTmetadata(self, video_urls):
        self.youtube_release_metadata = []
        
        if len(video_urls) <= 1:
            # Für einzelne URLs normal verarbeiten
            for url in video_urls:
                toAppend = self.fetch_single_metadata(url)
                if toAppend["title"] is not None:
                    self.youtube_release_metadata.append(toAppend)
        else:
            # Parallele Verarbeitung für mehrere URLs
            logger.process(f"Fetching metadata for {len(video_urls)} YouTube videos in parallel...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                # Starte alle Metadaten-Abrufe parallel
                future_to_url = {executor.submit(self.fetch_single_metadata, url): url for url in video_urls}
                
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        metadata = future.result()
                        if metadata["title"] is not None:
                            self.youtube_release_metadata.append(metadata)
                    except Exception as e:
                        logger.warning(f"Error fetching metadata for {url}: {e}")
            
            logger.success(f"Fetched metadata for {len(self.youtube_release_metadata)}/{len(video_urls)} videos")
            
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
        
        # Aktualisiere Original-Metadaten mit YouTube-Dauern falls Discogs-Dauer fehlt
        self.update_metadata_with_youtube_durations()
            
        return
    
    def update_metadata_with_youtube_durations(self):
        """Aktualisiert die Original-Metadaten mit YouTube-Dauern falls Discogs-Dauer fehlt"""
        metadata_file = os.path.join(self.release_folder, "metadata.json")
        
        if not os.path.exists(metadata_file):
            logger.warning("metadata.json not found - cannot update durations")
            return
            
        # Lade Original-Metadaten
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata.json: {e}")
            return
            
        # Erstelle ein Mapping von Track-Position zu YouTube-Dauer
        youtube_durations = {}
        for match in self.matches:
            track_pos = match.get('track_position')
            youtube_match = match.get('youtube_match')
            if track_pos and youtube_match and youtube_match.get('length'):
                # Konvertiere Sekunden zu MM:SS Format
                duration_seconds = youtube_match['length']
                minutes = duration_seconds // 60
                seconds = duration_seconds % 60
                duration_str = f"{minutes}:{seconds:02d}"
                youtube_durations[track_pos] = duration_str
        
        # Aktualisiere Tracks mit fehlenden Dauern
        updated_count = 0
        for track in metadata.get('tracklist', []):
            track_pos = track.get('position')
            current_duration = track.get('duration')
            
            # Wenn keine Dauer oder leere Dauer vorhanden ist
            if track_pos and (not current_duration or current_duration.strip() == ''):
                if track_pos in youtube_durations:
                    track['duration'] = youtube_durations[track_pos]
                    updated_count += 1
                    logger.info(f"Updated track {track_pos} duration: {youtube_durations[track_pos]} (from YouTube)")
        
        # Speichere aktualisierte Metadaten falls Änderungen vorgenommen wurden
        if updated_count > 0:
            try:
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=4, ensure_ascii=False)
                logger.success(f"Updated {updated_count} track durations in metadata.json")
            except Exception as e:
                logger.error(f"Error saving updated metadata.json: {e}")
        else:
            logger.debug("No track durations needed updating")
    
    def audio_download_analyze(self, release_metadata):
        """Downloads audio for matched tracks and performs analysis"""
        
        ytdl_opts = {
            'quiet': False,  # Enable output for debugging
            'skip_download': False,
            'nocheckcertificate': True,
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'opus',
            'outtmpl': '%(title)s.%(ext)s',  # Will be overridden per track
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '192',
            }],
            'ignoreerrors': True,  # Continue on errors
        }
        
        # Download phase - separate from analysis
        downloaded_tracks = []
        
        for i, match in enumerate(self.matches):
            if match["youtube_match"] is None:
                logger.warning(f"No YouTube match for track {match.get('track_position', i)}")
                continue
                
            # Ensure track position is set
            if match["track_position"] is None:
                match["track_position"] = str(i + 1)
                
            # Update duration if missing
            if self.matches[i]["discogs_duration"] is None:
                self.matches[i]["discogs_duration"] = match["youtube_match"]["length"]
            
            track_position = match["track_position"]
            track_filename_base = os.path.join(self.release_folder, sanitize_filename(track_position))
            
            # Check if audio file already exists
            existing_file = self.get_downloaded_audio_file(track_filename_base)
            if existing_file:
                logger.info(f"Audio file already exists for track {track_position}: {os.path.basename(existing_file)}")
                downloaded_tracks.append((track_filename_base, track_position))
                continue
            
            url = match["youtube_match"]["url"]
            ytdl_opts['outtmpl'] = track_filename_base + '.%(ext)s'
            
            try:
                logger.process(f"Downloading audio for track {track_position}: {match['discogs_track']}")
                
                with YoutubeDL(ytdl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    
                # Verify download completed
                downloaded_file = self.get_downloaded_audio_file(track_filename_base)
                if downloaded_file:
                    logger.success(f"Downloaded: {os.path.basename(downloaded_file)}")
                    downloaded_tracks.append((track_filename_base, track_position))
                else:
                    logger.error(f"Download failed for track {track_position} - no file found")
                    
            except Exception as e:
                logger.error(f"Download error for track {track_position}: {e}")
                continue
        
        # Analysis phase - parallel analysis of all downloaded tracks
        if downloaded_tracks:
            logger.info(f"Download phase complete. Starting parallel analysis for {len(downloaded_tracks)} tracks...")
            self._parallel_audio_analysis(downloaded_tracks)
        
        logger.success(f"Audio download and analysis completed for {len(downloaded_tracks)} tracks")
        return
    
    def _parallel_audio_analysis(self, downloaded_tracks):
        """Führt parallele Audio-Analyse mit ProcessPoolExecutor durch (optimiert für CPU-bound tasks)"""
        import concurrent.futures
        import time
        
        # Optimale Prozess-Anzahl für CPU-intensive Essentia-Analyse
        # Nutze 80% der CPU-Kerne, aber nicht mehr als Tracks vorhanden sind
        cpu_cores = os.cpu_count() or 2
        optimal_workers = max(1, int(cpu_cores * 0.8))  # 80% der Kerne für bessere Systemstabilität
        max_workers = min(len(downloaded_tracks), optimal_workers)
        
        logger.info(f"🔄 Starting parallel analysis with {max_workers}/{cpu_cores} processes (ProcessPoolExecutor)")
        analysis_start = time.time()
        
        # Bereite Daten für parallele Verarbeitung vor
        analysis_tasks = []
        for track_filename_base, track_position in downloaded_tracks:
            audio_file = self.get_downloaded_audio_file(track_filename_base)
            if audio_file:
                analysis_tasks.append({
                    'audio_file': audio_file,
                    'track_filename_base': track_filename_base,
                    'track_position': track_position
                })
        
        if not analysis_tasks:
            logger.warning("No audio files found for analysis")
            return
        
        # Verwende ProcessPoolExecutor für CPU-intensive Essentia-Analyse
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Starte alle Analyse-Tasks
            future_to_track = {
                executor.submit(_analyze_track_standalone, task): task['track_position']
                for task in analysis_tasks
            }
            
            # Sammle Ergebnisse
            results = []
            for future in concurrent.futures.as_completed(future_to_track):
                track_position = future_to_track[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        logger.success(f"✅ Track {result['track']} analyzed in {result['duration']:.2f}s")
                    else:
                        logger.error(f"❌ Track {result['track']} failed: {result['error']}")
                        
                except Exception as e:
                    logger.error(f"❌ Track {track_position} crashed: {e}")
                    results.append({
                        'track': track_position,
                        'success': False,
                        'duration': 0,
                        'error': f"Execution error: {e}"
                    })
        
        # Performance-Statistiken
        total_time = time.time() - analysis_start
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        avg_time = sum(r['duration'] for r in results if r['success']) / max(successful, 1)
        
        logger.info(f"📊 Parallel Analysis Results:")
        logger.info(f"   ✅ Successful: {successful}/{len(downloaded_tracks)} tracks")
        logger.info(f"   ❌ Failed: {failed} tracks")
        logger.info(f"   ⏱️  Total time: {total_time:.2f}s")
        logger.info(f"   📈 Average per track: {avg_time:.2f}s")
        logger.info(f"   🚀 Parallel speedup: ~{len(downloaded_tracks) * avg_time / max(total_time, 0.1):.1f}x faster than sequential")



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
            logger.debug(f"Direct stream URL: {stream_url}")
        
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
             
        logger.process("Running ffmpeg...")
         
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
         
        # 3. PCM-Daten lesen & in NumPy-Array umwandeln
        raw_audio = process.stdout.read()
        audio_array = np.frombuffer(raw_audio, dtype=np.float32)
         
        # 4. BPM mit librosa berechnen
        logger.analyze("Analyzing BPM...")
        tempo, _ = librosa.beat.beat_track(y=audio_array, sr=22050)
        logger.info(f"Estimated BPM: {round(tempo)}")
         
        process.stdout.close()
        process.wait()
         
        return round(tempo)
    
    def analyze_downloaded_track(self, track_filename_base, track_position):
        """Analysiert einen heruntergeladenen Track mit Essentia"""
        try:
            # Finde die tatsächlich heruntergeladene Datei
            audio_file = self.get_downloaded_audio_file(track_filename_base)
            
            if not audio_file:
                logger.warning(f"No audio file found for track {track_position}")
                return False
            
            # Prüfe welche Analysen noch fehlen
            json_file = f"{track_filename_base}.json"
            waveform_file = f"{track_filename_base}_waveform.png"
            
            analysis_exists = os.path.exists(json_file)
            waveform_exists = os.path.exists(waveform_file)
            
            if analysis_exists and waveform_exists:
                logger.info(f"Audio analysis and waveform already exist for track {track_position}")
                return True
                
            # Zeige was noch zu tun ist
            todo_items = []
            if not analysis_exists:
                todo_items.append("Essentia analysis")
            if not waveform_exists:
                todo_items.append("waveform generation")
            logger.info(f"Running {', '.join(todo_items)} for track {track_position}")
            
            # Warte kurz falls Datei noch geschrieben wird
            import time
            time.sleep(0.5)
            
            # Prüfe Dateigröße (sollte > 0 sein)
            if os.path.getsize(audio_file) == 0:
                logger.error(f"Audio file is empty for track {track_position}: {audio_file}")
                return False
                
            # Erstelle Analyzer-Instanz
            analyzer = analyzeAudioFileOrStream(
                fileOrStream=audio_file,
                sampleRate=44100,
                plotWaveform=False,  # Wird separat gehandhabt
                musicExtractor=True,
                plotSpectogram=True,
                debug=False
            )
            
            success = True
            
            # Führe Essentia-Analyse durch (falls noch nicht existiert)
            if not analysis_exists:
                try:
                    logger.analyze(f"Running Essentia analysis: {os.path.basename(audio_file)}")
                    analyzer.readAudioFile(ffmpegUsage=False)
                    analyzer.analyzeMusicExtractor()
                    logger.success(f"Essentia analysis completed for track {track_position}")
                except Exception as e:
                    logger.error(f"Essentia analysis failed for track {track_position}: {e}")
                    success = False
            
            # Führe Waveform-Generation durch (falls noch nicht existiert)
            if not waveform_exists:
                try:
                    # Waveform-Generierung für alle Tracks mit gnuplot
                    waveform_success = analyzer.generate_waveform_gnuplot()
                    
                    if waveform_success:
                        logger.success(f"Waveform generation completed for track {track_position}")
                    else:
                        logger.warning(f"Waveform generation failed for track {track_position}")
                        success = False
                except Exception as e:
                    logger.error(f"Waveform generation failed for track {track_position}: {e}")
                    success = False
            
            if success:
                logger.success(f"Audio processing completed for track {track_position}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in audio analysis for track {track_position}: {e}")
            return False
            
    def get_downloaded_audio_file(self, track_filename_base):
        """Findet die heruntergeladene Audio-Datei (yt-dlp fügt verschiedene Erweiterungen hinzu)"""
        for ext in ['.ogg', '.m4a', '.mp3', '.webm', '.opus']:
            potential_file = f"{track_filename_base}{ext}"
            if os.path.exists(potential_file):
                return potential_file
        return None
