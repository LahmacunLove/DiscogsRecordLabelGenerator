#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR Code Generator for Discogs Releases

Erstellt QR-Codes mit Cover-Hintergrund für Discogs-Releases
Basierend auf der originalen createQRCode Funktion mit modernen Verbesserungen

@author: ffx
"""

import os
import shutil
from logger import logger

def generate_qr_code(release_folder, release_id, cover_file=None):
    """
    Generiert QR-Code für ein Discogs Release
    
    Args:
        release_folder: Pfad zum Release-Ordner
        release_id: Discogs Release ID
        cover_file: Pfad zum Cover-Bild (optional, wird automatisch gesucht)
    
    Returns:
        bool: True wenn erfolgreich, False bei Fehlern
    """
    
    # Prüfe ob segno verfügbar ist
    try:
        import segno
    except ImportError:
        logger.warning("segno library not installed - skipping QR code generation")
        logger.info("Install with: pip install segno")
        return False
    
    qr_file = os.path.join(release_folder, 'qrcode.png')
    
    # Prüfe ob QR-Code bereits existiert
    if os.path.exists(qr_file):
        logger.debug(f"QR code already exists: {os.path.basename(qr_file)}")
        return True
    
    # Finde Cover-Datei falls nicht angegeben
    if not cover_file:
        cover_file = os.path.join(release_folder, 'cover.jpg')
    
    try:
        logger.process(f"Generating QR code for release {release_id}")
        
        # Erstelle QR-Code mit Discogs-URL
        discogs_url = f'https://discogs.com/release/{release_id}'
        qr_code = segno.make_qr(discogs_url, error='l')  # Low error correction für mehr Daten
        
        # Generiere QR-Code mit Cover als Hintergrund (falls Cover existiert)
        if os.path.exists(cover_file):
            logger.debug(f"Using cover as background: {os.path.basename(cover_file)}")
            qr_code.to_artistic(
                background=cover_file,
                target=qr_file,
                scale=10,
                border=2  # Kleiner Border für bessere Lesbarkeit
            )
            logger.success(f"Artistic QR code with cover created: {os.path.basename(qr_file)}")
        else:
            # Fallback: Einfacher QR-Code ohne Cover
            logger.debug("No cover found - creating simple QR code")
            qr_code.save(
                qr_file,
                scale=10,
                border=2,
                dark='black',
                light='white'
            )
            logger.success(f"Simple QR code created: {os.path.basename(qr_file)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating QR code for release {release_id}: {e}")
        return False

def generate_qr_code_advanced(release_folder, release_id, metadata=None):
    """
    Erweiterte QR-Code Generation mit zusätzlichen Features
    
    Args:
        release_folder: Pfad zum Release-Ordner  
        release_id: Discogs Release ID
        metadata: Optional - Release-Metadaten für erweiterte QR-Codes
        
    Returns:
        bool: True wenn erfolgreich, False bei Fehlern
    """
    
    try:
        import segno
    except ImportError:
        logger.warning("segno library not installed - skipping QR code generation")
        return False
    
    qr_file = os.path.join(release_folder, 'qrcode.png')
    
    if os.path.exists(qr_file):
        logger.debug(f"QR code already exists: {os.path.basename(qr_file)}")
        return True
    
    try:
        logger.process(f"Generating advanced QR code for release {release_id}")
        
        # Erweiterte URL mit mehr Informationen
        discogs_url = f'https://discogs.com/release/{release_id}'
        
        # Erweiterte QR-Code Optionen für bessere Lesbarkeit
        qr_code = segno.make_qr(
            discogs_url, 
            error='m',  # Medium error correction (balance zwischen Daten und Korrektur)
            micro=False  # Keine Micro QR-Codes für bessere Kompatibilität
        )
        
        cover_file = os.path.join(release_folder, 'cover.jpg')
        
        if os.path.exists(cover_file):
            # Artistic QR mit optimierten Einstellungen
            qr_code.to_artistic(
                background=cover_file,
                target=qr_file,
                scale=12,  # Etwas größer für bessere Scannbarkeit
                border=3,  # Größerer Border für bessere Erkennung
                dark='#000000',
                light='#FFFFFF'
            )
            logger.success(f"Advanced artistic QR code created: {os.path.basename(qr_file)}")
        else:
            # Hochwertiger einfacher QR-Code
            qr_code.save(
                qr_file,
                scale=12,
                border=3,
                dark='#000000',
                light='#FFFFFF'
            )
            logger.success(f"Advanced simple QR code created: {os.path.basename(qr_file)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating advanced QR code: {e}")
        return False

def check_qr_dependencies():
    """Prüft ob QR-Code Dependencies verfügbar sind"""
    try:
        import segno
        logger.info("✅ segno library available for QR code generation")
        return True
    except ImportError:
        logger.warning("❌ segno library not installed")
        logger.info("💡 Install with: pip install segno")
        return False