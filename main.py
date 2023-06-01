# Relogio Inteligente - Módulo Principal
import rp2
import network
import time
import gc

import secrets
import dht

from sys import exit
from machine import Pin, SPI

TIMEOUT = 20

# Inicia o display
from display_ips import DISPLAY_IPS
import fonts.freesans20 as freesans20
import fonts.weather_font as wfont

pdc = Pin(14, Pin.OUT, value=0)
prst = Pin(13, Pin.OUT, value=1)
pcs = Pin(9, Pin.OUT, value=1)
gc.collect()  # Precaution before instantiating framebuf
spi = SPI(1, sck=Pin(10), mosi=Pin(11), baudrate=1_000_000)
disp = DISPLAY_IPS(spi, pcs, pdc, prst, 80, 160)

WHITE = DISPLAY_IPS.rgb(255,255,255)
GRAY = DISPLAY_IPS.rgb(127,127,127)
BLACK = DISPLAY_IPS.rgb(0,0,0)
BLUE = DISPLAY_IPS.rgb(0,0,255)
YELLOW = DISPLAY_IPS.rgb(255, 216, 0)

disp.fill(BLUE)
disp.print(20, 30, "Conectando...", freesans20, WHITE, BLUE)
disp.show()

# Prepara acesso ao sensor
dht_data = Pin(15, Pin.IN, Pin.PULL_UP)
sensor = dht.DHT(dht_data, dht.DHT11, 0)

# Conecta à rede WiFi
rp2.country('BR')
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(secrets.ESSID, secrets.PASSWD)

print ('Conectando...')
timeout = time.ticks_add(time.ticks_ms(), TIMEOUT*1000)
while not wlan.isconnected() and wlan.status() >= 0 and \
      time.ticks_diff(timeout, time.ticks_ms()) > 0:
    time.sleep(0.2)

if not wlan.isconnected(): 
    disp.fill(BLUE)
    disp.print(0, 30, "SEM CONEXAO", freesans20, WHITE, BLUE)
    disp.show()
    print ('Não conseguiu conectar, abortando')
    exit()

print ('Conectado')
print('IP: '+wlan.ifconfig()[0])

# Obter a hora atual
import ntptime
UTC_OFFSET = -3 * 60 * 60
ntptime.settime()

# Iniciacoes para o laco principal
import weather
now = time.time()
clima = None
atlWeather = now
INTERVALO_HORA = 20 # tempo entre atualizacoes da hora
INTERVALO_WEATHER = 5*60 # tempo entre atualizacoes do clima

# Laco Principal
while True:
    # Obtem a hora atual
    now = time.time()
    agora = time.localtime(now + UTC_OFFSET)
    hora =  "{:02}:{:02}".format(agora[3], agora[4])

    # Obtem previsão do tempo
    if now >= atlWeather:
        code,sunrise,sunset = weather.previsao()
        if not code is None:
            print ("Weathercode: {}".format(code))
            clima, frente, fundo = weather.decodeWeather(code,
                        (now > sunrise) and (now < sunset))
        atlWeather = atlWeather + INTERVALO_WEATHER
        
    # Obtem a temperatura
    t = sensor.temperatura()
    temp = "{:.1f} C".format(t)

    # Atualiza a tela
    disp.fill(BLUE)
    disp.print(80, 10, hora, freesans20, WHITE, BLUE)
    disp.print(80, 40, temp, freesans20, GRAY, BLUE)
    if not clima is None:
        disp.print(20, 4, chr(clima), wfont, frente, fundo)
    disp.show()

    # Dá um tempo entre atualizações da hora
    time.sleep (INTERVALO_HORA)
