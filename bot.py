import discord
from discord.ext import commands
from discord import app_commands, Embed
import json
import os
from flask import Flask
import threading

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = app_commands.CommandTree(bot)

DATA_FILE = "store_data.json"

# --- نظام Flask للإبقاء على البوت شغال في Render ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

t = threading.Thread(target=run)
t.start()

# --- تحميل / حفظ البيانات ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# --- تنفيذ الأوامر ---
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

# --- أمر إنشاء متجر ---
@tree.command(name="انشاء_متجر", description="إنشاء متجر لهذا السيرفر")
async def create_store(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    if gid in data:
        await interaction.response.send_message(embed=Embed(description="🔸 المتجر موجود مسبقًا.", color=0x3498db))
    else:
        data[gid] = {"name": "متجري", "sections": {}, "payment_link": "", "order_channel": None}
        save_data(data)
        await interaction.response.send_message(embed=Embed(description="✅ تم إنشاء المتجر بنجاح!", color=0x2ecc71))

# --- أمر إضافة قسم ---
@tree.command(name="اضافة_قسم", description="إضافة قسم جديد للمتجر")
@app_commands.describe(name="اسم القسم")
async def add_section(interaction: discord.Interaction, name: str):
    gid = str(interaction.guild.id)
    if gid not in data:
        await interaction.response.send_message(embed=Embed(description="❌ لم يتم إنشاء متجر بعد.", color=0xe74c3c))
        return
    if name in data[gid]["sections"]:
        await interaction.response.send_message(embed=Embed(description="🔸 القسم موجود مسبقًا.", color=0xf1c40f))
        return
    data[gid]["sections"][name] = {}
    save_data(data)
    await interaction.response.send_message(embed=Embed(description=f"✅ تم إضافة القسم `{name}`.", color=0x2ecc71))

# --- أمر إضافة منتج ---
@tree.command(name="اضافة_منتج", description="إضافة منتج داخل قسم")
@app_commands.describe(section="اسم القسم", name="اسم المنتج", السعر="سعر المنتج")
async def add_product(interaction: discord.Interaction, section: str, name: str, السعر: str):
    gid = str(interaction.guild.id)
    if gid not in data or section not in data[gid]["sections"]:
        await interaction.response.send_message(embed=Embed(description="❌ القسم غير موجود.", color=0xe74c3c))
        return
    data[gid]["sections"][section][name] = السعر
    save_data(data)
    await interaction.response.send_message(embed=Embed(description=f"✅ تم إضافة المنتج `{name}` بسعر `{السعر}` إلى القسم `{section}`.", color=0x2ecc71))

# --- أمر تنفيذ طلب ---
@tree.command(name="طلب", description="طلب منتج معين")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج")
async def order(interaction: discord.Interaction, القسم: str, المنتج: str):
    gid = str(interaction.guild.id)
    user = interaction.user
    if gid not in data or القسم not in data[gid]["sections"] or المنتج not in data[gid]["sections"][القسم]:
        await interaction.response.send_message(embed=Embed(description="❌ القسم أو المنتج غير موجود.", color=0xe74c3c), ephemeral=True)
        return

    السعر = data[gid]["sections"][القسم][المنتج]
    رابط_الدفع = data[gid].get("payment_link", "لا يوجد")
    order_embed = Embed(title="🧾 فاتورة الطلب", color=0x1abc9c)
    order_embed.add_field(name="المنتج", value=المنتج, inline=True)
    order_embed.add_field(name="القسم", value=القسم, inline=True)
    order_embed.add_field(name="السعر", value=السعر, inline=True)
    order_embed.add_field(name="رابط الدفع", value=رابط_الدفع, inline=False)
    await user.send(embed=order_embed)

    تقييم = Embed(title="⭐ تقييم الطلب", description="كيف تقيم تجربتك؟ من 1 إلى 5 نجوم.", color=0xf1c40f)
    await user.send(embed=تقييم)

    # إرسال في روم الطلبات
    channel_id = data[gid].get("order_channel")
    if channel_id:
        channel = bot.get_channel(int(channel_id))
        if channel:
            await channel.send(embed=Embed(description=f"📦 طلب جديد من {user.mention} على المنتج `{المنتج}`.", color=0x95a5a6))

    await interaction.response.send_message(embed=Embed(description="✅ تم إرسال الفاتورة والتقييم في الخاص.", color=0x2ecc71), ephemeral=True)

# --- أمر تغيير رابط الدفع ---
@tree.command(name="رابط_الدفع", description="تحديد رابط الدفع للفواتير")
@app_commands.describe(link="الرابط")
async def set_payment_link(interaction: discord.Interaction, link: str):
    gid = str(interaction.guild.id)
    if gid not in data:
        await interaction.response.send_message(embed=Embed(description="❌ لا يوجد متجر بعد.", color=0xe74c3c))
        return
    data[gid]["payment_link"] = link
    save_data(data)
    await interaction.response.send_message(embed=Embed(description="✅ تم تحديث رابط الدفع للفواتير.", color=0x2ecc71))

# --- أمر تحديد روم الطلبات ---
@tree.command(name="تحديد_روم_الطلبات", description="اختيار روم تصل عليه الطلبات")
@app_commands.describe(channel="الروم")
async def set_order_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    gid = str(interaction.guild.id)
    if gid not in data:
        await interaction.response.send_message(embed=Embed(description="❌ لا يوجد متجر بعد.", color=0xe74c3c))
        return
    data[gid]["order_channel"] = str(channel.id)
    save_data(data)
    await interaction.response.send_message(embed=Embed(description=f"✅ تم تحديد روم الطلبات: {channel.mention}", color=0x2ecc71))

# --- أمر حذف متجر ---
@tree.command(name="حذف_متجر", description="حذف المتجر من السيرفر")
async def delete_store(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    if gid in data:
        del data[gid]
        save_data(data)
        await interaction.response.send_message(embed=Embed(description="🗑️ تم حذف المتجر بنجاح.", color=0xe74c3c))
    else:
        await interaction.response.send_message(embed=Embed(description="❌ لا يوجد متجر لحذفه.", color=0xe74c3c))

import os
bot.run(os.getenv("TOKEN"))
