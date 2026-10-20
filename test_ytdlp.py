import yt_dlp

def test_download():
    ydl_opts = {
        'quiet': False,
        'extractor_args': {'youtube': ['player_client=android,web']}
    }
    url = "https://www.youtube.com/watch?v=WZYUSaHlGlk"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            print("Title:", info.get('title'))
            # print("Stream URL:", info.get('url'))
            
            # Let's check for manifest or specific formats
            if 'url' in info:
                print("Default URL:", info['url'])
                
            for fmt in info.get('formats', []):
                if 'manifest_url' in fmt:
                    print("Manifest URL in format:", fmt['format_id'], fmt['manifest_url'])
                    
            print("Manifest url in info:", info.get('manifest_url'))

            
    except Exception as e:
        print("Error:", e)

test_download()
