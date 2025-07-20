import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction, Embed
import os, json
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ملف البيانات
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

# أوامر الإدارة
@bot.tree.command(name="إنشاء_متجر")
@app_commands.describe(الاسم="اسم المتجر")
async def انشاء_متجر(interaction: Interaction, الاسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    data[gid] = {"store_name": الاسم, "categories": {}, "payment": "غير محدد", "order_channel": None}
    save_data(data)
    await interaction.response.send_message(f"✅ تم إنشاء المتجر باسم: {الاسم}", ephemeral=True)

@bot.tree.command(name="روم_التاجر")
@app_commands.describe(الروم="حدد روم استلام الطلبات")
async def روم_التاجر(interaction: Interaction, الروم: discord.TextChannel):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ يجب إنشاء متجر أولاً.", ephemeral=True)
        return
    data[gid]["order_channel"] = الروم.id
    save_data(data)
    await interaction.response.send_message(f"✅ تم تعيين روم التاجر: {الروم.mention}", ephemeral=True)

@bot.tree.command(name="إضافة_قسم")
@app_commands.describe(الاسم="اسم القسم")
async def اضافة_قسم(interaction: Interaction, الاسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ يجب إنشاء متجر أولاً.", ephemeral=True)
        return
    data[gid]["categories"][الاسم] = {}
    save_data(data)
    await interaction.response.send_message(f"✅ تم إضافة القسم: {الاسم}", ephemeral=True)

@bot.tree.command(name="إضافة_منتج")
@app_commands.describe(القسم="اسم القسم", الاسم="اسم المنتج", الكمية="الكمية المتوفرة", السعر="السعر")
async def اضافة_منتج(interaction: Interaction, القسم: str, الاسم: str, الكمية: int, السعر: int):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data or القسم not in data[gid]["categories"]:
        await interaction.response.send_message("❌ تأكد من وجود المتجر والقسم.", ephemeral=True)
        return
    data[gid]["categories"][القسم][الاسم] = {"quantity": الكمية, "price": السعر}
    save_data(data)
    await interaction.response.send_message(f"✅ تمت إضافة المنتج: {الاسم} في القسم: {القسم}", ephemeral=True)

@bot.tree.command(name="حذف_قسم")
@app_commands.describe(الاسم="اسم القسم")
async def حذف_قسم(interaction: Interaction, الاسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data and الاسم in data[gid]["categories"]:
        del data[gid]["categories"][الاسم]
        save_data(data)
        await interaction.response.send_message(f"✅ تم حذف القسم: {الاسم}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)

@bot.tree.command(name="حذف_منتج")
@app_commands.describe(القسم="اسم القسم", الاسم="اسم المنتج")
async def حذف_منتج(interaction: Interaction, القسم: str, الاسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data and القسم in data[gid]["categories"] and الاسم in data[gid]["categories"][القسم]:
        del data[gid]["categories"][القسم][الاسم]
        save_data(data)
        await interaction.response.send_message(f"✅ تم حذف المنتج: {الاسم} من القسم: {القسم}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ المنتج أو القسم غير موجود.", ephemeral=True)

@bot.tree.command(name="تحديد_رابط_الدفع")
@app_commands.describe(الرابط="رابط الدفع")
async def تحديد_رابط_الدفع(interaction: Interaction, الرابط: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ يجب إنشاء متجر أولاً.", ephemeral=True)
        return
    data[gid]["payment"] = الرابط
    save_data(data)
    await interaction.response.send_message("✅ تم تحديث رابط الدفع", ephemeral=True)

# Flask للتشغيل في Render
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل"

Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

bot.run(os.getenv("TOKEN"))

