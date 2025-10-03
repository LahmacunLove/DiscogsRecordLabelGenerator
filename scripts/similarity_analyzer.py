#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Song Similarity Analyzer - Vergleicht Audio-Features zwischen Tracks

Nutzt Essentia MusicExtractor Features um die Ähnlichkeit zwischen Songs
zu bestimmen basierend auf:
- Rhythmus (BPM, Beat-Stärke)
- Tonalität (Key, Chroma-Features)
- Spektrale Features (Brightness, Rolloff, etc.)
- Dynamik (RMS, Zero-Crossing-Rate)

@author: ffx
"""

import json
import numpy as np
import sys
import os
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean

# Füge src/ zum Python-Pfad hinzu (go up one level from scripts/ to project root)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import load_config
from logger import logger


class SongSimilarityAnalyzer:
    def __init__(self, library_path):
        self.library_path = Path(library_path).expanduser()
        self.feature_weights = {
            "rhythmic": 0.3,  # BPM, Beat-Features
            "tonal": 0.3,  # Key, Chroma-Features
            "spectral": 0.25,  # Brightness, Rolloff, MFCC
            "dynamic": 0.15,  # RMS, ZCR, Dynamics
        }

    def load_track_features(self, release_folder, track_position):
        """Lädt Essentia-Features für einen Track"""
        try:
            feature_file = release_folder / f"{track_position}.json"
            if not feature_file.exists():
                return None

            with open(feature_file, "r", encoding="utf-8") as f:
                features = json.load(f)
            return features
        except Exception as e:
            print(f"Fehler beim Laden von {feature_file}: {e}")
            return None

    def extract_feature_vector(self, essentia_features):
        """Extrahiert relevante Features für Ähnlichkeitsvergleich"""
        if not essentia_features:
            return None

        try:
            # Rhythmic Features
            rhythmic = [
                essentia_features.get("rhythm", {}).get("bpm", 0),
                essentia_features.get("rhythm", {}).get("beats_count", 0),
                essentia_features.get("rhythm", {})
                .get("beats_loudness", {})
                .get("mean", 0),
                essentia_features.get("rhythm", {}).get("onset_rate", 0),
            ]

            # Tonal Features
            tonal = [
                essentia_features.get("tonal", {})
                .get("key_temperley", {})
                .get("key", 0),
                essentia_features.get("tonal", {})
                .get("key_temperley", {})
                .get("scale", 0),
                essentia_features.get("tonal", {})
                .get("chords_strength", {})
                .get("mean", 0),
                essentia_features.get("tonal", {})
                .get("hpcp", {})
                .get("mean", [0] * 36)[:12],  # Nur erste 12 HPCP bins
            ]
            # HPCP array flach machen
            if isinstance(tonal[-1], list):
                tonal = tonal[:-1] + tonal[-1]

            # Spectral Features
            spectral = [
                essentia_features.get("lowlevel", {})
                .get("spectral_centroid", {})
                .get("mean", 0),
                essentia_features.get("lowlevel", {})
                .get("spectral_rolloff", {})
                .get("mean", 0),
                essentia_features.get("lowlevel", {})
                .get("spectral_flux", {})
                .get("mean", 0),
                essentia_features.get("lowlevel", {})
                .get("mfcc", {})
                .get("mean", [0] * 13)[:5],  # Erste 5 MFCC
            ]
            # MFCC array flach machen
            if isinstance(spectral[-1], list):
                spectral = spectral[:-1] + spectral[-1]

            # Dynamic Features
            dynamic = [
                essentia_features.get("lowlevel", {}).get("average_loudness", 0),
                essentia_features.get("lowlevel", {}).get("dynamic_complexity", 0),
                essentia_features.get("lowlevel", {})
                .get("zerocrossingrate", {})
                .get("mean", 0),
            ]

            # Alle Features zusammenfügen
            feature_vector = rhythmic + tonal + spectral + dynamic

            # None-Werte durch 0 ersetzen
            feature_vector = [0 if x is None else x for x in feature_vector]

            return np.array(feature_vector, dtype=float)

        except Exception as e:
            print(f"Fehler beim Extrahieren der Features: {e}")
            return None

    def find_all_tracks(self):
        """Findet alle verfügbaren Tracks in der Library"""
        tracks = []

        if not self.library_path.exists():
            print(f"Library-Pfad existiert nicht: {self.library_path}")
            return tracks

        for release_folder in self.library_path.iterdir():
            if release_folder.is_dir() and "_" in release_folder.name:
                # Lade Release-Metadaten
                metadata_file = release_folder / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)

                        # Finde alle JSON-Feature-Dateien
                        for track in metadata.get("tracklist", []):
                            position = track.get("position", "")
                            feature_file = release_folder / f"{position}.json"

                            if feature_file.exists():
                                tracks.append(
                                    {
                                        "release_id": metadata.get("id"),
                                        "release_title": metadata.get("title"),
                                        "artist": metadata.get("artist", []),
                                        "track_position": position,
                                        "track_title": track.get("title"),
                                        "track_artist": track.get("artist"),
                                        "release_folder": release_folder,
                                        "feature_file": feature_file,
                                    }
                                )
                    except Exception as e:
                        print(f"Fehler beim Lesen von {metadata_file}: {e}")

        return tracks

    def calculate_similarity(self, track1_features, track2_features, method="cosine"):
        """Berechnet Ähnlichkeit zwischen zwei Feature-Vektoren"""
        if track1_features is None or track2_features is None:
            return 0.0

        # Ensure same length
        min_len = min(len(track1_features), len(track2_features))
        features1 = track1_features[:min_len]
        features2 = track2_features[:min_len]

        try:
            if method == "cosine":
                # Reshape für sklearn
                features1 = features1.reshape(1, -1)
                features2 = features2.reshape(1, -1)
                similarity = cosine_similarity(features1, features2)[0][0]
                return max(0, similarity)  # Negative Werte auf 0 setzen

            elif method == "euclidean":
                distance = euclidean(features1, features2)
                # In Ähnlichkeit umwandeln (kleiner Abstand = höhere Ähnlichkeit)
                similarity = 1 / (1 + distance)
                return similarity

        except Exception as e:
            print(f"Fehler bei Ähnlichkeitsberechnung: {e}")
            return 0.0

    def find_similar_tracks(self, target_track_path, num_results=10, method="cosine"):
        """Findet ähnliche Tracks zu einem gegebenen Track"""

        # Target Track Features laden
        if isinstance(target_track_path, str):
            target_track_path = Path(target_track_path)

        target_features_raw = None
        with open(target_track_path, "r", encoding="utf-8") as f:
            target_features_raw = json.load(f)

        target_features = self.extract_feature_vector(target_features_raw)
        if target_features is None:
            print("Konnte Features vom Target-Track nicht extrahieren")
            return []

        # Alle verfügbaren Tracks finden
        all_tracks = self.find_all_tracks()
        similarities = []

        for track in all_tracks:
            # Skip den Target-Track selbst
            if track["feature_file"] == target_track_path:
                continue

            # Features laden und vergleichen
            track_features_raw = self.load_track_features(
                track["release_folder"], track["track_position"]
            )
            track_features = self.extract_feature_vector(track_features_raw)

            similarity = self.calculate_similarity(
                target_features, track_features, method
            )

            similarities.append({"track": track, "similarity": similarity})

        # Nach Ähnlichkeit sortieren (absteigend)
        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        return similarities[:num_results]

    def get_track_info_by_file(self, feature_file_path):
        """Holt Track-Informationen basierend auf Feature-File-Pfad"""
        try:
            feature_file = Path(feature_file_path)
            release_folder = feature_file.parent
            track_position = feature_file.stem

            metadata_file = release_folder / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                for track in metadata.get("tracklist", []):
                    if track.get("position") == track_position:
                        return {
                            "release_id": metadata.get("id"),
                            "release_title": metadata.get("title"),
                            "artist": metadata.get("artist", []),
                            "track_position": track_position,
                            "track_title": track.get("title"),
                            "track_artist": track.get("artist"),
                            "release_folder": release_folder,
                        }
        except Exception as e:
            print(f"Fehler beim Holen der Track-Info: {e}")
        return None

    def analyze_collection_similarities(self, output_file=None):
        """Analysiert Ähnlichkeiten in der gesamten Collection"""
        all_tracks = self.find_all_tracks()
        print(f"Analysiere {len(all_tracks)} Tracks...")

        similarity_matrix = []

        for i, track1 in enumerate(all_tracks):
            print(
                f"Verarbeite Track {i + 1}/{len(all_tracks)}: {track1['track_title']}"
            )

            track1_features_raw = self.load_track_features(
                track1["release_folder"], track1["track_position"]
            )
            track1_features = self.extract_feature_vector(track1_features_raw)

            if track1_features is None:
                continue

            for j, track2 in enumerate(all_tracks[i + 1 :], i + 1):
                track2_features_raw = self.load_track_features(
                    track2["release_folder"], track2["track_position"]
                )
                track2_features = self.extract_feature_vector(track2_features_raw)

                similarity = self.calculate_similarity(track1_features, track2_features)

                similarity_matrix.append(
                    {"track1": track1, "track2": track2, "similarity": similarity}
                )

        # Nach Ähnlichkeit sortieren
        similarity_matrix.sort(key=lambda x: x["similarity"], reverse=True)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(
                    similarity_matrix[:100], f, indent=2, ensure_ascii=False
                )  # Top 100

        return similarity_matrix


def main():
    """Test-Funktion"""
    from config import load_config

    config = load_config()
    library_path = config["LIBRARY_PATH"]

    analyzer = SongSimilarityAnalyzer(library_path)

    # Finde alle Tracks
    tracks = analyzer.find_all_tracks()
    print(f"Gefunden: {len(tracks)} Tracks")

    if tracks:
        # Test: Ähnliche Tracks zum ersten Track finden
        first_track = tracks[0]
        print(
            f"\nSuche ähnliche Tracks zu: {first_track['track_title']} - {first_track['release_title']}"
        )

        similar = analyzer.find_similar_tracks(
            first_track["feature_file"], num_results=5
        )

        print("\nÄhnliche Tracks:")
        for i, result in enumerate(similar, 1):
            track = result["track"]
            similarity = result["similarity"]
            print(
                f"{i}. {track['track_title']} - {track['release_title']} (Ähnlichkeit: {similarity:.3f})"
            )


if __name__ == "__main__":
    main()
