#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 26 14:22:29 2023

@author: ffx
"""
import os
import sys
import discogs_client
from discogs_client.exceptions import HTTPError
import urllib.request
import numpy as np
import pandas as pd

script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
databaseDIR = os.path.dirname(os.path.abspath(sys.argv[0])) + '/' + 'database'

saveToDisk=True
DownloadCoverImage=True

# Consumer-Key 	mrBDnMaMVslFnyOEYBFa
# Consumer-Secret 	
# Token-URL anfragen 	https://api.discogs.com/oauth/request_token
# URL autorisieren 	https://www.discogs.com/de/oauth/authorize
# Auf Token-URL zugreifen 	https://api.discogs.com/oauth/access_token
# consumer_key = ''
# consumer_secret = ''
# user_agent = 'DiscogsRecordLabeler/0.1''

# # A user-agent is required with Discogs API requests. Be sure to make your
# # user-agent unique, or you may get a bad response.
# user_agent = 'discogs_api_example/2.0'

# # instantiate our discogs_client object.
# d = discogs_client.Client(user_agent)

# # prepare the client with our API consumer data.
# d.set_consumer_key(consumer_key, consumer_secret)
# token, secret, url = d.get_authorize_url()

# print(' == Request Token == ')
# print(f'    * oauth_token        = {token}')
# print(f'    * oauth_token_secret = {secret}')
# print()

# # Prompt your user to "accept" the terms of your application. The application
# # will act on behalf of their discogs.com account.
# # If the user accepts, discogs displays a key to the user that is used for
# # verification. The key is required in the 2nd phase of authentication.
# print(f'Please browse to the following URL {url}')

# accepted = 'n'
# while accepted.lower() == 'n':
#     print
#     accepted = input(f'Have you authorized me at {url} [y/n] :')


# # Waiting for user input. Here they must enter the verifier key that was
# # provided at the unqiue URL generated above.
# oauth_verifier = input('Verification code : ')

# try:
#     access_token, access_secret = d.get_access_token(oauth_verifier)
# except HTTPError:
#     print('Unable to authenticate.')
#     sys.exit(1)

# # fetch the identity object for the current logged in user.
# user = d.identity()

print("reading token from local file")
f = open("/home/ffx/.config/discogs_token", "r")
discogs_token=f.read().strip()
f.close()

d = discogs_client.Client('DiscogsRecordLabeler/0.1', user_token=discogs_token)
me = d.identity()

# empty list for gattering all timestamps (for later usage, unsorting already processed elements)
timestamps = []

print(me.collection_folders[5].releases)
test = me.collection_folders[5].releases

start=0
end=1
# for i in range(start, end):
# for i in range(52,len(me.collection_folders[5].releases)):
for i in range(len(me.collection_folders[5].releases)):
    print('\n')
    print(str(i+1)+ ' of ' + str(len(me.collection_folders[5].releases)))
    testrelease = me.collection_folders[5].releases[i].release
    timestamp = me.collection_folders[5].releases[i].date_added
    timestamps.append(timestamp)
    # print(timestamp)
    
    # receive data of testrelease:
    title = testrelease.title
    artists = [r.name for r in testrelease.artists]
    label = [label.name for label in testrelease.labels]
    formats = testrelease.formats[0]
    genres = testrelease.genres
    year = testrelease.year
    releaseid = testrelease.id
    videos = [video.url for video in testrelease.videos]
    
    # generate tracktable:
    tracktable = []
    for track in testrelease.tracklist:
        tracktable.append([track.position, track.title, ','.join([r.name for r in track.artists]),track.duration])
    #convert to pandas:
    tracktable = np.array(tracktable)
    tracktable = pd.DataFrame(tracktable, columns=['pos', 'title', 'artist', 'duration'])
    
        
    
    """ url processing: """
    try:
        imageURL = testrelease.images[0]['uri']
    except:
        imageURL = ''
        
    if saveToDisk:
        #set paths
        pathForExport = databaseDIR + '/' + str(releaseid) 
        if not os.path.exists(pathForExport):
            os.makedirs(pathForExport)
        
        # write cover image:
        try:
            if DownloadCoverImage:
                urllib.request.urlretrieve(imageURL, pathForExport + '/' + 'cover.jpg')
            else:
                pass
        except:
            pass
        
        # write tracktable:
        tracktable.to_csv(pathForExport+ '/' + 'tracktable.csv', index=False)
        # write metadata:        
        f=open(pathForExport + '/' + 'metadata','w')
        f.write('title,' + title + '\n')
        f.write('artist,' + ','.join(artists) +'\n')
        f.write('label,' + ','.join(label)+'\n')
        f.write('genres,' + ', '.join(genres)+'\n')
        f.write('id,' + str(releaseid)+'\n')
        f.write('timestamp,' + str(timestamp)+'\n\n')
        # f.write("#tracklist#\n")
        # f.write("#position, title, artists, duration#\n")
        # for track in tracktable:
            # f.write('-'.join(track) +'\n')
        f.write('\n\n')
        f.write('#videos#\n')
        for video in videos:
            f.write(video)
            f.write('\n')
        f.write('\n\n')
        f.write('#cover#\n')  
        f.write(imageURL + '\n')          
        f.close()
    else:
        pass
    
timestamps.sort()

f=open(databaseDIR + '/' + 'timestampLastCall','w')
f.write(timestamps[-1].strftime("%m/%d/%Y, %H:%M:%S"))
f.close()
