import asyncio

from telegram import Bot, InputMediaPhoto, Update
import atexit
import random
import requests
from bs4 import BeautifulSoup
from telegram.ext import Updater, CommandHandler, ContextTypes, ApplicationBuilder

TOKEN = 'YOUR TOKEN'
chat_id = "YOUR CHAT ID"
channels = ['anigeek', 'microceli', 'guides_tg', 'neuron_girl', 'picrandom']
total_imgs = 10 # 10 is max
channels_imgs = 0 # from publics listed in channels, not more than channels
bot = Bot(TOKEN)
application = ApplicationBuilder().token(TOKEN).build()


def get_random_joke():
    while True:
        number = random.randint(1, 999)
        url = f"https://baneks.ru/{number}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        content = meta_tag['content']
        if len(content) < 1000:
            break
    return content


async def get_imgs_from_safebooru(k, images):
    page = random.randint(1, 3450)
    page = page * 40
    url = f"https://safebooru.org/index.php?page=post&s=list&tags=1girl+1boy&pid={page}"
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    spans = soup.find_all('span', {'id': True})
    spans.pop(0)  # удаляем первый элемент списка
    images_url = random.sample(spans, k)  # айдишники картинок
    for i in range(len(images_url)):
        img_url = images_url[i]
        id = img_url['id']
        id = int(id.lstrip('s'))
        final_url = f"https://safebooru.org/index.php?page=post&s=view&id={id}"
        final_response = requests.get(final_url)
        final_html = final_response.text
        final_soup = BeautifulSoup(final_html, 'html.parser')
        result = final_soup.find('img', {'id': 'image'})['src']
        images.append(InputMediaPhoto(media=result))
    return images


def get_media(names):
    media = []
    links = []
    for channel in names:
        if len(media) >= channels_imgs:
            break
        soup = BeautifulSoup(requests.get(f'https://t.me/s/{channel}?embed=1').text, 'html.parser')
        photo_links = soup.find_all('a', {'class': 'tgme_widget_message_photo_wrap'})
        total = len(photo_links)
        if total < 2:
            continue
        total = -total
        image_id = random.randrange(total, -1)
        links.append(photo_links[image_id])
    links = list(set(links))
    for link in links:
        media.append(InputMediaPhoto(media=link['href']))
    return media


async def send_message(bot, anek, media):
    message = await bot.send_media_group(chat_id=chat_id, media=media, caption=anek, connect_timeout=30)


async def content(update, context):
    user_id = update.effective_user.id
    chat_member = await context.bot.get_chat_member(chat_id, user_id)
    if chat_member.status in ["administrator", "creator"]:
        try:
            await msg_main()
        except:
            print("Запрос выполнен!")
    else:
        job_queue = application.job_queue
        job_queue.run_once(not_admin, 0)


async def start(update, context):
    await context.bot.send_message(chat_id=chat_id, text="Привет! Я жду команду /content от администраторов канала")


async def exit_handler():
    await bot.send_message(chat_id=chat_id, text='Я ухожу спать, не скучайте!')


async def msg_main():
    anek = get_random_joke()
    # choosed_channels = random.choices(channels, k=total_imgs)
    media = get_media(channels)
    left_imgs = 10 - len(media)
    media = await get_imgs_from_safebooru(left_imgs, media)
    await send_message(bot, anek, media)


async def hi(empty):
    await bot.send_message(chat_id=chat_id, text='Я cнова живу!')


async def not_admin(empty):
    await bot.send_message(chat_id=chat_id, text='Я слушаюсь только администраторов чатика!')


def main():
    print("Бот запущен!")
    job_queue = application.job_queue
    job_queue.run_once(hi, 0)
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    content_handler = CommandHandler('content', content)
    application.add_handler(content_handler)
    application.run_polling()


if __name__ == '__main__':
    asyncio.run(main())
