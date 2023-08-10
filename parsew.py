from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from random import random
from bs4 import BeautifulSoup
import time
import sqlite3 as sl
import datetime

GOAL_PRICE = 500

def start():
    options = webdriver.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
    options.add_argument('--allow-profiles-outside-user-dir')
    options.add_argument('--enable-profile-shortcut-manager')
    options.add_argument(r'user-data-dir=D:\projects\buyerBot\User') #необходим полный путь
    options.add_argument('--profile-directory=Profile 23')

    options.add_extension("extension_1_18_33_0.crx")
    driver = webdriver.Chrome(options=options)

    url = 'https://steamcommunity.com/market/listings/730/AWP%20%7C%20Redline%20%28Field-Tested%29' #"https://steamcommunity.com/market/listings/730/Souvenir%20MAC-10%20%7C%20Sienna%20Damask%20%28Minimal%20Wear%29"
    driver.get(url)

    # найти и поставить галку для отображения цены и качества наклеек
    time.sleep(6)
    # put_checkbox(driver)
    time.sleep(2)
    #страница для парсинга
    page_source = driver.page_source

    start_parse(driver, page_source)

def start_parse(driver, page_source = 'd'):
    soup = BeautifulSoup(page_source, "html.parser")
    # print(soup)
    skin_name = soup.find("div", {"class": "market_listing_nav"})
    skin_name = skin_name.find_all("a")
    print(skin_name[1].text)
    
    # проходим по каждой строке со скином
    for div in soup.find_all("div", {"class": "market_listing_row"}):
        sum = div.find("span", {"class": "value-price"})
        if sum is not None:
            sum_price = float(sum.get_text().replace('₽','')) #$ ₽
            print(sum_price)

            if sum_price < GOAL_PRICE:
                continue
            else:
                #покупаем скин и добавляем в базу данных
                temp = push_sticks(driver, div, sum_price, skin_name[1].text)
                if temp:
                    print('Куплен 1 скин')
                    return 1


def put_checkbox(driver):
    try:
        xPath = "//label[@for='auto_get_float_and_sticker_wear']"
        time.sleep(6)
        span_checkbox = driver.find_element('xpath', xPath)
        span_checkbox.click()
    except NoSuchElementException:
        print("элемент checkbox не найден")

def push_sticks(driver, div, sum_price, skin_name):
    #в sticks ищем div без класса, чтобы не дублировались наклейки
    stickss = div.find("div", {"class": False})
    sticks = stickss.find_all("div", {"class": "tooltip__row"}) #.find_all("div", {"class": "sih-images"})
    name_tuple = ()
    wear_tuple = ()
    stick_count = 0 # если количество наклеек будет меньше 4, то для базы данных добавим пустые

    buy = True #флаг для покупки
    for stick in sticks:
        stick_count = stick_count + 1 

        name = stick.find("div", class_="tooltip__name").text
        name_tuple = name_tuple + (name,)
        # price = stick.find("span", class_="tooltip__price").text
        wear = stick.find("span", class_="tooltip__percent").text
        wear_float = float(wear.replace('%',''))
        wear_tuple = wear_tuple + (float(wear.replace('%','')),)
        if wear_float > 0:
            buy = False

    if stick_count < 4:
        while stick_count != 4:
            name_tuple = name_tuple + ('-',)
            wear_tuple = wear_tuple + ('NULL',)
            stick_count = stick_count + 1

    if buy:
        print("Все стикеры целые, купить скин")
        try:
            time.sleep(random() * (1.4 - 0.1) + 0.1)
            buy_span = driver.find_element('xpath', f'//div[@id="{div["id"]}"]//span[contains(text(), "Купить")]')
            buy_span.click()
            time.sleep(random() * (1.4 - 0.1) + 0.1)
            buy_conditions = driver.find_element('xpath', '//input[@id="market_buynow_dialog_accept_ssa"]')
            buy_conditions.click()
            time.sleep(random() * (1.4 - 0.1) + 0.1)
            buy_real = driver.find_element('xpath', '//a[@id="market_buynow_dialog_purchase"]')
            buy_real.click()
        except NoSuchElementException:
            print("buy элемент не найден, скин не купился")
    else:
        print("Есть тёртые стикеры, скипаем скин")

    data = (skin_name,) + (sum_price,) + (datetime.datetime.now(),) + name_tuple + wear_tuple
    # print(data)
    
    con = sl.connect('skins.db')
    sql = 'INSERT INTO history (skin_name, stick_price, date, stick1,stick2,stick3,stick4,wear1,wear2,wear3,wear4) values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    with con:
        con.execute(sql, data)
    return buy



start()
#start_parse()

#создание базы данных
def create_db():
    # открываем файл с базой данных
    con = sl.connect('skins.db')

    with con:
        con.execute("""
            CREATE TABLE history (
            skin_name VARCHAR(50),
            stick_price float,
            date TEXT,
            stick1 VARCHAR(100),
            stick2 VARCHAR(100),
            stick3 VARCHAR(100),
            stick4 VARCHAR(100),
            wear1 REAL,
            wear2 REAL,
            wear3 REAL,
            wear4 REAL
    );
        """)