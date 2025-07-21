import discord
from discord.ext import commands
from discord import app_commands
import json
import uuid
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
tree = app_commands.CommandTree()

bot = commands.Bot(command_prefix="!", intents=intents)

# تحميل البيانات من ملف JSON
try:
    with open("data.json", "r") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {}

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")

# ... باقي الأوامر ...

@tree.command(name="تقييم", description="تقييم الطلب")
@app_commands.describe(الطلب="صف الطلب أو المنتج", التقييم="التقييم من 1 إلى 5")
async def تقييم(interaction: discord.Interaction, الطلب: str, التقييم: app_commands.Range[int, 1, 5]):
    guild_id = str(interaction.guild.id)
    trader_channel_id = data.get(guild_id, {}).get("trader_channel_id")

    if not trader_channel_id:
        await interaction.response.send_message("❌ لم يتم تحديد روم التاجر بعد.", ephemeral=True)
        return

    التاجر_channel = bot.get_channel(trader_channel_id)
    if not التاجر_channel:
        await interaction.response.send_message("❌ لا يمكن العثور على روم التاجر المحدد.", ephemeral=True)
        return

    embed = discord.Embed(title="⭐ تقييم جديد", color=discord.Color.gold())
    embed.add_field(name="👤 العميل", value=interaction.user.mention, inline=True)
    embed.add_field(name="📦 الطلب", value=الطلب, inline=False)
    embed.add_field(name="⭐ التقييم", value=f"{"⭐" * التقييم} ({التقييم}/5)", inline=True)

    await التاجر_channel.send(embed=embed)
    await interaction.response.send_message("✅ تم إرسال التقييم، شكرًا لك!", ephemeral=True)

keep_alive()
bot.run(os.environ["TOKEN"])
