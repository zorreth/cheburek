import os

import discord
import regex
from dotenv import load_dotenv

from markov_chain import MarkovChain

load_dotenv()

chain = MarkovChain()


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"🥟 Logged in as {client.user}!")


@client.event
async def on_message(ctx: discord.Message):
    if ctx.author.bot:
        return

    # Keep only letters, numbers, punctuation and spaces.
    clean_content = regex.sub(r"[^\p{L}\p{N}\p{P}\s]+", "", ctx.content)

    words = clean_content.split(" ")
    chain.process_words(words)


client.run(os.environ["TOKEN"])
