#! /usr/bin/python3
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse

import pytz
print('#EXTINF:-1 tvg-name="Telefe." tvg-logo="https://entretenimiento.flow.com.ar/content/dam/teco-cms-ecosystem/flow/guia-de-canales/35.png" group-title="Nacionales" tvg-id="Telefe.ar",Telefe')
print('https://telefemultieventos3.akamaized.net/hls/live/2041414/multieventos_3_hls/multieventos_3_hls.m3u8')
import requests
from lxml import etree
from bs4 import BeautifulSoup

tz = pytz.timezone('Europe/London')
channels = []


def generate_times(curr_dt: datetime):
    """
Generate 3-hourly blocks of times based on a current date
    :param curr_dt: The current time the script is executed
    :return: A tuple that contains a list of start dates and a list of end dates
    """
    # Floor the last hour (e.g. 13:54:00 -> 13:00:00) and add timezone information
    last_hour = curr_dt.replace(microsecond=0, second=0, minute=0)
    last_hour = tz.localize(last_hour)
    start_dates = [last_hour]

    # Generate start times that are spaced out by three hours
    for x in range(7):
        last_hour += timedelta(hours=3)
        start_dates.append(last_hour)

    # Copy everything except the first start date to a new list, then add a final end date three hours after the last
    # start date
    end_dates = start_dates[1:]
    end_dates.append(start_dates[-1] + timedelta(hours=3))

    return start_dates, end_dates


def build_xml_tv(streams: list) -> bytes:
    """
Build an XMLTV file based on provided stream information
    :param streams: List of tuples containing channel/stream name, ID and category
    :return: XML as bytes
    """
    data = etree.Element("tv")
    data.set("generator-info-name", "youtube-live-epg")
    data.set("generator-info-url", "https://github.com/dp247/YouTubeToM3U8")

    for stream in streams:
        channel = etree.SubElement(data, "channel")
        channel.set("id", stream[1])
        name = etree.SubElement(channel, "display-name")
        name.set("lang", "en")
        name.text = stream[0]

        dt_format = '%Y%m%d%H%M%S %z'
        start_dates, end_dates = generate_times(datetime.now())

        for idx, val in enumerate(start_dates):
            programme = etree.SubElement(data, 'programme')
            programme.set("channel", stream[1])
            programme.set("start", val.strftime(dt_format))
            programme.set("stop", end_dates[idx].strftime(dt_format))

            title = etree.SubElement(programme, "title")
            title.set('lang', 'en')
            title.text = stream[3] if stream[3] != '' else f'LIVE: {stream[0]}'
            description = etree.SubElement(programme, "desc")
            description.set('lang', 'en')
            description.text = stream[4] if stream[4] != '' else 'No description provided'
            icon = etree.SubElement(programme, "icon")
            icon.set('src', stream[5])

    return etree.tostring(data, pretty_print=True, encoding='utf-8')


def grab_youtube(url: str):
    """
Grabs the live-streaming M3U8 file from YouTube
    :param url: The YouTube URL of the livestream
    """
    if '&' in url:
        url = url.split('&')[0]

    requests.packages.urllib3.disable_warnings()
    stream_info = requests.get(url, timeout=15)
    response = stream_info.text
    soup = BeautifulSoup(stream_info.text, features="html.parser")


    if '.m3u8' not in response or stream_info.status_code != 200:
        print("https://github.com/ExperiencersInternational/tvsetup/raw/main/staticch/no_stream_2.mp4")
        return
    end = response.find('.m3u8') + 5
    tuner = 100
    while True:
        if 'https://' in response[end - tuner: end]:
            link = response[end - tuner: end]
            start = link.find('https://')
            end = link.find('.m3u8') + 5

            stream_title = soup.find("meta", property="og:title")["content"]
            stream_desc = soup.find("meta", property="og:description")["content"]
            stream_image_url = soup.find("meta", property="og:image")["content"]
            channels.append((channel_name, channel_id, category, stream_title, stream_desc, stream_image_url))

            break
        else:
            tuner += 5
    print(f"{link[start: end]}")

