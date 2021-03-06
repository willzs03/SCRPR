import discord
from discord.ext import tasks
from discord.ext import commands
import os
import requests
import json
import pprint 
from replit import db
from keep_alive import keep_alive
from requests import Request, Session

# interval at which the bot retrieves info in MINUTES. Setting default to 60 minutes.
db["interval"] = 60

def coinExists(sym):
  """Returns True if coin exists from coin market cap"""
  url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
  print(sym)
  params = {
    "symbol": sym
  }
  headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': '48ca8a26-d287-45bf-9ca2-b35926510638',
  }
  
  session = Session()
  session.headers.update(headers)
  try:
    response = session.get(url, params=params)
    data = json.loads(response.text)
    if (data['status']['error_code'] == 400):
      return False
    return True
  except e:
    print(e)
    return False

def getCryptoData():
  """Fetches and returns crypto average prices for all currently tracked cryptos
      currently tracked cryptos are stored in db["cryptoCollection"]
      their most recent prices and volume change is in db["cryptoInfo"]
  """
  symbols = db["cryptoCollection"]
  symbolStr = ','.join(symbols)
  url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
  params = {
    "symbol": symbolStr
  }
  headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': '48ca8a26-d287-45bf-9ca2-b35926510638',
  }
  
  session = Session()
  session.headers.update(headers)
  response = session.get(url, params=params)
  data = json.loads(response.text)
  cryptoInfo = {}
  for sym in symbols:
    name = sym
    percentChange24hr = round(data['data'][name]['quote']['USD']['percent_change_24h'],2)
    currentPrice = round(data['data'][name]['quote']['USD']['price'],2)
    cryptoInfo[sym] = {"24HourChange":percentChange24hr, "currentPrice": currentPrice}
  db["cryptoInfo"] = cryptoInfo
  return cryptoInfo

def getETHPrice():
  """Fetches current ETH prices in USD."""
  url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
  params = {
    "symbol": "ETH"
  }
  headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': '48ca8a26-d287-45bf-9ca2-b35926510638',
  }
  session = Session()
  session.headers.update(headers)
  response = session.get(url, params=params)
  data = json.loads(response.text)
  ETHPrice = round(data['data']['ETH']['quote']['USD']['price'],2)
  db["ETHPrice"] = ETHPrice

def addCryptoToList(symbol):
  """add it's crypto to list of cryptos tracked """

  if "cryptoCollection" in db.keys():
    collection = db["cryptoCollection"]
    collection.append(symbol)
    db["cryptoCollection"] = collection
  else:
    db["cryptoCollection"] = [symbol]
  

def get_data():
  """Fetches and returns data for all currently tracked collections.
  """
  # OpenSea API https://docs.opensea.io/reference/retrieving-collection-stats
  all_data = []
  for item in db["collection"]:
    url = "https://api.opensea.io/api/v1/collection/" + item + "/stats"
    headers = {"Accept": "application/json"}
    response = requests.request("GET", url, headers=headers)
    json_data = json.loads(response.text)
    response = json_data["stats"]
    all_data.append(response)
  return(all_data)

def get_collection_info(slug):
  """Fetches and returns JSON data for a particular collection.
  """
  url = "https://api.opensea.io/api/v1/collection/" + slug
  response = requests.request("GET", url)
  json_data = json.loads(response.text)["collection"]
  return json_data


def add_collection(slug):
  """Adds a collection to be tracked. Input can be the full URL or the slug (endpoint).
  """
  if "collection" in db.keys():
    collection = db["collection"]
    collection.append(slug)
    db["collection"] = collection
  else:
    db["collection"] = [slug]

def remove_collection(slug):
  """Removes a collection that is being tracked. Input can be the full URL or the slug (endpoint).
  If the URL/slug that the user types is not currently being tracked, nothing happens.
  """
  collection = db["collection"]
  if slug in collection:
    collection.remove(slug)
    db["collection"] = collection

def check_collection(slug):
  """Checks if the user input collection exists on OpenSea. Return True if so, False otherwise.
  """
  url = "https://api.opensea.io/api/v1/collection/" + slug + "/stats"
  headers = {"Accept": "application/json"}
  response = requests.request("GET", url, headers=headers)
  if response.status_code != 200:
    return False
  return True

