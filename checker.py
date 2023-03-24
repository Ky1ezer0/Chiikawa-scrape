import json
from pprint import pprint
import configparser
import requests
import telebot
import logging
from telebot import types
from haversine import haversine


class BusStop:
    def __init__(self, id, lat, long, name) -> None:
        self.id = id
        self.lat = float(lat)
        self.long = float(long)
        self.name = name
        self.distance = 0


busStop = []
with open("./busStop.txt", "r") as doc:
    for t in doc.readlines():
        data = t.split(" ", 3)
        stop = BusStop(data[0], data[1], data[2], data[3].replace("\n", ""))
        busStop.append(stop)

telebot.logger.setLevel(logging.INFO)
config = configparser.ConfigParser()
config.read("config.ini")
bot = telebot.TeleBot(config["TELEGRAM"]["ACCESS_TOKEN"], parse_mode=None)


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    itembtn1 = types.KeyboardButton("幫我睇下K68呢個垃圾巴士幾時到", request_location=True)
    markup.add(itembtn1)
    bot.reply_to(message, "喂！有咩可以幫到你", reply_markup=markup)


@bot.message_handler(content_types=["location"])
def bus(message):
    userLong = message.location.longitude
    userLat = message.location.latitude
    closestStop = []
    for b in busStop:
        userBetweenStop = haversine((userLat, userLong), (b.lat, b.long))
        b.distance = userBetweenStop
        closestStop.append(b)
    closestStop.sort(key=lambda elem: elem.distance)

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            closestStop[0].name,
            callback_data=closestStop[0].id,
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            closestStop[1].name,
            callback_data=closestStop[1].id,
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            closestStop[2].name,
            callback_data=closestStop[2].id,
        )
    )

    bot.reply_to(message, "睇下邊個站近你多啲?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def bus_callback(call):
    # Fetch bus data via MTR API
    reqUrl = "https://rt.data.gov.hk/v1/transport/mtr/bus/getSchedule"
    headersList = {"Accept": "application/json", "Content-Type": "application/json"}
    payload = json.dumps({"language": "en", "routeName": "K68"})
    response = requests.request("POST", reqUrl, data=payload, headers=headersList)
    raw = json.loads(response.text)
    raw = raw["busStop"]
    for data in raw:
        if data["busStopId"] == call.data:
            pprint(data)
            departureTimeSecond = data["bus"][0]["departureTimeInSecond"]
            break

    for s in busStop:
        if s.id == call.data:
            currentBusStop = s
            break
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        f"架巴士仲有 {departureTimeSecond} 秒 ({round(int(departureTimeSecond)/60)} min) 先到\n{currentBusStop.name}",
    )


if __name__ == "__main__":
    bot.infinity_polling()
    # reqUrl = "https://rt.data.gov.hk/v1/transport/mtr/bus/getSchedule"

    # headersList = {"Accept": "application/json", "Content-Type": "application/json"}

    # payload = json.dumps({"language": "en", "routeName": "K68"})

    # response = requests.request("POST", reqUrl, data=payload, headers=headersList)
    # raw = json.loads(response.text)
    # raw = raw["busStop"]
    # for data in raw:
    #     if data["busStopId"] == "K68-U020":
    #         pprint(data)
    #         print(
    #             f"架巴士仲有 {data['bus'][0]['departureTimeInSecond']} 秒 ({round(int(data['bus'][0]['departureTimeInSecond'])/60)} min) 先到你簡個個站"
    #         )
