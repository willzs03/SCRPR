import discord
from discord.ext import tasks
import os
import requests
import json
from replit import db
from keep_alive import keep_alive

# interval at which the bot retrieves info in MINUTES. Setting default to 60 minutes.
db["interval"] = 60

def get_data():
  """Fetches and returns floor prices for all currently tracked collections.
  """
  # OpenSea API https://docs.opensea.io/reference/retrieving-collection-stats
  all_data = []
  for item in db["collection"]:
    url = "https://api.opensea.io/api/v1/collection/" + item + "/stats"
    headers = {"Accept": "application/json"}
    response = requests.request("GET", url, headers=headers)
    json_data = json.loads(response.text)
    response = json_data["stats"]["floor_price"]
    all_data.append(response)
  return(all_data)

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

def main():
  # Tutorial https://www.youtube.com/watch?v=SPTfmiYiuok
  # This helped fix the bot https://stackoverflow.com/questions/70920148/pycord-message-content-is-empty/70920258
  intents = discord.Intents.all()
  client = discord.Client(intents=intents)

  # These lines execute after the bot has fully loaded.
  @client.event
  async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    # Starts the 'tracking' loop
    myLoop.start()

  @tasks.loop(minutes=db["interval"])
  async def myLoop():
    """Goes through all the currently tracked collections and retrieves floor prices for each one. The notification interval is initially set to 60 minutes and can be changed. Time units are always in minutes.
    """
    channel = client.get_channel(950141811601600562)
    data = get_data()
    all_collections = db["collection"]
    for i, collection in enumerate(all_collections):
      floor_price = data[i]
      await channel.send("{} floor price is {}Ξ".format(collection, floor_price))

  
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
      await message.channel.send('**Information** \n\n Welcome to SCRPR! This bot helps you keep track of NFT collection prices. By default, you will be notified on floor prices of tracked collections every `60 minutes (1 hour)`. \n\n **Commands**: !add  !remove  !list  !interval  !reset  !prices  \n\n  **Usage**:  \n  !add [link] - adds a collection to be tracked  \n\n  !remove [link] - removes a collection from the tracked list  \n\n  !list - shows currently tracked collections  \n\n  !interval [number] - default is set to `60 minutes`. Type in any number (even decimals) to change the interval. NOTE: Scale is in minutes, so doing !interval 30 will set the interval to `30 minutes`  \n\n  !reset - resets the interval to `60 minutes` and clears all tracked collections  \n\n  !prices - displays the current floor prices for all tracked collections')

    # Current price command (!prices). Displays the prices at the time of command input for all tracked collections.
    if msg.startswith('!prices'):
      data = get_data()
      all_collections = db["collection"]
      for i, collection in enumerate(all_collections):
        floor_price = data[i]
        await message.channel.send("{} floor price is {}Ξ".format(collection, floor_price))

    # Shows all tracked collections
    if msg.startswith("!list"):
      collection = []
      if "collection" in db.keys():
        collection = db["collection"]
      await message.channel.send(collection)

    # Adds a collection to be tracked
    if msg.startswith("!add"):
      # get the URL, trim to slug
      slug = msg.split("!add ",1)[1].rsplit('/', 1)[-1]
      collection = db["collection"]
      # check if collection doesn't exist
      if not check_collection(slug):
        await message.channel.send("Collection doesn't exist")
        return
      # check if collection is already being tracked
      if slug in collection:
        await message.channel.send("Collection already being tracked")
        return
      add_collection(slug)
      await message.channel.send("New collection added!")

    # Removes a tracked collection
    if msg.startswith("!remove"):
      collection = []
      # get the URL, trim to slug
      slug = msg.split("!remove ",1)[1].rsplit('/', 1)[-1]
      if "collection" in db.keys():
        existence_check = db["collection"]
        if slug not in existence_check:
          await message.channel.send("Collection not being tracked")
          return
        remove_collection(slug)
        collection = db["collection"]
      await message.channel.send("Collection deleted, see currently tracked collections below")
      await message.channel.send(collection)

    # Allows the user to change the notification interval. Input is always interpreted as minutes. Decimals are accepted. The bot displays the current price of all tracked collections
    if msg.startswith("!interval"):
      new_interval = float(msg.split("!interval ",1)[1])
      db["interval"] = new_interval
      myLoop.change_interval(minutes=new_interval)
      myLoop.restart()
      await message.channel.send("New interval set to `{} minute(s)`".format(new_interval))

    # Resets notification interval to 60 minutes and clears all tracked collections.
    if msg.startswith("!reset"):
      db["interval"] = 60
      db["collection"] = []
      myLoop.change_interval(minutes=db["interval"])
      myLoop.restart()
      await message.channel.send("Reset interval to `60 minutes` \n Cleared all tracked collections")
      
  # To keep the bot running 24/7 and check for rate limits.
  keep_alive()
  try:
    client.run(os.getenv('TOKEN'))
  except:
    os.system("kill 1")

if __name__ == '__main__':
  main()