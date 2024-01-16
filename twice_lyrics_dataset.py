#%%
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import numpy as np

#%%
# Getting all album titles, publication years and urls of each song.

all_songs = 'https://www.azlyrics.com/t/twice.html'

albums = requests.get(all_songs)
soup = BeautifulSoup(albums.content.decode('utf-8'), 'html.parser')
albums.close()

albumList = soup.findAll('div', attrs={'id':'listAlbum'})

# fixing some characters
newlist = str(albumList).replace('&amp;', '&').replace('˂','<').split('div class="album"')

#%%
# Under I'm listing all albums where one list element is an album [name, year, [list of songs].

all_albums = []
one_album = []

for i in newlist:
    
    if '<b>\"' in i:
        tup1 = re.findall(r'<b>"(.*?)"</b> [(](.*?)[)]<div>', i)
        one_album.append(tup1[0][0]) # name
        one_album.append(tup1[0][1]) # year
    
    if 'href="/lyrics' in i:
        tup2 = re.findall(r'href="/(.*?)" tar', i)
        one_album.append(tup2) # url to song list

    if one_album != []:
        all_albums.append(one_album)
    one_album = []

#%%
# Some published songs don't belong to any album. 
# Those songs are all in the same list, which is the last element in all_albums, and that list item does not have album name nor year.

number_of_songs = 0

for album in all_albums:
    for song in album[len(album)-1]:
        number_of_songs += 1
print('Number of songs:', number_of_songs)

#%%
# The final dataframe
df = pd.DataFrame(columns=['Album','Year','Song','url','Romanized_lyrics','Korean_lyrics','Japanese_lyrics','English_lyrics'])

#%%
album_list_index = 0
homepage = 'https://www.azlyrics.com/'

for a in range(0,len(all_albums)):
    
    if a == (len(all_albums)-1): 
    # This statement is needed for the last item in all_albums, which is just the song list
        album = all_albums[a]
        album_title = np.nan  # no album name
        year = np.nan         # no album year
        album_list_index = 0
        
    else: # This is the normal case
        album = all_albums[a]
        album_title = album[0]
        year = album[1]
        album_list_index = 2

    for url in album[album_list_index]: # For song in an album
        
        page = requests.get(homepage + url)
        soup = BeautifulSoup(page.content.decode('utf-8'), "html.parser")
        page.close()
        
        # lyrics
        lyrics = soup.findAll('div', attrs={'class':'col-xs-12 col-lg-8 text-center'})
        str_lyrics = str(lyrics)
        
        # song title 
        title = soup.findAll('h1')
        title = str(title).split('\"')[1]
        og_title = title
        title = title.replace('&amp;', '&').replace('˂','<')
        
        onlyenglish = np.nan
        romanized = np.nan
        korean = np.nan
        japanese= np.nan
        english= np.nan
        
        # This part of the code seems quite clumsy, but the format on the web page sometimes changes depending on
        # the song or available lyrics, and this is the best I came up with so far without having to
        # detect languages. Different lyrics are processed in the order where they usually appear. Variable
        # 'onlyenglish' is used for English songs, because the html format is slightly different for those.
        
        if '[Romanized' in str_lyrics:
            rom_lyr = str_lyrics
            rom_l = rom_lyr.split('[Romanized')
            rom_lyr = rom_l[1] 
            rom_lyr = rom_lyr.split('</div>')[0]
            if 'Korean' or 'English' or 'Japanese' in rom_lyr:
                rom_lyr = rom_lyr.split('[')[0]
            final_rom_lyr = re.sub('<.*>', '', rom_lyr).strip()
            final_rom_lyr = final_rom_lyr.strip(':').strip(']').strip()
            romanized = final_rom_lyr

        if '[Korean' in str_lyrics:
            kor_lyr = str_lyrics
            kor_l = kor_lyr.split('[Korean')
            kor_lyr = kor_l[1] 
            kor_lyr = kor_lyr.split('</div>')[0]
            if '[English' in kor_lyr:
                kor_lyr = kor_lyr.split('[E')[0]
            final_kor_lyr = re.sub('<.*>', '', kor_lyr).strip()
            final_kor_lyr = final_kor_lyr.strip(':').strip(']').strip()
            korean = final_kor_lyr

        if '[Japanese' in str_lyrics:
            jap_lyr = str_lyrics
            jap_l = jap_lyr.split('[Japanese')
            jap_lyr = jap_l[1] 
            jap_lyr = jap_lyr.split('</div>')[0]
            if '[English' in jap_lyr:
                jap_lyr = jap_lyr.split('[E')[0]
            final_jap_lyr = re.sub('<.*>', '', jap_lyr).strip()
            final_jap_lyr = final_jap_lyr.strip(':').strip(']').strip()
            japanese = final_jap_lyr

        if '[English' in str_lyrics:
            eng_lyr = str_lyrics
            eng_l = eng_lyr.split('[English')
            eng_lyr = eng_l[len(eng_l)-1] 
            eng_lyr = eng_lyr.split(']')[1] 
            eng_lyr = eng_lyr.split('</div>')[0]
            final_eng_lyr = re.sub('<.*>', '', eng_lyr).strip()
            final_eng_lyr = final_eng_lyr.strip(':').strip(']').strip()
            english = final_eng_lyr
    
        if english == np.nan and ('[Romanized' not in str_lyrics):
            lyr = str_lyrics
            l = lyr.split('<b>"' + og_title + '"</b><br/>')
            lyr = l[1]
            lyr = lyr.split('</div>')[0]
            final_lyr = re.sub('<.*>', '', lyr).strip()
            final_lyr = final_lyr.strip(':').strip(']').strip()
            onlyenglish = final_lyr
        
            data_item = [album_title, year, title, homepage + url, romanized, korean, japanese, onlyenglish]
        else:
            data_item = [album_title, year, title, homepage + url, romanized, korean, japanese, english]
            
        df.loc[len(df.index)] = data_item
        
        time.sleep(5)
        print(album_title,'-',title)
        print('Songs left:', number_of_songs - len(df))

#%%
df.to_csv('twice_lyrics_dataset.csv', index=False)

#%%
# Some examples:

# English lyrics for Cheer up
print(df['English_lyrics'].iloc[6])

#%%
# Korean lyrics for TT
print(df.iloc[13,5])
        