def grab_dailymotion(url: str):
    """
Grabs the live-streaming M3U8 file from Dailymotion at its best resolution
    :param url: The Dailymotion URL of the livestream
    :return:
    """
    requests.packages.urllib3.disable_warnings()
    stream_info = requests.get(url, timeout=15)
    response = stream_info.text
    soup = BeautifulSoup(stream_info.text, features="html.parser")

    if stream_info.status_code != 200:
        print("https://github.com/ExperiencersInternational/tvsetup/raw/main/staticch/no_stream_2.mp4")
        return

    stream_title = soup.find("meta", property="og:title")["content"].split('-')[0].strip()
    stream_desc = soup.find("meta", property="og:description")["content"]
    stream_image_url = soup.find("meta", property="og:image")["content"]
    channels.append((channel_name, channel_id, category, stream_title, stream_desc, stream_image_url))

    stream_api = requests.get(f"https://www.dailymotion.com/player/metadata/video/{url.split('/')[4]}").json()['qualities']['auto'][0]['url']
    m3u_file = requests.get(stream_api).text.strip().split('\n')[1:]
    best_url = sorted([[int(m3u_file[i].strip().split(',')[2].split('=')[1]), m3u_file[i + 1]] for i in range(0, len(m3u_file) - 1, 2)], key=lambda x: x[0])[-1][1].split('#')[0]
    print(best_url)

def grab_twitch(url: str):
    """

    :param url:
    :return:
    """
    requests.packages.urllib3.disable_warnings()
    stream_info = requests.get(url, timeout=15)
    soup = BeautifulSoup(stream_info.text, features="html.parser")

    if stream_info.status_code != 200:
        print("https://github.com/ExperiencersInternational/tvsetup/raw/main/staticch/no_stream_2.mp4")
        return

    stream_title = soup.find("meta", property="og:title")["content"].split('-')[0].strip()
    stream_desc = soup.find("meta", property="og:description")["content"]
    stream_image_url = soup.find("meta", property="og:image")["content"]
    channels.append((channel_name, channel_id, category, stream_title, stream_desc, stream_image_url))

    response = requests.get(f"https://pwn.sh/tools/streamapi.py?url={url}").json()["success"]
    if response == "false":
        print("https://github.com/ExperiencersInternational/tvsetup/raw/main/staticch/no_stream_2.mp4")
        return
    url_list = requests.get(f"https://pwn.sh/tools/streamapi.py?url={url}").json()["urls"]
    max_res_key = list(url_list)[-1]
    stream_url = url_list.get(max_res_key)
    print(stream_url)

channel_name = ''
stream_image_url = ''
category = ''
channel_id = ''

# Open text file and parse stream information and URL
with open('./ZKL0D600Jd0F7k4dm9o13sL7pDGD8sIIq510p0928JpQ2914912347129866029275628957gu389gii48t8g92oig84y6hy8h83oguh6re9i3orfit4urofg4uurur7salk3jofj39ajlij09409jbhbdfj9d489tjlijhiojh598efjm914D.txt', encoding='utf-8') as f:
    print("#EXTM3U")
    for line in f:
        line = line.strip()
        if not line or line.startswith('##'):
            continue
        if not (line.startswith('https:') or line.startswith('http:')):
            line = line.split('||')
            channel_name = line[0].strip()
            stream_image_url = line[1].strip()
            category = line[2].strip().title()
            channel_id = line[3].strip()
            print(
                f'\n#EXTINF:-1 tvg-name="{channel_name}." tvg-logo="{stream_image_url}" group-title="{category}" tvg-id="{channel_id}",{channel_name}')
        else:
            if urlparse(line).netloc == 'www.youtube.com':
                grab_youtube(line)
            elif urlparse(line).netloc == 'www.dailymotion.com':
                grab_dailymotion(line)
            elif urlparse(line).netloc == 'www.twitch.tv':
                grab_twitch(line)

# Time to build an XMLTV file based on stream data
channel_xml = build_xml_tv(channels)
with open('epg.xml', 'wb') as f:
    f.write(channel_xml)
    f.close()

# Remove temp files from project dir
if 'temp.txt' in os.listdir():
    os.system('rm temp.txt')
    os.system('rm watch*')
