import urllib.request
import re

url = 'https://www.youtube.com/results?search_query=muse+absolution+playlist'
html = urllib.request.urlopen(url).read().decode('utf-8')
match = re.search(r'"playlistId":"(PL[^"]+)"', html)
if match:
    print('https://www.youtube.com/playlist?list=' + match.group(1))
else:
    match = re.search(r'"playlistId":"(OLAK5uy_[^"]+)"', html)
    if match:
        print('https://www.youtube.com/playlist?list=' + match.group(1))
    else:
        print('Not found')
