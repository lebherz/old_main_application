﻿#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pi3d
import sys
import os
import time
import datetime
import threading
import numpy as np
import logging
from pkg_resources import resource_filename

from .. import config
from ..core import  peripherals
from ..core import graphics

try:
    import pyowm
except ImportError:
    sys.exit("Please run: (sudo) pip3 install pyowm")

try:
    unichr
except NameError:
    unichr = chr

threehours = time.time()

grapharea = pi3d.Sprite(camera=graphics.CAMERA, w=780,
                        h=100, z=3.0, x=0, y=-180)
grapharea.set_shader(graphics.MATSH)
grapharea.set_material((1.0, 1.0, 1.0))
grapharea.set_alpha(0.3)
grapharea2 = pi3d.Sprite(camera=graphics.CAMERA,
                         w=780, h=350, z=3.0, x=0, y=55)

grapharea2.set_shader(graphics.MATSH)
grapharea2.set_material((0, 0, 0))
grapharea2.set_alpha(0.7)
text = pi3d.PointText(graphics.pointFont, graphics.CAMERA,
                      max_chars=850, point_size=128)

error = False

def init():
    global snowline, rainline, seplines, degwind, weathericon, text, line, windneedle, acttemp, text, error
    #global baroneedle, linemin, linemax

    owm = pyowm.OWM(API_key=config.OWMKEY, language=config.OWMLANGUAGE)
    place = owm.weather_at_place(config.OWMCITY)
    weather = place.get_weather()

    text.text_blocks = []
    text._first_free_char = 0

    if config.OWMLANGUAGE == 'de': #TODO this needs untangling from stuff in config
        weekdays = ['Montag', 'Dienstag', 'Mittwoch',
                    'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    else:
        weekdays = ['monday', 'tuesday', 'wednesday',
                    'thursday', 'friday', 'saturday', 'sunday']

    file_path = resource_filename("shpi", "sprites/{}.png".format(
                                    weather.get_weather_icon_name()))
    if os.path.exists(file_path):
        weathericon = pi3d.ImageSprite(file_path, shader=graphics.SHADER, camera=graphics.CAMERA,
                                        w=150, h=150, z=2, x=-220)

    #else:
    #    import urllib.request
    #    urllib.request.urlretrieve("http://openweathermap.org/img/wn/" + weather.get_weather_icon_name(
    #    ) + "@2x.png", "sprites/" + weather.get_weather_icon_name() + ".png")
    city = pi3d.TextBlock(-390, 180, 0.1, 0.0, 150, text_format=place.get_location(
    ).get_name(), size=0.7, spacing="F", space=0.05, colour=(1.0, 1.0, 1.0, 1.0))
    text.add_text_block(city)

    city = pi3d.TextBlock(-220, 80, 0.1, 0.0, 30, justify=0.5, text_format=weather.get_detailed_status(),
                            size=0.3, spacing="F", space=0.05, colour=(1.0, 1.0, 1.0, 1.0))
    text.add_text_block(city)

    acttemp = pi3d.TextBlock(-350, -50, 0.1, 0.0, 10, text_format=str(weather.get_temperature(
        unit='celsius')['temp']) + u'°C',  size=0.9, spacing="F", space=0.05, colour=(1.0, 1.0, 1.0, 1.0))
    text.add_text_block(acttemp)

    sunriset = weather.get_sunrise_time(
        timeformat='date') + datetime.timedelta(hours=2)
    sunsett = weather.get_sunset_time(
        timeformat='date') + datetime.timedelta(hours=2)
    sunset = pi3d.TextBlock(50, 100, 0.1, 0.0, 20, text_format=unichr(0xE041) + " %s:%02d" % (sunriset.hour, sunriset.minute) + ' ' + unichr(0xE042) + " %s:%02d" % (sunsett.hour, sunsett.minute),  size=0.3, spacing="F",
                            space=0.05, colour=(1.0, 1.0, 1.0, 1.0))
    text.add_text_block(sunset)

    barometer = pi3d.TextBlock(50, -50, 0.1, 0.0, 10, text_format=unichr(0xE00B) + ' ' + str(
        weather.get_pressure()['press']) + ' hPa', size=0.3, spacing="F", space=0.05, colour=(1.0, 1.0, 1.0, 1.0))
    text.add_text_block(barometer)
    #baroneedle = pi3d.Triangle(camera=graphics.CAMERA, corners=(
    #    (-2, 0, 0), (0, 7, 0), (2, 0, 0)), x=barometer.x+16, y=barometer.y - 6, z=0.1)
    #baroneedle.set_shader(graphics.MATSH)
    normalizedpressure = (weather.get_pressure()['press'] - 950)
    if normalizedpressure < 0:
        normalizedpressure = 0
    if normalizedpressure > 100:
        normalizedpressure = 100
    green = 0.02 * (normalizedpressure)
    if green > 1:
        green = 1
    red = 0.02 * (100 - normalizedpressure)
    if red > 1:
        red = 1
    barometer.colouring.set_colour([red, green, 0, 1.0])
    #baroneedle.set_material([red, green, 0])
    #baroneedle.rotateToZ(100 - (normalizedpressure*2))

    humidity = pi3d.TextBlock(50, 0, 0.1, 0.0, 10, text_format=unichr(0xE003) + ' ' + str(
        weather.get_humidity()) + '%', size=0.3, spacing="F", space=0.05, colour=(1.0, 1.0, 1.0, 1.0))
    text.add_text_block(humidity)

    if 'speed' in weather.get_wind():
        wind = pi3d.TextBlock(50, 50, 0.1, 0.0, 10, text_format=unichr(0xE040) + ' ' + str(
            weather.get_wind()['speed']) + 'm/s', size=0.3, spacing="F", space=0.05, colour=(1.0, 1.0, 1.0, 1.0))
        text.add_text_block(wind)

    if 'deg' in weather.get_wind():
        degwind = True
        windneedle = pi3d.Triangle(camera=graphics.CAMERA, corners=(
            (-3, 0, 0), (0, 15, 0), (3, 0, 0)), x=wind.x+180, y=wind.y, z=0.1)
        windneedle.set_shader(graphics.MATSH)
        windneedle.set_material([1, 1, 1])
        windneedle.rotateToZ(weather.get_wind()['deg'])
    else:
        degwind = False

    fc = owm.three_hours_forecast(config.OWMCITY)
    f = fc.get_forecast()

    step = 780 / (len(f))
    actualy = -400 + step
    temp_max = []
    temp_min = []
    temp = []
    seplinesarr = []
    icons = []
    rainarr = []
    snowarr = []
    maxdaytemp = -100
    mindaytemp = 100
    
    for weather in f:
        file_path = resource_filename("shpi", "sprites/{}.png".format(
                                    weather.get_weather_icon_name()))
        if not os.path.exists(file_path):
            import urllib.request #TODO py2 py3 fix
            urllib.request.urlretrieve("http://openweathermap.org/img/wn/" + weather.get_weather_icon_name(
            ) + "@2x.png", file_path)

        icons.append(pi3d.ImageSprite(file_path, shader=graphics.SHADER,
                        camera=graphics.CAMERA, w=20, h=20, z=1, x=actualy, y=-220))

        if weather.get_reference_time('iso')[11:16] == '00:00':
            seplinesarr.append([actualy, -50, 2])
            seplinesarr.append([actualy, 50, 2])
            seplinesarr.append([actualy, -50, 2])
                            
        # if weather.get_reference_time('iso')[11:16] == '12:00':
            day = weather.get_reference_time(timeformat='date').weekday()
            if actualy < 300:
                city = pi3d.TextBlock(
                    actualy+65, -100, 0.1, 0.0, 30, text_format=weekdays[day], justify=0.5,  size=0.23, spacing="F", space=0.05, colour=(1.0, 1.0, 1.0, 1.0))
                text.add_text_block(city)
            if actualy > -300:
                city = pi3d.TextBlock(actualy-6*step, -150, 0.1, 0.0, 30, text_format=str(round(
                    maxdaytemp, 1)) + u'°C', size=0.25, spacing="F", space=0.05, colour=(1.0, 0.0, 0.0, 1.0))
                text.add_text_block(city)
                city = pi3d.TextBlock(actualy-6*step, -210, 0.1, 0.0, 30, text_format=str(round(
                    mindaytemp, 1)) + u'°C', size=0.25, spacing="F", space=0.05, colour=(0.0, 0.0, 1.0, 1.0))
                text.add_text_block(city)

            maxdaytemp = -100
            mindaytemp = 100

        if '3h' in weather.get_snow():
            snowarr.append([actualy, (-50+weather.get_snow()['3h']*30),2])
        else:
            snowarr.append([actualy, -50 ,2])


        if '3h' in weather.get_rain():
            rainarr.append([actualy, (-50+weather.get_rain()['3h']*30),2])
        else:
            rainarr.append([actualy, -50 ,2])

        temperatures = weather.get_temperature(unit='celsius')
        if temperatures['temp_max'] > maxdaytemp:
            maxdaytemp = temperatures['temp_max']
        if temperatures['temp_min'] < mindaytemp:
            mindaytemp = temperatures['temp_min']

        temp_max.append([actualy, temperatures['temp_max']*3, 2])
        temp_min.append([actualy, temperatures['temp_min']*3, 2])
        temp.append([actualy, temperatures['temp']*3, 2])
        actualy += step

    snowline = pi3d.Lines(vertices=snowarr, line_width=3, y=-180, strip=True)
    snowline.set_shader(graphics.MATSH)
    snowline.set_material((0.5, 0.5, 1))
    snowline.set_alpha(0.7)

    rainline = pi3d.Lines(vertices=rainarr, line_width=3, y=-180, strip=True)
    rainline.set_shader(graphics.MATSH)
    rainline.set_material((0, 0, 1))
    rainline.set_alpha(0.7)

    seplines  = pi3d.Lines(vertices=seplinesarr, line_width=1, y=-180, strip=True)
    seplines.set_shader(graphics.MATSH)
    seplines.set_material((0, 0, 0))
    seplines.set_alpha(0.9)

    line = pi3d.Lines(vertices=temp, line_width=2, y=-220, strip=True)
    line.set_shader(graphics.MATSH)
    line.set_material((0, 0, 0))
    line.set_alpha(0.9)

    #linemin = pi3d.Lines(vertices=temp_min, line_width=1,y=-220, strip=True)
    # linemin.set_shader(graphics.MATSH)
    # linemin.set_material((0,0,1))
    # linemin.set_alpha(0.9)

    #linemax = pi3d.Lines(vertices=temp_max, line_width=1,y=-220, strip=True)
    # linemax.set_shader(graphics.MATSH)
    # linemax.set_material((1,0,0))
    # linemax.set_alpha(0.9)

    #except:

    #    error = pi3d.TextBlock(-390, 180, 0.1, 0.0, 150, text_format="OWM ERROR",
    #                           size=0.7, spacing="F", space=0.05, colour=(1.0, 1.0, 1.0, 1.0))
    #    text.add_text_block(error)
    #    error = True

init()
threehours = time.time() + (60*60*1)

def inloop(textchange=False, activity=False, offset=0):
    global snowline, rainline, seplines, degwind, threehours, weathericon, text, line, windneedle, error
    #global baroneedle, linemin, linemax
    if (time.time() > threehours):
        logging.info('new weather forecast')
        #start_new_thread(init, ())
        t = threading.Thread(target=init)
        t.start()
        threehours = time.time() + (60*60*1)

    grapharea2.draw()
    grapharea.draw()

    if offset != 0:
        #graphics.slider_change(city.sprite, offset)
        offset = graphics.slider_change(text.text, offset)
    else:
        if not error:
            try:
                weathericon.draw()
                #baroneedle.draw()
                line.draw()
                # linemin.draw()
                # linemax.draw()
                if degwind:
                    windneedle.draw()
                seplines.draw()
                snowline.draw()
                rainline.draw()
            except Exception as e:
                logging.error('error: {}'.format(e))
                #for icon in icons: icon.draw()

    text.draw()

    return activity, offset
