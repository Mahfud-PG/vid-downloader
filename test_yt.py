import sys, traceback
with open('yt_test.log', 'w') as f:
    try:
        f.write('Importing...\n')
        from ytmusicapi import YTMusic
        f.write('Instantiating...\n')
        yt = YTMusic()
        f.write('Searching...\n')
        res = yt.search('slank', filter='albums')
        f.write(f'Got {len(res)} results.\n')
    except Exception as e:
        traceback.print_exc(file=f)
