# DiscogsRecordLabeler

## Overview

This Python script is designed for crawling your Discogs library using the Discogs API and the discogs_client module for Python. It generates printable 8163 shipping labels for your home printer.

## Features

The script utilizes various Python modules for tasks such as:

- Matching and downloading YouTube videos
- Music analysis
- BPM and key analysis

## Subprocesses

The following subprocesses are employed:

- `pdfLaTeX`
- `ffmpeg`
- `gnuplot`

## Platform Compatibility

It is compatible with Linux and has not been tested on other platforms, but it should be straightforward to set up on any Unix system.

## Open Tasks 
Some adjustments may be necessary for the PDF output, as there are still formatting issues, as evident in the image below.
Also the speed is quite slow, when downloading all the youtubevideos and also the discogs api got some delays for security reasons to prevent (DDoS) attacks - for bigger library its better to run over night.
Im also working on some routines to prevent analyzing and downloading already existing data or reprint stickers for already printed records. If you have ideas, hit me up, i was thinking about simple timestamps.

## How to run

- clone the repository
- create token for your profile on discogs (somewhere in your profile settings)
- paste token in `$HOME/.config/discogs_token`
- run main.py via python 3 interpreter
- probably you have to install some missing pythonpackages, preferably with pip.

![image](https://github.com/LahmacunLove/DiscogsRecordLabeler/blob/master/output.jpg)
