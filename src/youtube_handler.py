from rapidfuzz import fuzz
from yt_dlp import YoutubeDL
import os, json
import numpy as np
from scipy.optimize import linear_sum_assignment
import subprocess
import librosa

# Make audio analysis optional
try:
    from analyzeSoundFile import analyzeAudioFileOrStream, ESSENTIA_AVAILABLE
except ImportError as e:
    analyzeAudioFileOrStream = None
    ESSENTIA_AVAILABLE = False
    import warnings
    warnings.warn(f"Audio analysis not available: {e}")

from logger import logger
import concurrent.futures
import threading
from utils import sanitize_filename
from cpu_utils import get_optimal_workers

def _analyze_track_standalone(task):
    """Standalone function for parallel track analysis"""
    import time
    import os
    try:
        from analyzeSoundFile import analyzeAudioFileOrStream, ESSENTIA_AVAILABLE
    except ImportError:
        analyzeAudioFileOrStream = None
        ESSENTIA_AVAILABLE = False
    from logger import logger

    audio_file = task['audio_file']
    track_filename_base = task['track_filename_base']
    track_position = task['track_position']
    release_info = task.get('release_info', 'Unknown Release')

    # Skip if audio analysis not available
    if not analyzeAudioFileOrStream:
        logger.warning(f"[{release_info}] Skipping analysis for track {track_position} - audio analysis not available")
        return {
            'track': track_position,
            'success': False,
            'duration': 0,
            'error': 'Audio analysis not available'
        }

    try:
        start_time = time.time()

        json_file = f"{track_filename_base}.json"
        waveform_file = f"{track_filename_base}_waveform.png"

        analysis_needed = not os.path.exists(json_file)
        waveform_needed = not os.path.exists(waveform_file)

        if not analysis_needed and not waveform_needed:
            logger.debug(f"[{release_info}] Track {track_position} already analyzed")
            return {
                'track': track_position,
                'success': True,
                'duration': 0,
                'error': 'Already analyzed'
            }

        analyzer = None

        # Perform Essentia analysis (independent task)
        if analysis_needed:
            logger.process(f"[{release_info}] Running Essentia analysis for track {track_position}")
            analyzer = analyzeAudioFileOrStream(
                fileOrStream=audio_file,
                sampleRate=44100,
                plotWaveform=False,
                musicExtractor=True,
                plotSpectogram=True,
                debug=False
            )
            analyzer.readAudioFile(ffmpegUsage=False)
            analyzer.analyzeMusicExtractor()
            logger.success(f"[{release_info}] Essentia analysis completed for track {track_position}")
        
        # Perform waveform generation (independent task)
        if waveform_needed:
            try:
                logger.process(f"[{release_info}] Generating waveform for track {track_position}")
                # Create separate analyzer instance if not already created
                if analyzer is None:
                    analyzer = analyzeAudioFileOrStream(
                        fileOrStream=audio_file,
                        sampleRate=44100,
                        plotWaveform=False,
                        musicExtractor=False,  # No need for music analysis
                        plotSpectogram=False,  # No need for spectrograms
                        debug=False
                    )
                    analyzer.readAudioFile(ffmpegUsage=False)
                
                analyzer.generate_waveform_gnuplot()
                logger.success(f"[{release_info}] Waveform generation completed for track {track_position}")
            except Exception as e:
                logger.warning(f"[{release_info}] Waveform generation failed for track {track_position}: {e}")
        
        duration = time.time() - start_time
        logger.success(f"[{release_info}] Track {track_position} analysis completed in {duration:.2f}s")
        return {
            'track': track_position,
            'success': True,
            'duration': duration,
            'error': None
        }
        
    except Exception as e:
        logger.error(f"[{release_info}] Track {track_position} analysis failed: {e}")
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
            # Process single URLs normally
            for url in video_urls:
                toAppend = self.fetch_single_metadata(url)
                if toAppend["title"] is not None:
                    self.youtube_release_metadata.append(toAppend)
        else:
            # Parallel processing for multiple URLs
            logger.process(f"Fetching metadata for {len(video_urls)} YouTube videos in parallel...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                # Start all metadata fetches in parallel
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
            
            # Helper lists for later access
            track_info = []
            video_info = []
            
            # Build score matrix
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
            
                    # Duration filter: reject videos with extreme duration differences
                    if track_duration and video_duration:
                        duration_ratio = video_duration / track_duration if track_duration > 0 else float('inf')
                        if duration_ratio > 2.0 or duration_ratio < 0.5:
                            # Video is more than double or less than half the track duration - completely exclude
                            logger.debug(f"Rejecting video '{video_title}' for track '{track_title}': "
                                       f"duration ratio {duration_ratio:.2f} (video: {video_duration}s, track: {track_duration}s)")
                            score = float('inf')  # Use infinity to completely exclude from Hungarian algorithm
                        else:
                            # Normal scoring with duration consideration
                            title_score = fuzz.WRatio(track_title.lower(), video_title.lower())
                            title_artist_score = fuzz.WRatio(f"{track_title.lower()} - {track_artist.lower()}", video_title.lower())
                            diff = abs(track_duration - video_duration)
                            duration_score = max(0, 100 - (diff / max(track_duration, 1)) * 100)  # Scale to 0-100
                            score = title_score + title_artist_score + duration_score
                    else:
                        # No duration info available - use only title/artist scoring
                        title_score = fuzz.WRatio(track_title.lower(), video_title.lower())
                        title_artist_score = fuzz.WRatio(f"{track_title.lower()} - {track_artist.lower()}", video_title.lower())
                        score = title_score + title_artist_score
            
                    score_matrix[i][j] = score if score != float('inf') else float('inf')  # Keep infinity for excluded matches
            
            # Check if the matrix is solvable - Hungarian algorithm fails when there are more tracks than videos
            # or when too many entries are infinite
            try:
                # Calculate optimal matching
                track_indices, video_indices = linear_sum_assignment(score_matrix)
                assignment_successful = True
            except ValueError as e:
                logger.warning(f"Hungarian algorithm failed: {e}")
                logger.warning("Creating empty matches for all tracks")
                assignment_successful = False
                
                # Create empty matches for all tracks
                for i, (track_title, track_duration, track_position) in enumerate(track_info):
                    self.matches.append({
                        'discogs_track': track_title,
                        'discogs_duration': track_duration,
                        'track_position': track_position,
                        'youtube_match': None,
                        'match_score': 0.0
                    })
            
            if assignment_successful:
                
                # Save results - exclude tracks with no valid matches (infinity scores)
                for i, j in zip(track_indices, video_indices):
                    track_title, track_duration, track_position = track_info[i]
                    
                    # Check if this assignment has an infinite score (no valid match)
                    if score_matrix[i][j] == float('inf'):
                        logger.warning(f"No valid YouTube match found for track '{track_title}' (all videos rejected by duration filter)")
                        self.matches.append({
                            'discogs_track': track_title,
                            'discogs_duration': track_duration,
                            'track_position': track_position,
                            'youtube_match': None,  # No match
                            'match_score': 0.0
                        })
                    else:
                        matched_video = video_info[j]
                        final_score = score_matrix[i][j]  # Score is already positive now
                        
                        self.matches.append({
                            'discogs_track': track_title,
                            'discogs_duration': track_duration,
                            'track_position': track_position,
                            'youtube_match': matched_video,
                            'match_score': round(final_score, 3)
                        })

            # Save as JSON
            with open(os.path.join(self.release_folder,"yt_matches.json"), "w", encoding="utf-8") as f:
                json.dump(self.matches, f, indent=2, ensure_ascii=False)
        
        # Update original metadata with YouTube durations if Discogs duration is missing
        self.update_metadata_with_youtube_durations()
            
        return
    
    def update_metadata_with_youtube_durations(self):
        """Updates the original metadata with YouTube durations if Discogs duration is missing"""
        metadata_file = os.path.join(self.release_folder, "metadata.json")
        
        if not os.path.exists(metadata_file):
            logger.warning("metadata.json not found - cannot update durations")
            return
            
        # Load original metadata
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata.json: {e}")
            return
            
        # Create a mapping from track position to YouTube duration
        youtube_durations = {}
        for match in self.matches:
            track_pos = match.get('track_position')
            youtube_match = match.get('youtube_match')
            if track_pos and youtube_match and youtube_match.get('length'):
                # Convert seconds to MM:SS format
                duration_seconds = youtube_match['length']
                minutes = duration_seconds // 60
                seconds = duration_seconds % 60
                duration_str = f"{minutes}:{seconds:02d}"
                youtube_durations[track_pos] = duration_str
        
        # Update tracks with missing durations
        updated_count = 0
        for track in metadata.get('tracklist', []):
            track_pos = track.get('position')
            current_duration = track.get('duration')
            
            # If no duration or empty duration is present
            if track_pos and (not current_duration or current_duration.strip() == ''):
                if track_pos in youtube_durations:
                    track['duration'] = youtube_durations[track_pos]
                    updated_count += 1
                    logger.info(f"Updated track {track_pos} duration: {youtube_durations[track_pos]} (from YouTube)")
        
        # Save updated metadata if changes were made
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
            release_folder_name = os.path.basename(self.release_folder)
            logger.info(f"[{release_folder_name}] Download phase complete. Starting parallel analysis for {len(downloaded_tracks)} tracks...")
            self._parallel_audio_analysis(downloaded_tracks)
        
        release_folder_name = os.path.basename(self.release_folder)
        logger.success(f"[{release_folder_name}] Audio download and analysis completed for {len(downloaded_tracks)} tracks")
        return
    
    def audio_download_only(self, release_metadata):
        """Downloads audio for matched tracks without analysis (download-only mode)"""
        
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
        
        # Download phase - without analysis
        downloaded_tracks = []
        release_folder_name = os.path.basename(self.release_folder)
        
        for i, match in enumerate(self.matches):
            if match["youtube_match"] is None:
                logger.warning(f"[{release_folder_name}] No YouTube match for track {match.get('track_position', i)}")
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
                logger.info(f"[{release_folder_name}] Audio file already exists for track {track_position}: {os.path.basename(existing_file)}")
                downloaded_tracks.append((track_filename_base, track_position))
                continue
            
            url = match["youtube_match"]["url"]
            ytdl_opts['outtmpl'] = track_filename_base + '.%(ext)s'
            
            try:
                logger.process(f"[{release_folder_name}] Downloading audio for track {track_position}: {match['discogs_track']}")
                
                with YoutubeDL(ytdl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    
                # Verify download completed
                downloaded_file = self.get_downloaded_audio_file(track_filename_base)
                if downloaded_file:
                    logger.success(f"[{release_folder_name}] Downloaded: {os.path.basename(downloaded_file)}")
                    downloaded_tracks.append((track_filename_base, track_position))
                else:
                    logger.error(f"[{release_folder_name}] Download failed for track {track_position} - no file found")
                    
            except Exception as e:
                logger.error(f"[{release_folder_name}] Download error for track {track_position}: {e}")
                continue
        
        logger.success(f"[{release_folder_name}] Audio download completed for {len(downloaded_tracks)} tracks (no analysis)")
        return
    
    def _parallel_audio_analysis(self, downloaded_tracks):
        """Performs parallel audio analysis using ProcessPoolExecutor (optimized for CPU-bound tasks)"""
        import concurrent.futures
        import time
        
        # Get release info for logging context
        release_folder_name = os.path.basename(self.release_folder)
        
        # Optimal number of processes for CPU-intensive Essentia analysis
        # Use hyperthreading-aware detection for better performance
        optimal_workers, effective_cores, logical_cores, ht_detected = get_optimal_workers(min_workers=1, max_percentage=0.8)
        max_workers = min(len(downloaded_tracks), optimal_workers)
        
        if ht_detected:
            logger.info(f"🔄 [{release_folder_name}] Hyperthreading detected: {logical_cores} logical → {effective_cores} physical cores")
        logger.info(f"🔄 [{release_folder_name}] Starting parallel analysis with {max_workers}/{effective_cores} processes")
        analysis_start = time.time()
        
        # Prepare data for parallel processing
        analysis_tasks = []
        for track_filename_base, track_position in downloaded_tracks:
            audio_file = self.get_downloaded_audio_file(track_filename_base)
            if audio_file:
                analysis_tasks.append({
                    'audio_file': audio_file,
                    'track_filename_base': track_filename_base,
                    'track_position': track_position,
                    'release_info': release_folder_name
                })
        
        if not analysis_tasks:
            logger.warning("No audio files found for analysis")
            return
        
        # Use ProcessPoolExecutor for CPU-intensive Essentia analysis
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Start all analysis tasks
            future_to_track = {
                executor.submit(_analyze_track_standalone, task): task['track_position']
                for task in analysis_tasks
            }
            
            # Collect results
            results = []
            for future in concurrent.futures.as_completed(future_to_track):
                track_position = future_to_track[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        if result['error'] != 'Already analyzed':
                            logger.success(f"✅ [{release_folder_name}] Track {result['track']} analyzed in {result['duration']:.2f}s")
                    else:
                        logger.error(f"❌ [{release_folder_name}] Track {result['track']} failed: {result['error']}")
                        
                except Exception as e:
                    logger.error(f"❌ [{release_folder_name}] Track {track_position} crashed: {e}")
                    results.append({
                        'track': track_position,
                        'success': False,
                        'duration': 0,
                        'error': f"Execution error: {e}"
                    })
        
        # Performance statistics
        total_time = time.time() - analysis_start
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        avg_time = sum(r['duration'] for r in results if r['success']) / max(successful, 1)
        
        logger.info(f"📊 [{release_folder_name}] Parallel Analysis Results:")
        logger.info(f"   ✅ Successful: {successful}/{len(downloaded_tracks)} tracks")
        logger.info(f"   ❌ Failed: {failed} tracks")
        logger.info(f"   ⏱️  Total time: {total_time:.2f}s")
        logger.info(f"   📈 Average per track: {avg_time:.2f}s")
        logger.info(f"   🚀 Parallel speedup: ~{len(downloaded_tracks) * avg_time / max(total_time, 0.1):.1f}x faster than sequential")



    def download_and_stream_audio(self, youtube_url, output_path="output.ogg"):
        # 1. Extract info only, don't save file
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
        
        # 2. ffmpeg: PCM + Save as OGG simultaneously
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
            '-ar', '22050',          # Sample rate for librosa (smaller = faster)
            'pipe:1'                 # PCM to stdout
        ]
             
        logger.process("Running ffmpeg...")
         
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
         
        # 3. Read PCM data & convert to NumPy array
        raw_audio = process.stdout.read()
        audio_array = np.frombuffer(raw_audio, dtype=np.float32)
         
        # 4. Calculate BPM with librosa
        logger.analyze("Analyzing BPM...")
        tempo, _ = librosa.beat.beat_track(y=audio_array, sr=22050)
        logger.info(f"Estimated BPM: {round(tempo)}")
         
        process.stdout.close()
        process.wait()
         
        return round(tempo)
    
    def analyze_downloaded_track(self, track_filename_base, track_position):
        """Analyzes a downloaded track with Essentia"""
        # Skip if audio analysis not available
        if not analyzeAudioFileOrStream:
            logger.debug(f"Skipping analysis for track {track_position} - audio analysis not available")
            return True  # Return True to avoid blocking workflow

        try:
            # Find the actually downloaded file
            audio_file = self.get_downloaded_audio_file(track_filename_base)

            if not audio_file:
                logger.warning(f"No audio file found for track {track_position}")
                return False

            # Check which analyses are still missing
            json_file = f"{track_filename_base}.json"
            waveform_file = f"{track_filename_base}_waveform.png"

            analysis_exists = os.path.exists(json_file)
            waveform_exists = os.path.exists(waveform_file)

            if analysis_exists and waveform_exists:
                logger.info(f"Audio analysis and waveform already exist for track {track_position}")
                return True

            # Show what still needs to be done
            todo_items = []
            if not analysis_exists:
                todo_items.append("Essentia analysis")
            if not waveform_exists:
                todo_items.append("waveform generation")
            logger.info(f"Running {', '.join(todo_items)} for track {track_position}")

            # Wait briefly if file is still being written
            import time
            time.sleep(0.5)

            # Check file size (should be > 0)
            if os.path.getsize(audio_file) == 0:
                logger.error(f"Audio file is empty for track {track_position}: {audio_file}")
                return False

            # Create analyzer-Instanz
            analyzer = analyzeAudioFileOrStream(
                fileOrStream=audio_file,
                sampleRate=44100,
                plotWaveform=False,  # Wird separat gehandhabt
                musicExtractor=True,
                plotSpectogram=True,
                debug=False
            )
            
            success = True
            
            # Perform Essentia analysis (if not already exists)
            if not analysis_exists:
                try:
                    logger.analyze(f"Running Essentia analysis: {os.path.basename(audio_file)}")
                    analyzer.readAudioFile(ffmpegUsage=False)
                    analyzer.analyzeMusicExtractor()
                    logger.success(f"Essentia analysis completed for track {track_position}")
                except Exception as e:
                    logger.error(f"Essentia analysis failed for track {track_position}: {e}")
                    success = False
            
            # Perform waveform generation (if not already exists)
            if not waveform_exists:
                try:
                    # Waveform generation for all tracks with gnuplot
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
        """Finds the downloaded audio file (yt-dlp adds various extensions)"""
        for ext in ['.ogg', '.m4a', '.mp3', '.webm', '.opus']:
            potential_file = f"{track_filename_base}{ext}"
            if os.path.exists(potential_file):
                return potential_file
        return None
