
import discord
from discord import app_commands, Embed
from discord.ext import commands
import json
import os
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
TREE = bot.tree

# قاعدة بيانات JSON
DB_FILE = "data.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({}, f)

def load_data():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# سحب أو إنشاء متجر لسيرفر
def get_store(guild_id):
    data = load_data()
    return data.setdefault(str(guild_id), {"store_name": None, "sections": {}, "order_channel": None, "payment_link": None})

def update_store(guild_id, store):
    data = load_data()
    data[str(guild_id)] = store
    save_data(data)

# الأحداث
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await TREE.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

# إنشاء متجر
@TREE.command(name="إنشاء_متجر", description="إنشاء متجر جديد للسيرفر")
async def create_store(interaction: discord.Interaction, الاسم: str):
    store = get_store(interaction.guild.id)
    store["store_name"] = الاسم
    update_store(interaction.guild.id, store)
    await interaction.response.send_message(embed=Embed(title="✅ تم إنشاء المتجر", description=f"اسم المتجر: **{الاسم}**", color=0x00ff00))

# تحديد روم الطلبات
@TREE.command(name="تحديد_روم_الطلبات", description="حدد روم الطلبات")
async def set_order_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    store = get_store(interaction.guild.id)
    store["order_channel"] = channel.id
    update_store(interaction.guild.id, store)
    await interaction.response.send_message(embed=Embed(title="📥 تم تحديد روم الطلبات", description=f"{channel.mention}", color=0x00ff00))

# تحديد رابط الدفع
@TREE.command(name="تحديد_رابط_الدفع", description="حدد رابط الدفع الذي يظهر بالفاتورة")
async def set_payment_link(interaction: discord.Interaction, الرابط: str):
    store = get_store(interaction.guild.id)
    store["payment_link"] = الرابط
    update_store(interaction.guild.id, store)
    await interaction.response.send_message(embed=Embed(title="💸 تم تعيين رابط الدفع", description=f"الرابط: {الرابط}", color=0x00ff00))

# تنفيذ الطلب
@TREE.command(name="طلب", description="طلب منتج من المتجر")
async def place_order(interaction: discord.Interaction, القسم: str, المنتج: str):
    store = get_store(interaction.guild.id)
    if القسم not in store["sections"] or المنتج not in store["sections"][القسم]["products"]:
        await interaction.response.send_message(embed=Embed(title="❌ المنتج غير موجود", color=0xff0000), ephemeral=True)
        return

    السعر = store["sections"][القسم]["products"][المنتج]
    رابط_الدفع = store.get("payment_link", "لا يوجد رابط دفع محدد")
    order_embed = Embed(title="📦 فاتورة الطلب", color=0x3498db)
    order_embed.add_field(name="المنتج", value=المنتج, inline=False)
    order_embed.add_field(name="القسم", value=القسم, inline=False)
    order_embed.add_field(name="السعر", value=f"{السعر} ريال", inline=False)
    order_embed.add_field(name="رابط الدفع", value=رابط_الدفع, inline=False)

    try:
        await interaction.user.send(embed=order_embed)
        await interaction.user.send("📢 من فضلك بعد الدفع، قيّم تجربتك باستخدام هذا الرابط: https://example.com/rate")

        # إرسال الطلب إلى روم الطلبات إن وُجد
        order_channel_id = store.get("order_channel")
        if order_channel_id:
            channel = interaction.guild.get_channel(order_channel_id)
            if channel:
                await channel.send(f"🛒 تم طلب **{المنتج}** من قبل {interaction.user.mention}")

        await interaction.response.send_message(embed=Embed(title="✅ تم تنفيذ الطلب", description="تم إرسال الفاتورة في الخاص.", color=0x00ff00), ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ لا يمكنني إرسال رسائل خاصة لك، فعل الرسائل الخاصة أولاً.", ephemeral=True)

# Flask للبقاء على قيد الحياة في Render
app = Flask('')

@app.route('/')
def home():
    return "البوت يعمل ✅"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

import os
TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ لم يتم تحديد التوكن")
