import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction, Embed, ButtonStyle
import os, json
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ تم تسجيل {len(bot.tree.get_commands())} أمر سلاش")

@bot.tree.command(name="تعديل_منتج")
@app_commands.describe(القسم="اسم القسم", الاسم_الحالي="اسم المنتج الحالي", الاسم_الجديد="الاسم الجديد (اختياري)", الكمية="الكمية (اختياري)", السعر="السعر (اختياري)")
async def تعديل_منتج(interaction: Interaction, القسم: str, الاسم_الحالي: str, الاسم_الجديد: str = None, الكمية: int = None, السعر: int = None):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data or القسم not in data[gid]["categories"] or الاسم_الحالي not in data[gid]["categories"][القسم]:
        await interaction.response.send_message("❌ تأكد من وجود المتجر والقسم والمنتج.", ephemeral=True)
        return

    المنتج = data[gid]["categories"][القسم].pop(الاسم_الحالي)

    if الاسم_جديد:
        الاسم = الاسم_جديد
    else:
        الاسم = الاسم_الحالي

    if الكمية is not None:
        المنتج["quantity"] = الكمية
    if السعر is not None:
        المنتج["price"] = السعر

    data[gid]["categories"][القسم][الاسم] = المنتج
    save_data(data)
    await interaction.response.send_message(f"✅ تم تعديل المنتج: {الاسم}", ephemeral=True)

@bot.tree.command(name="تعديل_قسم")
@app_commands.describe(الاسم_الحالي="اسم القسم الحالي", الاسم_الجديد="الاسم الجديد للقسم")
async def تعديل_قسم(interaction: Interaction, الاسم_الحالي: str, الاسم_الجديد: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data or الاسم_الحالي not in data[gid]["categories"]:
        await interaction.response.send_message("❌ القسم غير موجود أو لم يتم إنشاء متجر.", ephemeral=True)
        return

    data[gid]["categories"][الاسم_الجديد] = data[gid]["categories"].pop(الاسم_الحالي)
    save_data(data)
    await interaction.response.send_message(f"✅ تم تعديل اسم القسم إلى: {الاسم_الجديد}", ephemeral=True)

# باقي الأوامر تبقى كما هي...

# تأكد من مزامنة الأوامر بعد التعديل
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ تم تسجيل {len(bot.tree.get_commands())} أمر سلاش")

app = Flask('')
@app.route('/')
def home(): return "البوت يعمل"

Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

bot.run(os.getenv("TOKEN"))
