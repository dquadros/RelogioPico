# Módulo para consulta do Clima em https://open-meteo.com/
import network
import urequests
import json
import time

url = 'https://api.open-meteo.com/v1/forecast?latitude=-23.53&longitude=-46.79&daily=weathercode,sunrise,sunset&timezone=America%2FSao_Paulo'

# converte hora de formato ISO para interno
def _conv_time(iso):
    return time.mktime((int(iso[0:4]), int(iso[5:7]), int(iso[8:10]),
                        int(iso[11:13]), int(iso[14:16]), 
                        0, 0, 0))

# obtem a previsão de tempo para hoje
def previsao():
    r = urequests.get(url)
    if r.status_code == 200:
        resposta = json.loads(r.text)
        r.close()
        sunrise = _conv_time(resposta['daily']['sunrise'][0])
        sunset = _conv_time(resposta['daily']['sunset'][0])
        return resposta['daily']['weathercode'][0], sunrise, sunset
    else:
        r.close()
        print ('ERRO: {0}'.format(r.status_code));
        return None, 0, 0

from display_ips import DISPLAY_IPS
WHITE = DISPLAY_IPS.rgb(255,255,255)
GRAY = DISPLAY_IPS.rgb(127,127,127)
BLACK = DISPLAY_IPS.rgb(0,0,0)
BLUE = DISPLAY_IPS.rgb(0,0,255)
YELLOW = DISPLAY_IPS.rgb(255, 216, 0)

# conversão do código do tempo em caracter e cores
tabWeather = {
    0: [ (0x0d, YELLOW), (0x2e, WHITE) ], # clear sky
    1: [ (0x0d, YELLOW), (0x2e, WHITE) ], # mainly clear
    2: [ (0x02, YELLOW), (0x86, WHITE) ], # partly cloudy
    3: [ (0x13, WHITE), (0x13, WHITE) ], # overcast
    45: [ (0x14, WHITE), (0x14, WHITE) ], # fog
    48: [ (0x14, WHITE), (0x14, WHITE) ], # depositing rime fog
    51: [ (0x17, WHITE), (0x17, WHITE) ], # light drizzle
    53: [ (0x17, WHITE), (0x17, WHITE) ], # moderate drizzle
    55: [ (0x17, WHITE), (0x17, WHITE) ], # dense drizzle
    56: [ (0x17, WHITE), (0x17, WHITE) ], # light freezing drizzle
    57: [ (0x17, WHITE), (0x17, WHITE) ], # dense freezing drizzle
    61: [ (0x19, WHITE), (0x19, WHITE) ], # slight rain
    63: [ (0x19, WHITE), (0x19, WHITE) ], # moderate rain
    65: [ (0x19, WHITE), (0x19, WHITE) ], # heavy rain
    66: [ (0x19, WHITE), (0x19, WHITE) ], # light freezing rain
    67: [ (0x19, WHITE), (0x19, WHITE) ], # heavy freezing rain
    71: [ (0x1b, WHITE), (0x1b, WHITE) ], # slight snow
    73: [ (0x1b, WHITE), (0x1b, WHITE) ], # moderate snow fall
    75: [ (0x1b, WHITE), (0x1b, WHITE) ], # heavy snow fall
    77: [ (0x1b, WHITE), (0x1b, WHITE) ], # snow grains
    80: [ (0x19, WHITE), (0x19, WHITE) ], # slight rain shower
    81: [ (0x19, WHITE), (0x19, WHITE) ], # moderate rain shower
    82: [ (0x19, WHITE), (0x19, WHITE) ], # violent rain shower
    85: [ (0x1b, WHITE), (0x1b, WHITE) ], # slight snow shower
    86: [ (0x1b, WHITE), (0x1b, WHITE) ], # heavy snow shower
    95: [ (0x1e, GRAY), (0x1e, GRAY) ], # thunderstorm
    96: [ (0x1e, GRAY), (0x1e, GRAY) ], # thunderstorm with slight hail
    99: [ (0x1e, GRAY), (0x1e, GRAY) ] # thunderstorm with heavy hail
}

def decodeWeather(code, ehDia):
    if code in tabWeather:
        fundo = BLUE if ehDia else BLACK
        return tabWeather[code][ehDia][0], tabWeather[code][ehDia][1], fundo
    else:
        return None, 0, 0
    
