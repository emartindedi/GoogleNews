"""Técnicas de Recogida de Datos - Universidad de Navarra - 2022-2023 - Elena Martín de Diego"""
# Importing all needed libraries
import time
import datetime
import os
import time
import requests
from pprint import pprint
#from bs4 import BeautifulSoup
import pandas as pd

import json
from lxml import html
import re
import csv
import numpy as np

import sys
import traceback

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
    )
from textblob import TextBlob
#import re

class GoogleNews:

    url: str = "https://news.google.com/"
    opened: bool
    topics: list = []
    topics_urls: list = []
    data: dict = {}
    inicio: None
    fin: None

    def define_options_scraper(self):
        """Configurating the web page appearance"""
        options = Options()
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/5\ 37.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument('--window-size=920,1480')
        options.add_argument('--headless')  # Headless mode

    def open_google_news(self, driver):
        """Open the web page contained in the url attribute of the class
        :param: driver selenium object
        :return: boolean object if it was opened the web page correctly and accepted the consent"""
        r = requests.get(self.url + "home?hl=es&gl=ES&ceid=ES:es.hlml")
        if r.status_code == 200:
            # If status is equal to 200 it means that the web can be opened correctly
            driver.get(self.url)
            time.sleep(7)
            # Accept the consent button
            consent = driver.find_element(by=By.CSS_SELECTOR,
                                          value='button.VfPpkd-LgbsSe.VfPpkd-LgbsSe-OWXEXe-k8QpJ.VfPpkd-LgbsSe-OWXEXe-dgl2Hf.nCP5yc.AjY5Oe.DuMIQc.LQeN7.Nc7WLe')
            consent.click()
            self.opened = True
        else:
            self.opened = False

    def get_topics(self, driver):
        """Function to obtain the possible topics
        :param: driver: selenium driver object with the google news google chrome tab
        :return: tuple (possible topics in google news, urls of the topics)"""
        lista = driver.find_elements(by=By.CLASS_NAME, value='brSCsc')  # All elements to choose
        self.topics = [element.get_attribute("textContent") for element in lista if
                  element.get_attribute('href') != None]  # list withour Para ti y Siguiendo because it need to log in
        self.topics_urls = [element.get_attribute('href') for element in lista if element.get_attribute('href') != None]
        return (self.topics, self.topics_urls)

    def analize_sentiment(self, text):
        """Utility function to classify the polarity of a string
        using textblob
        :param: text: string to analize
        :return: {-1,0,1} are the possible answers"""
        analysis = TextBlob(text.strip()) # Function of the library textblob that given the wordls seaparately (.strip), it retiurns -1, 0 or 1
        if analysis.sentiment.polarity > 0:
            return 1
        elif analysis.sentiment.polarity == 0:
            return 0
        else:
            return -1

    def generate_dataframe(self, driver, topics, topics_urls):
        """Core funcion of the class. It generates and saves it locally a dataframe with the information extracted from the
        google news web page
        :param driver: selenium object
        :param topics: list with the possoble topics
        :param topics_url: list with the urls to access each topic
        :return: dictionary with the information extracted"""
        dictionary = {'Fecha': [], 'Ultima actualizacion': [], 'Topic': [], 'Fuente': [], 'Resumen noticia': [],
                      'Link': [], 'Analisis sentimental': []} # Dictionary to save all information that will be extracted
        # La fecha se encuentra el la pagina de inicio, por tanto se extrae antes de pinchar en la seccion selecionada
        date = driver.find_element(by=By.CLASS_NAME, value='Hp1DDd.oBu3Fe')
        fecha = date.get_attribute("textContent")
        current_time = ' de ' + str(datetime.datetime.today().year)
        # Recorremos todos los posibles temas
        for num in range(len(topics)):
            # Access the topic by his url previously obtained
            driver.get(topics_urls[num])
            time.sleep(3)
            url = driver.current_url
            if topics[num] == 'Inicio':
                # Go to Noticas Destacadas
                noticias_destacadas = driver.find_element(by=By.CLASS_NAME, value='aqvwYd')
                driver.get(noticias_destacadas.get_attribute('href'))  # Go to the link
                # Get the news
                texto = driver.find_elements(by=By.CLASS_NAME, value='gPFEn') + driver.find_elements(by=By.CLASS_NAME,
                                                                                                     value='JtKRv')
                fuente = driver.find_elements(by=By.CLASS_NAME, value='vr1PYe')
                destacados_more = zip(texto, driver.find_elements(by=By.CLASS_NAME, value='WwrzSb'))
                time_ago = driver.find_elements(by=By.CLASS_NAME, value='hvbAAd')
                i = 0
                for (noticia, link) in destacados_more:
                    dictionary['Fecha'].append(fecha + current_time)
                    dictionary['Ultima actualizacion'].append(time_ago[i].get_attribute("textContent"))
                    dictionary['Topic'].append(topics[num])
                    dictionary['Fuente'].append(fuente[i].get_attribute("textContent"))
                    dictionary['Resumen noticia'].append(str(noticia.get_attribute("textContent")))
                    dictionary['Link'].append(link.get_attribute('href'))
                    i += 1
            if topics[num] == 'News Showcase':
                noticias = driver.find_elements(by=By.CLASS_NAME, value='sLwsDb')
                topic_especifico = driver.find_elements(by=By.CLASS_NAME, value='JrYg1b.vP0hTc')
                resumen = driver.find_elements(by=By.CLASS_NAME, value='kEAYTc.r5Cqre')
                links = driver.find_elements(by=By.CLASS_NAME, value='WwrzSb')
                fuente = driver.find_elements(by=By.CLASS_NAME, value='UiDffd.IGhidc')  # probar MyQDIb
                time_ago = driver.find_elements(by=By.CLASS_NAME, value='xsHp8')
                i = 0
                j = 0
                for noticia in noticias:
                    dictionary['Fecha'].append(fecha + current_time)
                    dictionary['Ultima actualizacion'].append(time_ago[j].get_attribute("textContent"))
                    dictionary['Topic'].append(
                        str(topics[num]) + ' --- ' + str(topic_especifico[i].get_attribute("textContent")))
                    dictionary['Fuente'].append(fuente[j].get_attribute("alt"))
                    dictionary['Resumen noticia'].append(resumen[i].get_attribute("textContent"))
                    dictionary['Link'].append(links[i].get_attribute('href'))
                    i += 1
                    if i % 3 == 0:
                        j = j + 1
            if topics[num] == 'España':
                # Get the news
                noticias = driver.find_elements(by=By.CLASS_NAME, value='WwrzSb')
                fuente = driver.find_elements(by=By.CLASS_NAME, value='vr1PYe')
                time_ago = driver.find_elements(by=By.CLASS_NAME, value='hvbAAd')
                i = 0
                for noticia in noticias:
                    dictionary['Fecha'].append(fecha + current_time)
                    dictionary['Ultima actualizacion'].append(time_ago[i].get_attribute("textContent"))
                    dictionary['Topic'].append(topics[num])
                    dictionary['Fuente'].append(fuente[i].get_attribute("textContent"))
                    dictionary['Resumen noticia'].append(str(noticia.get_attribute("aria-label")))
                    dictionary['Link'].append(noticia.get_attribute('href'))
                    i += 1
            if topics[num] == 'Internacional':
                # Get the news
                noticias = driver.find_elements(by=By.CLASS_NAME, value='WwrzSb')
                fuente = driver.find_elements(by=By.CLASS_NAME, value='vr1PYe')
                time_ago = driver.find_elements(by=By.CLASS_NAME, value='hvbAAd')
                i = 0
                for noticia in noticias:
                    dictionary['Fecha'].append(fecha + current_time)
                    dictionary['Ultima actualizacion'].append(time_ago[i].get_attribute("textContent"))
                    dictionary['Topic'].append(topics[num])
                    dictionary['Fuente'].append(fuente[i].get_attribute("textContent"))
                    dictionary['Resumen noticia'].append(str(noticia.get_attribute("aria-label")))
                    dictionary['Link'].append(noticia.get_attribute('href'))
                    i += 1
            if topics[num] == 'Local':
                # Get the news
                noticias = driver.find_elements(by=By.CLASS_NAME, value='WwrzSb')
                fuente = driver.find_elements(by=By.CLASS_NAME, value='vr1PYe')
                time_ago = driver.find_elements(by=By.CLASS_NAME, value='hvbAAd')
                i = 0
                for noticia in noticias:
                    dictionary['Fecha'].append(fecha + current_time)
                    dictionary['Ultima actualizacion'].append(time_ago[i].get_attribute("textContent"))
                    dictionary['Topic'].append(topics[num])
                    dictionary['Fuente'].append(fuente[i].get_attribute("textContent"))
                    dictionary['Resumen noticia'].append(str(noticia.get_attribute("aria-label")))
                    dictionary['Link'].append(noticia.get_attribute('href'))
                    i += 1
            if topics[num] == 'Economía':
                # Get the news
                noticias = driver.find_elements(by=By.CLASS_NAME, value='WwrzSb')
                fuente = driver.find_elements(by=By.CLASS_NAME, value='vr1PYe')
                time_ago = driver.find_elements(by=By.CLASS_NAME, value='hvbAAd')
                i = 0
                for noticia in noticias:
                    dictionary['Fecha'].append(fecha + current_time)
                    dictionary['Ultima actualizacion'].append(time_ago[i].get_attribute("textContent"))
                    dictionary['Topic'].append(topics[num])
                    dictionary['Fuente'].append(fuente[i].get_attribute("textContent"))
                    dictionary['Resumen noticia'].append(str(noticia.get_attribute("aria-label")))
                    dictionary['Link'].append(noticia.get_attribute('href'))
                    i += 1
            if topics[num] == 'Ciencia y tecnología':
                # Get the news
                noticias = driver.find_elements(by=By.CLASS_NAME, value='WwrzSb')
                fuente = driver.find_elements(by=By.CLASS_NAME, value='vr1PYe')
                time_ago = driver.find_elements(by=By.CLASS_NAME, value='hvbAAd')
                i = 0
                for noticia in noticias:
                    dictionary['Fecha'].append(fecha + current_time)
                    dictionary['Ultima actualizacion'].append(time_ago[i].get_attribute("textContent"))
                    dictionary['Topic'].append(topics[num])
                    dictionary['Fuente'].append(fuente[i].get_attribute("textContent"))
                    dictionary['Resumen noticia'].append(str(noticia.get_attribute("aria-label")))
                    dictionary['Link'].append(noticia.get_attribute('href'))
                    i += 1
            if topics[num] == 'Entretenimiento':
                # Get the news
                noticias = driver.find_elements(by=By.CLASS_NAME, value='WwrzSb')
                fuente = driver.find_elements(by=By.CLASS_NAME, value='vr1PYe')
                time_ago = driver.find_elements(by=By.CLASS_NAME, value='hvbAAd')
                i = 0
                for noticia in noticias:
                    dictionary['Fecha'].append(fecha + current_time)
                    dictionary['Ultima actualizacion'].append(time_ago[i].get_attribute("textContent"))
                    dictionary['Topic'].append(topics[num])
                    dictionary['Fuente'].append(fuente[i].get_attribute("textContent"))
                    dictionary['Resumen noticia'].append(str(noticia.get_attribute("aria-label")))
                    dictionary['Link'].append(noticia.get_attribute('href'))
                    i += 1
            if topics[num] == 'Deportes':
                # Get the news
                noticias = driver.find_elements(by=By.CLASS_NAME, value='WwrzSb')
                fuente = driver.find_elements(by=By.CLASS_NAME, value='vr1PYe')
                time_ago = driver.find_elements(by=By.CLASS_NAME, value='hvbAAd')
                i = 0
                for noticia in noticias:
                    dictionary['Fecha'].append(fecha + current_time)
                    dictionary['Ultima actualizacion'].append(time_ago[i].get_attribute("textContent"))
                    dictionary['Topic'].append(topics[num])
                    dictionary['Fuente'].append(fuente[i].get_attribute("textContent"))
                    dictionary['Resumen noticia'].append(str(noticia.get_attribute("aria-label")))
                    dictionary['Link'].append(noticia.get_attribute('href'))
                    i += 1
            if topics[num] == 'Salud':
                # Get the news
                noticias = driver.find_elements(by=By.CLASS_NAME, value='WwrzSb')
                fuente = driver.find_elements(by=By.CLASS_NAME, value='vr1PYe')
                time_ago = driver.find_elements(by=By.CLASS_NAME, value='hvbAAd')
                i = 0
                for noticia in noticias:
                    dictionary['Fecha'].append(fecha + current_time)
                    dictionary['Ultima actualizacion'].append(time_ago[i].get_attribute("textContent"))
                    dictionary['Topic'].append(topics[num])
                    dictionary['Fuente'].append(fuente[i].get_attribute("textContent"))
                    dictionary['Resumen noticia'].append(str(noticia.get_attribute("aria-label")))
                    dictionary['Link'].append(noticia.get_attribute('href'))
                    i += 1

        dictionary['Analisis sentimental'] = list(np.array([self.analize_sentiment(text) for text in dictionary['Resumen noticia']]))
        driver.quit()
        return dictionary

    def summary(self, df):
        """Print a summary of the columns choosen
        :param: df: pandas dataframe with the information"""
        stop = 'True'
        flag = True
        while flag:
            try:
                print("The possibilities are:", df.columns)
                user_selection = str(input("Choose the option to extract detail information about it:"))
                if user_selection in df.columns:
                    if user_selection == 'Fecha':
                        print(df["Fecha"].value_counts(normalize=True))
                    if user_selection == 'Ultima actualizacion':
                        print(df["Ultima actualizacion"].value_counts(normalize=True))
                    if user_selection == 'Topic':
                        print(df["Topic"].value_counts(normalize=True))
                    if user_selection == 'Fuente':
                        print(df["Fuente"].value_counts(normalize=True))
                    if user_selection == 'Resumen noticia':
                        print(df["Resumen noticia"].value_counts(normalize=True))
                    if user_selection == 'Link':
                        print(df["Link"].value_counts(normalize=True))
                    if user_selection == 'Analisis sentimental':
                        print(df["Analisis sentimental"].value_counts(normalize=True))
                        ## We print percentages of the sentimental analysis (last column in the dataset generated):
                        print("Percentage of positive news: {}%".format(
                            len([text for index, text in enumerate(df['Resumen noticia']) if
                                 df['Analisis sentimental'][index] > 0]) * 100 / len(df['Resumen noticia'])))
                        print("Percentage of neutral news: {}%".format(
                            len([text for index, text in enumerate(df['Resumen noticia']) if
                                 df['Analisis sentimental'][index] == 0]) * 100 / len(df['Resumen noticia'])))
                        print("Percentage of negative news: {}%".format(
                            len([text for index, text in enumerate(df['Resumen noticia']) if
                                 df['Analisis sentimental'][index] < 0]) * 100 / len(df['Resumen noticia'])))
                    try:
                        stop = str(input("Do you want more information? [True/False]"))
                        if stop in ['True', 'False']:
                            if stop == 'False':
                                flag = False
                                break
                        else:
                            continue
                    except ValueError:
                        print('Invalid')
                        continue
                else:
                    print("The topic is not available or it not correct")
            except ValueError:
                print('Invalid')
                continue


    def extract_google_news(self):
        """Function that manages the rest of the functios of the class"""
        self.define_options_scraper()
        driver = webdriver.Chrome(ChromeDriverManager().install())
        self.open_google_news(driver)
        if self.opened != True:
            print("Not possible to open the web page of google news")
        else:
            print('Inicio: ', time.ctime())
            self.inicio = str(time.ctime()) # Cuando se ejecuta
            topics, topics_urls = self.get_topics(driver)
            self.data = self.generate_dataframe(driver, topics, topics_urls)
            df = pd.DataFrame(self.data)
            df.to_csv('Google_news.csv', index=False) # Save it locally
            print('Fin: ', time.ctime())
            self.summary(df)
            print('Fin: ', time.ctime())
            self.fin = str(time.ctime()) # Cuando termina