def check_interval(user_interval):
  """Checks if the interval used in the !interval command is valid. Valid is defined as over 1.00 minutes and under 10800.00 minutes (1 week)"""
  if (user_interval < 1.00 or user_interval > 10800.00):
    return False
  return True

def get_channel_id():
  # Start of code to get channel for bot-commands
  channel_id = ''
  for channel in client.get_all_channels():
    if channel.name == "bot-commands":
      channel_id = channel.id
  return channel_id
  # End of code to get channel for bot-commands
  
# Tutorial https://www.youtube.com/watch?v=SPTfmiYiuok
# This helped fix the bot https://stackoverflow.com/questions/70920148/pycord-message-content-is-empty/70920258
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# These lines execute after the bot has fully loaded.
@client.event
async def on_ready():
  print('We have logged in as {0.user}'.format(client))
  # Starts the 'tracking' loop
  NFTLoop.start()
  await display_landing_help()

@tasks.loop(minutes=db["interval"])
async def NFTLoop():
  """Goes through all the currently tracked collections and retrieves floor prices for each one. The notification interval is initially set to 60 minutes and can be changed. Time units are always in minutes.
  """
  channel = client.get_channel(get_channel_id())
  await display_collection_stats()
  cryptoData = getCryptoData()
  await display_crypto_list(cryptoData)

# -------------------------------------------------------
# Start of template for embeds
    
# embed = discord.Embed(
#     title = 'Title',
#     description = 'A test description',
#     colour = discord.Colour.blue()
#   )
#   embed.set_footer(text='This is a footer')
#   embed.set_image(url='https://cdn.discordapp.com/avatars/172795799552393216/57c11124d1dfec5c14b362c872050921.webp?size=64')
#   embed.set_thumbnail(url='https://cdn.discordapp.com/avatars/172795799552393216/57c11124d1dfec5c14b362c872050921.webp?size=64')
#   embed.set_author(name='Test Author', icon_url='https://cdn.discordapp.com/avatars/172795799552393216/57c11124d1dfec5c14b362c872050921.webp?size=64')
#   embed.add_field(name='Field 1', value='Field 1 value', inline=False)
#   embed.add_field(name='Field 2', value='Field 2 value', inline=True)
#   embed.add_field(name='Field 3', value='Field 3 value', inline=True)
    
# End of template for embeds
# -------------------------------------------------------

async def display_landing_help():
  channel = client.get_channel(get_channel_id())
  embed = discord.Embed(
    title = 'Type `!help` to get started with SCRPR!',
    colour = discord.Colour.yellow()
  )
  embed.set_footer(text='SCRPR MVP#1')
  embed.set_author(name='SCRPR Information')
  
  await channel.send(embed=embed)

async def display_crypto_list(cryptoData):
  channel = client.get_channel(get_channel_id())
  cryptoDataKeys = db["cryptoCollection"]
  for key in cryptoDataKeys:
    priceChange = cryptoData[key]["24HourChange"]
    currentPrice = cryptoData[key]["currentPrice"]
    embed = discord.Embed(
      title = 'Recent Price Movements on {}'.format(key),
      colour = discord.Colour.blue()
    )

    embed.set_footer(text='SCRPR MVP#1')
    embed.set_author(name='Crypto Information')
    #embed.set_thumbnail(url=collection_info["image_url"])
    embed.add_field(name='Current Price', value='${}'.format(currentPrice))
    embed.add_field(name='24-hour price change', value='{}%'.format(priceChange))
    await channel.send(embed=embed)

async def display_crypto_fail(type):
  channel = client.get_channel(get_channel_id())
  embed = discord.Embed(
    title = 'Crypto add',
    colour = discord.Colour.red()
  )
  embed.set_footer(text='SCRPR MVP#1')
  if type == "no_exist":
    embed.add_field(name='Error', value='Coin does not exist')
  elif type == "already_tracked":
    embed.add_field(name='Error', value='Coin already being tracked')
  await channel.send(embed=embed)

async def display_crypto_remove_fail():
  channel = client.get_channel(get_channel_id())
  embed = discord.Embed(
    title = 'Crypto remove',
    color = discord.Colour.red()
  )

  embed.set_footer(text='SCRPR MVP#1')
  embed.add_field(name="ERROR", value="Coin was not being tracked")
  await channel.send(embed=embed)

