import io
import os
import random
import re
import textwrap
from pathlib import Path

import discord
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

from markov_chain import MarkovChain
from meme_generator import MemeGenerator

load_dotenv()

chain = MarkovChain()
chain.load()

meme = MemeGenerator()

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

    # Save image attachments

    image_dir = Path("./images")
    image_dir.mkdir(parents=True, exist_ok=True)

    for a in ctx.attachments:
        if (
            a.content_type == "image/png"
            or a.content_type == "image/jpeg"
            or a.content_type == "image/webp"
        ):
            await a.save(image_dir / str(ctx.id))
            print(f"🌅 New image from {ctx.author}")

    # Reply when someone mentioned/replied to bot

    mentioned = bot.user in ctx.mentions

    replied = (
        ctx.reference != None
        and isinstance(ctx.reference.resolved, discord.Message)
        and ctx.reference.resolved.author == bot.user
    )

    if mentioned or replied:
        message = chain.generate_message(random.randint(2, 12))

        try:
            await ctx.reply(message)
        except Exception as e:
            print("Failed to reply a message:", e)
    else:
        # Try a chance to generate and send a message

        if random.random() < float(os.environ["MESSAGE_CHANCE"]):
            message = chain.generate_message(random.randint(2, 12))

            try:
                await ctx.channel.send(message)
            except Exception as e:
                print("Failed to send message:", e)


class GenerateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="🔁 Перегенерировать", style=discord.ButtonStyle.primary)
    async def regenerate(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        await interaction.response.defer()

        message = chain.generate_message(random.randint(2, 12))

        await interaction.edit_original_response(
            content=message, attachments=[], view=self
        )

    @discord.ui.button(label="👴 Жак Фреско", style=discord.ButtonStyle.secondary)
    async def fresco(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()

        if not interaction.message:
            return

        img = meme.create_fresco(interaction.message.content)

        with io.BytesIO() as image_binary:
            img.save(image_binary, "PNG")
            image_binary.seek(0)

            await interaction.followup.send(
                file=discord.File(fp=image_binary, filename="fresco.png"),
            )


@bot.command(description="Сгенерировать сообщение")
async def generate(interaction: discord.Interaction):
    try:
        message = chain.generate_message(random.randint(2, 12))
        await interaction.response.send_message(message, view=GenerateView())
    except Exception as e:
        print("Failed to generate message:", e)
        await interaction.response.send_message("Произошла ошибка!", ephemeral=True)


@bot.command(description="Сгенерировать демотиватор")
async def demotivator(interaction: discord.Interaction):
    message = chain.generate_message(random.randint(2, 8))
    image = "./images/" + random.choice(os.listdir("./images"))

    img = meme.create_demotivator(message, image)

    with io.BytesIO() as image_binary:
        img.save(image_binary, "PNG")
        image_binary.seek(0)

        await interaction.response.send_message(
            file=discord.File(fp=image_binary, filename="demotivator.png")
        )


@bot.command(description="Показать статистику")
async def stats(interaction: discord.Interaction):
    words = chain.get_words_count()
    links = chain.get_links_count()

    images = len(os.listdir("./images"))

    embed = discord.Embed(
        title="Статистика",
        description="Количество изученных данных",
        color=discord.Color.orange(),
    )

    embed.add_field(name="📖 Слова", value=f"{words} слов")
    embed.add_field(name="🔗 Связи", value=f"{links} связей")
    embed.add_field(name="🌅 Картинки", value=f"{images} картинок")

    await interaction.response.send_message(embed=embed)


bot.run(os.environ["TOKEN"])