print('#EXTINF:-1 tvg-name="TV Pública." tvg-logo="https://entretenimiento.flow.com.ar/content/dam/teco-cms-ecosystem/flow/guia-de-canales/292.png" group-title="Nacionales" tvg-id="TVPublica.ar",TV Pública')
print('http://200.73.141.22/b16/ngrp:c7_vivo01_dai_source-20001_all/Playlist.m3u8')
print('#EXTINF:-1 tvg-name="América TV." tvg-logo="https://entretenimiento.flow.com.ar/content/dam/teco-cms-ecosystem/flow/guia-de-canales/175.png" group-title="Nacionales" tvg-id="AmericaTV.ar",América TV')
print('http://200.73.141.22/a07/americahls-100056/Playlist.m3u8')
print('#EXTINF:-1 tvg-name="Telefe." tvg-logo="https://entretenimiento.flow.com.ar/content/dam/teco-cms-ecosystem/flow/guia-de-canales/35.png" group-title="Nacionales" tvg-id="Telefe.ar",Telefe')
print('https://telefemultieventos3.akamaized.net/hls/live/2041414/multieventos_3_hls/multieventos_3_hls.m3u8')
print('#EXTINF:-1 tvg-name="Net TV." tvg-logo="https://entretenimiento.flow.com.ar/content/dam/teco-cms-ecosystem/flow/guia-de-canales/4646.png" group-title="Nacionales" tvg-id="NetTV.ar",Net TV')
print('https://unlimited1-buenosaires.dps.live/nettv/nettv.smil/playlist.m3u8')
print('#EXTINF:-1 tvg-name="El Trece." tvg-logo="https://entretenimiento.flow.com.ar/content/dam/teco-cms-ecosystem/flow/guia-de-canales/6.png" group-title="Nacionales" tvg-id="ElTrece.ar",El Trece')
print('https://live-01-02-eltrece.vodgc.net/eltrecetv/index.m3u8')
print('#EXTINF:-1 tvg-name="Canal E." tvg-logo="http://iptv-argentina.republicaweb.net/Oficial/Logos/CanalE.png" group-title="Nacionales" tvg-id="CanalE.ar",Canal E')
print('https://unlimited1-buenosaires.dps.live/perfiltv/perfiltv.smil/playlist.m3u8')
print('#EXTINF:-1 tvg-name="Caras TV." tvg-logo="http://www.radiosargentina.com.ar/png/VI-CARAS.png" group-title="Nacionales" tvg-id="NetTV.ar",Caras TV')
print('https://unlimited1-buenosaires.dps.live/carastv/carastv.smil/playlist.m3u8')
print('#EXTINF:-1 tvg-name="CineAr." tvg-logo="https://entretenimiento.flow.com.ar/content/dam/teco-cms-ecosystem/flow/guia-de-canales/1605.png" group-title="Nacionales" tvg-id="CineAr.ar",CineAr')
print('https://538d0bde28ccf.streamlock.net/live-cont.ar/cinear/playlist.m3u8')
print('#EXTINF:-1 tvg-name="Encuentro." tvg-logo="https://entretenimiento.flow.com.ar/content/dam/teco-cms-ecosystem/flow/guia-de-canales/477.png" group-title="Nacionales" tvg-id="Encuentro.ar",Encuentro')
print('https://538d0bde28ccf.streamlock.net/live-cont.ar/encuentro/playlist.m3u8')
print('#EXTINF:-1 tvg-name="Argentinísima Satelital." tvg-logo="https://entretenimiento.flow.com.ar/content/dam/teco-cms-ecosystem/flow/guia-de-canales/57.png" group-title="Nacionales" tvg-id="ArgentinisimaSatelital.ar",Argentinísima Satelital')
print('https://stream1.sersat.com/hls/argentinisima.m3u8')
print('#EXTINF:-1 tvg-name="Aunar TV." tvg-logo="http://tvabierta.weebly.com/uploads/5/1/3/4/51344345/aunar.png" group-title="Nacionales" tvg-id="AunarTV.ar",Aunar TV')
print('https://538d0bde28ccf.streamlock.net/live-cont.ar/mirador/playlist.m3u8')
print('#EXTINF:-1 tvg-name="Canal de la Ciudad." tvg-logo="https://entretenimiento.flow.com.ar/content/dam/teco-cms-ecosystem/flow/guia-de-canales/2332.png" group-title="Nacionales" tvg-id="CanaldelaCiudad.ar",Canal de la Ciudad')
print('http://200.73.141.22/a06/ngrp:gcba_video4-100042_all/Playlist.m3u8')
print('#EXTINF:-1 tvg-name="Canal 10 Mar del Plata." tvg-logo="https://upload.wikimedia.org/wikipedia/commons/6/62/Canal_10_Mar_del_Plata_nuevo_logo.png" group-title="Nacionales",Canal 10 Mar del Plata')
print('http://200.73.141.22/a12/ngrp:canal10mdq-100044_all/Playlist.m3u8')
print('#EXTINF:-1 tvg-name="Canal 10 de Junín." tvg-logo="https://www.canaldiez.com.ar/wp-content/uploads/2022/09/canal-diez_80.png" group-title="Nacionales",Canal 10 de Junín')
print('http://200.73.141.22/a10/ngrp:canal10junin-100056_all/Playlist.m3u8')
print('#EXTINF:-1 tvg-name="El Doce TV Misiones." tvg-logo="https://upload.wikimedia.org/wikipedia/commons/f/f2/Logo_canaldoce_misiones.png" group-title="Nacionales",El Doce TV Misiones')
print('http://200.73.141.22/a13/ngrp:c12_live01-100129_all/Playlist.m3u8')
print('#EXTINF:-1 tvg-name="Canal 9 Televida Mendoza." tvg-logo="https://www.elnueve.com/images/brand-blue.png" group-title="Nacionales" tvg-id="Canal9Televida.ar",Canal 9 Televida Mendoza')
print('https://unlimited1-buenosaires.dps.live/televidaar/televidaar.smil/playlist.m3u8')
print('#EXTINF:-1 tvg-name="Aire de Santa Fe." tvg-logo="https://telefe-static2.akamaized.net/media/143191/logo-cordoba-368x80.png" group-title="Nacionales" tvg-id="TelefeCordoba.ar",Aire de Santa Fe')
print('https://unlimited1-buenosaires.dps.live/airedesantafetv/airedesantafetv.smil/playlist.m3u8')
print('#EXTINF:-1 tvg-name="El 8 Córdoba." tvg-logo="https://telefe-static2.akamaized.net/media/143191/logo-cordoba-368x80.png" group-title="Nacionales" tvg-id="TelefeCordoba.ar",El 8 Córdoba')
print('https://csc-nod-edge01.sensa.com.ar/output/Canal8D/output.mpd')
print('#EXTINF:-1 tvg-name="El 10 Córdoba." tvg-logo="https://upload.wikimedia.org/wikipedia/commons/e/e0/Canal_10_C%C3%B3rdoba_%28Logo_2018%29.png" group-title="Nacionales" tvg-id="Canal10Cordoba.ar",El 10 Córdoba')
print('https://csc-nod-edge01.sensa.com.ar/output/Canal10D/output.mpd')
print('#EXTINF:-1 tvg-name="El 12 Córdoba." tvg-logo="https://upload.wikimedia.org/wikipedia/commons/9/94/El_doce_tv_cba_logo.png" group-title="Nacionales" tvg-id="",El 12 Córdoba')
print('https://csc-nod-edge01.sensa.com.ar/output/Canal12D/output.mpd')
print('#EXTINF:-1 tvg-name="T5 Satelital Corrientes." tvg-logo="https://t5satelital.com/wp-content/uploads/2023/09/T5-Satelital-en-vivo-Online.png" group-title="Nacionales",T5 Satelital Corrientes')
print('https://csc-nod-edge01.sensa.com.ar/output/ARR3/T5SD/output.mpd')
print('#EXTINF:-1 tvg-name="Telefe Internacional." tvg-logo="https://images.pluto.tv/channels/613237a1c9e0db0007a91350/colorLogoPNG.png" group-title="Nacionales" tvg-id="TelefeInternacional.ar",Telefe Internacional')
print('https://cfd-v4-service-channel-stitcher-use1-1.prd.pluto.tv/v1/stitch/embed/hls/channel/613237a1c9e0db0007a91350livestitch/master.m3u8?deviceType=samsung-tvplus&deviceMake=samsung&deviceModel=samsung&deviceVersion=unknown&appVersion=unknown&marketingRegion=VE&deviceLat=0&deviceLon=0&deviceDNT=%7BTARGETOPT%7D&deviceId=%7BPSID%7D&advertisingId=%7BPSID%7D&us_privacy=1YNY&samsung_app_domain=%7BAPP_DOMAIN%7D&samsung_app_name=%7BAPP_NAME%7D&profileLimit=&profileFloor=&embedPartner=samsung-tvplus')