async def display_crypto_remove_success():
  channel = client.get_channel(get_channel_id())
  embed = discord.Embed(
    title = 'Crypto remove',
    color = discord.Colour.blue()
  )

  embed.set_footer(text='SCRPR MVP#1')
  embed.add_field(name="Success", value="Coin was no longer being tracked")
  await channel.send(embed=embed)

async def display_collection_stats():
  channel = client.get_channel(get_channel_id())
  data = get_data()
  getETHPrice()
  ETHPrice = db["ETHPrice"]
  all_collections = db["collection"]
  for i, collection in enumerate(all_collections):
    opensea_url = 'https://opensea.io/collection/' + collection
    collection_info = get_collection_info(collection)
    floor_price = round(data[i]["floor_price"], 2)
    one_day_volume = round(data[i]["one_day_volume"], 2)
    one_day_change = round(data[i]["one_day_change"], 2)
    one_day_average_price = round(data[i]["one_day_average_price"], 2)

    # ----- START EMBED -----
    embed = discord.Embed(
      title = 'Portfolio Notification on {}'.format(collection_info["name"]),
      colour = discord.Colour.blue()
    )
    embed.set_footer(text='SCRPR MVP#1')
    embed.set_author(name='Collection Information')
    embed.set_thumbnail(url=collection_info["image_url"])
    embed.add_field(name='Floor price', value='{}?? | ${}'.format(floor_price, "{:,}".format(round(floor_price*ETHPrice, 2))))
    embed.add_field(name='24-hour volume', value='{}?? | ${}'.format(one_day_volume, "{:,}".format(round(one_day_volume*ETHPrice, 2))))
    embed.add_field(name='24-hour price change', value='{}%'.format(one_day_change))
    embed.add_field(name='24-hour average price', value='{}?? | ${}'.format(one_day_average_price, "{:,}".format(round(one_day_average_price*ETHPrice, 2))))
    embed.add_field(name='See more', value='[OpenSea]({})'.format(opensea_url))
    # ----- END EMBED -----
    await channel.send(embed=embed)

async def display_help():
  channel = client.get_channel(get_channel_id())
  embed = discord.Embed(
    title = 'Information about SCRPR',
    description = 'Welcome to SCRPR! This bot helps you keep track of NFT collection statistics and cryptocurrency prices. By default, you will be notified on prices for collections/crypto every `60 minutes`',
    colour = discord.Colour.yellow()
  )
  embed.set_footer(text='SCRPR MVP#1')
  embed.set_author(name='Help')
  embed.add_field(name='Commands', value='`!add` | `!remove` | `!list` | `!interval` | `!reset` | `!prices` | `!crypto add` | `!crypto remove` | `!crypto list` \n', inline=False)
  embed.add_field(name='!add [link/slug]', value='Adds a collection to be tracked \n _Examples_ \n !add `https://opensea.io/collection/azuki` \n !add `boredapeyachtclub`', inline=False)
  embed.add_field(name='!remove [link/slug]', value='Removes a tracked collection \n _Examples_ \n !remove `https://opensea.io/collection/azuki` \n !remove `boredapeyachtclub`', inline=False)
  embed.add_field(name='!list', value='Shows all currently tracked collections', inline=False)
  embed.add_field(name='!interval [number]', value='Changes the notification interval. Default is set to `60 minutes`. Accepts whole numbers or decimals. NOTE: scale is in `minutes` \n _Examples_ \n !interval `30` - Sets notification interval to `30 minutes` \n !interval `0.5` - Sets notification interval to `0.5 minutes`', inline=False)
  embed.add_field(name='!reset', value='Clears all tracked collections AND cryptocurrencies. Sets the notification interval to the default `60 minutes`', inline=False)
  embed.add_field(name='!prices', value='Displays the current floor prices for all tracked collections', inline=False)
  embed.add_field(name='!crypto add [symbol]', value='Adds a cryptocurrency to be tracked \n _Examples_ \n !crypto add `BTC`\n !crypto add `ETH`\n', inline=False)
  embed.add_field(name='!crypto remove [symbol]', value='Removes a tracked cryptocurrency \n _Examples_ \n !crypto remove `BTC` \n !crypto remove `ETH`', inline=False)
  embed.add_field(name='!crypto list', value='Shows all currently tracked cryptocurrencies')

  await channel.send(embed=embed)

