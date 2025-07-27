#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified logging system for DiscogsRecordLabelGenerator

@author: ffx
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

class DiscogsLogger:
    def __init__(self, name="DiscogsRecordLabelGenerator", level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Verhindere doppelte Handler
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup console und file handlers"""
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # File Handler (optional)
        log_dir = Path.home() / ".config" / "discogsDBLabelGen" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"discogs_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Formatter
        console_formatter = logging.Formatter(
            '%(levelname)s │ %(message)s'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s │ %(name)s │ %(levelname)s │ %(message)s'
        )
        
        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def info(self, message):
        self.logger.info(message)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def success(self, message):
        self.logger.info(f"✅ {message}")
    
    def process(self, message):
        self.logger.info(f"🔄 {message}")
    
    def download(self, message):
        self.logger.info(f"⬇️  {message}")
    
    def analyze(self, message):
        self.logger.info(f"🎵 {message}")
    
    def match(self, message):
        self.logger.info(f"🔗 {message}")
    
    def separator(self, title=None):
        if title:
            self.logger.info(f"\n{'─' * 50}")
            self.logger.info(f"  {title}")
            self.logger.info(f"{'─' * 50}")
        else:
            self.logger.info(f"{'─' * 50}")

# Global logger instance
logger = DiscogsLogger()