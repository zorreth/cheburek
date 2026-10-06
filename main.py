import os
import random
import re

import discord
from dotenv import load_dotenv

from markov_chain import MarkovChain

load_dotenv()

chain = MarkovChain()
chain.load()

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    print(f"🥟 Logged in as {bot.user}!")


@bot.event
async def on_message(ctx: discord.Message):
    if ctx.author.bot:
        return

    # Clean up and process the words

    clean_content = re.sub(
        r"^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$",
        "",
        ctx.content,
    )
    clean_content = re.sub(r"<@!?\d+>", "", clean_content)
    clean_content = re.sub(r"\s+", " ", clean_content).strip()

    words = clean_content.split(" ")
    chain.process_words(words)

    # Randomly generate and send a message

    if random.random() < float(os.environ["MESSAGE_CHANCE"]):
        message = chain.generate_message(random.randint(2, 12))

        try:
            await ctx.channel.send(message)
        except Exception as e:
            print("Failed to send message:", e)


@bot.command(description="Сгенерировать сообщение")
async def generate(interaction: discord.Interaction):
    try:
        message = chain.generate_message(random.randint(2, 12))
        await interaction.response.send_message(message)
    except Exception as e:
        print("Failed to generate message:", e)
        await interaction.response.send_message("Произошла ошибка!", ephemeral=True)


@bot.command(description="Показать статистику")
async def stats(interaction: discord.Interaction):
    words = chain.get_words_count()
    links = chain.get_links_count()

    embed = discord.Embed(
        title="Статистика",
        description="Количество изученных слов и связей",
        color=discord.Color.orange(),
    )

    embed.add_field(name="📖 Слова", value=f"{words} слов")
    embed.add_field(name="🔗 Связи", value=f"{links} связей")

    await interaction.response.send_message(embed=embed)


bot.run(os.environ["TOKEN"])