async def display_add_collection_success(slug):
  channel = client.get_channel(get_channel_id())
  collection_info = get_collection_info(slug)
  opensea_url = 'https://opensea.io/collection/' + slug
  embed = discord.Embed(
    title = '{} is now being tracked'.format(collection_info["name"]),
    colour = discord.Colour.blue()
  )
  embed.set_footer(text='SCRPR MVP#1')
  embed.set_author(name='Add')
  embed.set_thumbnail(url=collection_info["image_url"])
  embed.add_field(name='Links', value='[Discord Server]({}) \n [OpenSea]({})'.format(collection_info["discord_url"], opensea_url))
  
  await channel.send(embed=embed)

async def display_add_collection_fail(type):
  channel = client.get_channel(get_channel_id())
  embed = discord.Embed(
    colour = discord.Colour.red()
  )
  embed.set_footer(text='SCRPR MVP#1')
  embed.set_author(name='Add')
  if type == "no_exist":
    embed.add_field(name='Error', value='Collection does not exist')
  elif type == "already_tracked":
    embed.add_field(name='Error', value='Collection already being tracked')

  await channel.send(embed=embed)

async def display_remove_collection_success(slug):
  channel = client.get_channel(get_channel_id())
  collection_info = get_collection_info(slug)
  opensea_url = 'https://opensea.io/collection/' + slug
  embed = discord.Embed(
    title = '{} is no longer being tracked'.format(collection_info["name"]),
    colour = discord.Colour.blue()
  )
  embed.set_footer(text='SCRPR MVP#1')
  embed.set_author(name='Remove')
  embed.set_thumbnail(url=collection_info["image_url"])
  embed.add_field(name='Links', value='[Discord Server]({}) \n [OpenSea]({})'.format(collection_info["discord_url"], opensea_url))
  
  await channel.send(embed=embed)

async def display_remove_collection_fail(type):
  channel = client.get_channel(get_channel_id())
  embed = discord.Embed(
    colour = discord.Colour.red()
  )
  embed.set_footer(text='SCRPR MVP#1')
  embed.set_author(name='Remove')
  if type == "no_exist":
    embed.add_field(name='Error', value='Collection does not exist')
  elif type == "not_tracked":
    embed.add_field(name='Error', value='Collection not being tracked')

  await channel.send(embed=embed)

async def display_list(tracked_collections):
  channel = client.get_channel(get_channel_id())
  embed = discord.Embed(
    title = 'Currently tracked collections',
    colour = discord.Colour.blue()
  )
  embed.set_footer(text='SCRPR MVP#1')
  embed.set_author(name='List')
  if not tracked_collections:
    embed.add_field(name='Information', value='Nothing being tracked')
    await channel.send(embed=embed)
    return
  for item in tracked_collections:
    collection_data = get_collection_info(item)
    opensea_url = 'https://opensea.io/collection/' + item
    embed.add_field(name='{}'.format(collection_data["name"]), value='[OpenSea]({})'.format(opensea_url))
  await channel.send(embed=embed)
  
async def display_interval(new_interval):
  channel = client.get_channel(get_channel_id())
  embed = discord.Embed(
    colour = discord.Colour.blue()
  )
  embed.set_footer(text='SCRPR MVP#1')
  embed.set_author(name='Interval')
  embed.add_field(name='Information', value='New interval set to `{} minute(s)`'.format(new_interval))
  await channel.send(embed=embed)

async def display_invalid_interval():
  channel = client.get_channel(get_channel_id())
  embed = discord.Embed(
    colour = discord.Colour.red()
  )
  embed.set_footer(text='SCRPR MVP#1')
  embed.set_author(name='Interval')
  embed.add_field(name='Information', value='Invalid Interval. Minimum value is 1.00 minutes and maximum value is 10080.00 minutes (1 week). Please do not input non-numerical values.')
  await channel.send(embed=embed)

