import telebot
import sys
import time

token = "1824656204:AAEUCJcFykiOTXlFJB23Bi7tkR0WMkdIX24"

bot =telebot.TeleBot(token)
tb = telebot.AsyncTeleBot(token)
cur_day = time.strftime('%Y.%m.%d')
picture = '/home/pi/Pictures/Thermal/Clear/VIGIA_IR_0.png'
messg = sys.argv[1:]
print(messg)
counter = 0
time_msg = "My clock says it was "+time.strftime("%H:%M:%S")+" when I woke up"
chat_id = '250793611'
group_chat_id = '-722715519'

def formatMessage(msg):
    sentences = ""
    for item in msg:
      sentences += item+" "
    long_sent = sentences.split("_")
    outMsg = ""
    for _sentence in long_sent:
      outMsg += _sentence+"\n"
    return(outMsg)

@bot.message_handler(commands=['image0'])
def send_img(message):
    send_image(message)
    #bot.send_photo(message.chat.id,photo=open(image,'rb'))
    
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    tmstamp = time.strftime("%H:%M:%S")
    bot.reply_to(message, time_msg+" and now it is "+str(tmstamp))
    
def send_image(img):
    global chat_id
    global messg
    tmstamp = time.strftime("%H:%M:%S")
    bot.send_photo(chat_id, photo=open(img,'rb'), caption=formatMessage(messg))

def send_msg(cur_day):
    bot.send_message(chat_id, "Today, the date is "+cur_day+".\nBye")

# for the asynchronous functionality    
task = tb.get_me()

#print(time_msg)

send_image(picture)

#bot.polling()