import discord
from discord.ext import commands
from keep_alive import keep_alive
import os

# تشغيل السيرفر الصغير (مهم عشان Render ما يطفي)
keep_alive()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("pong!")

# تشغيل البوت باستخدام التوكن من متغير البيئة
bot.run(os.getenv("TOKEN"))

