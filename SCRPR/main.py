import discord
# from discord import task
import os
import requests
import json
from threading import Thread
import time
from replit import db
from keep_alive import keep_alive

#can we make edits? We can cool!

# interval at which the bot retrieves info. Expressed in seconds, default is 1 hr.
db["interval"] = 3600

def get_data():
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
  if "collection" in db.keys():
    collection = db["collection"]
    collection.append(slug)
    db["collection"] = collection
  else:
    db["collection"] = [slug]

def remove_collection(slug):
  collection = db["collection"]
  if slug in collection:
    collection.remove(slug)
    db["collection"] = collection

def check_collection(slug):
  url = "https://api.opensea.io/api/v1/collection/" + slug + "/stats"
  headers = {"Accept": "application/json"}
  response = requests.request("GET", url, headers=headers)
  if response.status_code != 200:
    return False
  return True

def main():
  class OpenSeaAPI(Thread):
    def __init__(self):
      Thread.__init__(self)
      self.daemon = True
      self.start()
    def run(self):
      while True:
        if len(db["collection"]) == 0:
          pass
        else:
          # call get_data() function
          print("something being tracked")
        time.sleep(10)

  # Tutorial https://www.youtube.com/watch?v=SPTfmiYiuok
  client = discord.Client()
  channel = client.get_channel(950141811601600562)
  print(channel)
  OpenSeaAPI()
  
  @client.event
  async def on_ready():
    print('We have logged in as {0.user}'.format(client))

  # @tasks.loop(seconds = 10) # repeat after every 10 seconds
  # async def myLoop():
  #   await message.channel.send("test")
  
  @client.event
  async def on_message(message):
    if message.author == client.user:
      return
  
    msg = message.content
    # try to clean this part, https://www.youtube.com/results?search_query=discord+bot+help+command+python
    if msg.startswith('!help'):
      await message.channel.send('**Information** \n\n Welcome to SCRPR! This bot helps you keep track of NFT collection prices. By default, you will be notified on floor prices of tracked collections every `1 hour`. \n\n **Commands**: !add  !remove  !list  !interval  !reset  \n\n  **Usage**:  \n  !add [link] - adds a collection to be tracked  \n\n  !remove [link] - removes a collection from the tracked list  \n\n  !list - shows currently tracked collections  \n\n  !interval [number] - default is set to `1 hour`. Type in any number (even decimals) to change the interval. NOTE: Scale is in hours, so doing !interval 0.5 will set the interval to `0.5 hours`  \n\n  !reset - resets the interval to `1 hour` and clears all tracked collections')
    
    if msg.startswith('!inspire'):
      data = get_data()
      all_collections = db["collection"]
      for i, collection in enumerate(all_collections):
        floor_price = data[i]
        await message.channel.send("{} floor price is {}Ξ".format(collection, floor_price))
        
    if msg.startswith("!list"):
      collection = []
      if "collection" in db.keys():
        collection = db["collection"]
      await message.channel.send(collection)
  
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
      await message.channel.send(collection)
  
    if msg.startswith("!interval"):
      # times 3600 because the Python sleep function is measured in seconds
      new_interval = float(msg.split("!interval ",1)[1]) * 3600.00
      db["interval"] = new_interval
      await message.channel.send("New interval set to `{} hour(s)`".format(new_interval / 3600))
  
    if msg.startswith("!reset"):
      db["interval"] = 3600
      db["collection"] = []
      await message.channel.send("Reset interval to `1 hour` \n Cleared all tracked collections")
  async def test():
    data = get_data()
    all_collections = db["collection"]
    for i, collection in enumerate(all_collections):
      floor_price = data[i]
      await message.channel.send("{} floor price is {}Ξ".format(collection, floor_price))
  # To keep the bot running 24/7
  keep_alive()
  client.run(os.getenv('TOKEN'))

if __name__ == '__main__':
  main()