async def display_reset():
  channel = client.get_channel(get_channel_id())
  embed = discord.Embed(
    colour = discord.Colour.blue()
  )
  embed.set_footer(text='SCRPR MVP#1')
  embed.set_author(name='Reset')
  embed.add_field(name='Information', value='Reset interval to `60 minutes` \n Cleared all tracked NFT collections and cryptocurrencies')
  await channel.send(embed=embed)

@client.event
async def on_message(message):
  """Listener function to watch for commands.
  """
  if message.author == client.user:
    return

  # For convenience
  msg = message.content

  # Help (!help) command. For now it's hardcoded to print all the help information.
  if msg.startswith('!help'):
    await display_help()

  # Current price command (!prices). Displays the prices at the time of command input for all tracked collections.
  if msg.startswith('!prices'):
    await display_collection_stats()

  # Shows all tracked collections
  if msg.startswith("!list"):
    collection = []
    if "collection" in db.keys():
      collection = db["collection"]
    await display_list(collection)
  
  # Adds a collection to be tracked
  if msg.startswith("!add"):
    # get the URL, trim to slug
    slug = msg.split("!add ",1)[1].rsplit('/', 1)[-1]
    collection = db["collection"]
    # check if collection doesn't exist
    if not check_collection(slug):
      await display_add_collection_fail("no_exist")
      return
    # check if collection is already being tracked
    if slug in collection:
      await display_add_collection_fail("already_tracked")
      return
    add_collection(slug)
    await display_add_collection_success(slug)

  # Removes a tracked collection
  if msg.startswith("!remove"):
    collection = []
    # get the URL, trim to slug
    slug = msg.split("!remove ",1)[1].rsplit('/', 1)[-1]
    if not check_collection(slug):
      await display_remove_collection_fail("no_exist")
      return
    if "collection" in db.keys():
      existence_check = db["collection"]
      if slug not in existence_check:
        await display_remove_collection_fail("not_tracked")
        return
      remove_collection(slug)
      collection = db["collection"]
    await display_remove_collection_success(slug)

  # Allows the user to change the notification interval. Input is always interpreted as minutes. Decimals are accepted. The bot displays the current price of all tracked collections
  if msg.startswith("!interval"):
    new_interval = msg.split("!interval ",1)[1]
    # check if interval is invalid
    if (type(new_interval) != float or not check_interval(new_interval)):
      await display_invalid_interval()
    # Invalid interval, display error message
    else:
      new_interval = float(new_interval)
      db["interval"] = new_interval
      NFTLoop.change_interval(minutes=db["interval"])
      NFTLoop.restart()
      await display_interval(new_interval)

  # Resets notification interval to 60 minutes and clears all tracked collections.
  if msg.startswith("!reset"):
    db["interval"] = 60
    db["collection"] = []
    NFTLoop.change_interval(minutes=db["interval"])
    NFTLoop.restart()
    db["cryptoCollection"] = []
    db["cryptoInfo"] = {}
    await display_reset()

  if msg.startswith("!crypto add"):
    new_sym = msg.split("!crypto add ",1)[1]
    if (coinExists(new_sym) == False):
      await display_crypto_fail("no_exist")
    elif ("cryptoCollection" in db.keys() and new_sym in db["cryptoCollection"])  :
      print(db["cryptoCollection"])
      await display_crypto_fail("already_tracked")
    else:
      addCryptoToList(new_sym)
      cryptoData = getCryptoData()
      await display_crypto_list(cryptoData)
    
  if msg.startswith("!crypto list"):
    if "cryptoInfo" not in db.keys():
      await message.channel.send("No cryptos being tracked")
    else:
      cryptoDataKeys = db["cryptoCollection"]
      cryptoData = db["cryptoInfo"]
      await display_crypto_list(cryptoData)

  if msg.startswith("!crypto remove"):
    del_sym = msg.split("!crypto remove ",1)[1]
    if ("cryptoCollection" not in db.keys() or del_sym not in db["cryptoCollection"]):
      await display_crypto_remove_fail()
    else:
      db["cryptoCollection"].remove(del_sym)
      await display_crypto_remove_success()
      
    
# To keep the bot running 24/7 and check for rate limits.
keep_alive()
try:
  client.run(os.getenv('TOKEN'))
except:
  os.system("kill 1")
