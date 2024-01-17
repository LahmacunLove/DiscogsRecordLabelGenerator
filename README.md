# DiscogsRecordLabeler
This Python script is designed for crawling your Discogs library using the Discogs API and the discogs_client module for Python with your user token. It generates printable 8163 shipping labels for your home printer.

The script utilizes various Python modules for tasks such as matching and downloading YouTube videos, music analysis, and BPM and key analysis.

The following subprocesses are employed: pdfLaTeX, ffmpeg, and gnuplot.

It is compatible with Linux and has not been tested on other platforms, but it should be straightforward to set up on any Unix system.

Some adjustments may be necessary for the PDF output, as there are still formatting issues, as evident in the image below.
Also the speed is quite slow, when downloading all the youtubevideos and also the discogs api got some delays for security reasons to prevent (DDoS) attacks - for bigger library its better to run over night.
Im also working on some routines to prevent analyzing and downloading already existing data or reprint stickers for already printed records. If you have ideas, hit me up, i was thinking about simple timestamps.


![image](https://github.com/LahmacunLove/DiscogsRecordLabeler/blob/master/output.jpg)
