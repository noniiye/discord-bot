import discord
from discord.ext import commands
from discord import app_commands, Embed
import json, os
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

data_file = "store_data.json"

# === حفظ وتحميل البيانات ===
def load_data():
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)

store_data = load_data()

# === Flask للحفاظ على تشغيل البوت على Render ===
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run).start()

# === أحداث البوت ===
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

# === إنشاء متجر ===
@tree.command(name="انشاء_متجر", description="إنشاء متجر جديد لهذا السيرفر")
async def create_store(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id in store_data:
        await interaction.response.send_message("🔸 المتجر موجود بالفعل!", ephemeral=True)
        return
    store_data[guild_id] = {"sections": {}, "orders_channel": None, "payment_link": None}
    save_data(store_data)
    await interaction.response.send_message("✅ تم إنشاء المتجر بنجاح!", ephemeral=True)

# === إضافة قسم ===
@tree.command(name="اضافة_قسم", description="إضافة قسم جديد للمتجر")
@app_commands.describe(name="اسم القسم")
async def add_section(interaction: discord.Interaction, name: str):
    guild_id = str(interaction.guild.id)
    if guild_id not in store_data:
        await interaction.response.send_message("❌ يجب إنشاء المتجر أولاً باستخدام /انشاء_متجر", ephemeral=True)
        return
    store_data[guild_id]["sections"][name] = {}
    save_data(store_data)
    await interaction.response.send_message(f"✅ تم إضافة القسم **{name}**", ephemeral=True)

# === إضافة منتج ===
@tree.command(name="اضافة_منتج", description="إضافة منتج داخل قسم")
@app_commands.describe(section="اسم القسم", product="اسم المنتج", price="سعر المنتج")
async def add_product(interaction: discord.Interaction, section: str, product: str, price: int):
    guild_id = str(interaction.guild.id)
    if guild_id not in store_data or section not in store_data[guild_id]["sections"]:
        await interaction.response.send_message("❌ القسم غير موجود", ephemeral=True)
        return
    store_data[guild_id]["sections"][section][product] = price
    save_data(store_data)
    await interaction.response.send_message(f"✅ تم إضافة المنتج **{product}** بسعر {price}$ في القسم **{section}**", ephemeral=True)

# === تنفيذ الطلب ===
@tree.command(name="طلب", description="طلب منتج من المتجر")
@app_commands.describe(section="اسم القسم", product="اسم المنتج")
async def order(interaction: discord.Interaction, section: str, product: str):
    guild_id = str(interaction.guild.id)
    user = interaction.user
    if guild_id not in store_data or section not in store_data[guild_id]["sections"]:
        await interaction.response.send_message("❌ القسم غير موجود", ephemeral=True)
        return
    if product not in store_data[guild_id]["sections"][section]:
        await interaction.response.send_message("❌ المنتج غير موجود", ephemeral=True)
        return

    price = store_data[guild_id]["sections"][section][product]
    payment_link = store_data[guild_id].get("payment_link", "لا يوجد")
    embed = Embed(title="📦 فاتورة طلب", description=f"**{user.name}** طلب منتج **{product}** من قسم **{section}**", color=0x00ff00)
    embed.add_field(name="السعر", value=f"{price}$", inline=False)
    embed.add_field(name="رابط الدفع", value=payment_link, inline=False)
    try:
        await user.send(embed=embed)
    except:
        pass

    channel_id = store_data[guild_id].get("orders_channel")
    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)
    await interaction.response.send_message("✅ تم تنفيذ الطلب! تم إرسال الفاتورة في الخاص.", ephemeral=True)

    # تقييم
    try:
        rate_embed = Embed(title="🌟 تقييم الطلب", description="هل أعجبك الطلب؟ رد بـ تقييمك من 1 إلى 5.", color=0xffff00)
        await user.send(embed=rate_embed)
    except:
        pass

# === تحديد روم الطلبات ===
@tree.command(name="تحديد_روم_الطلبات", description="تحديد الروم الذي تصل عليه الطلبات")
@app_commands.describe(channel="الروم المطلوب")
async def set_order_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    if guild_id not in store_data:
        await interaction.response.send_message("❌ يجب إنشاء المتجر أولاً.", ephemeral=True)
        return
    store_data[guild_id]["orders_channel"] = channel.id
    save_data(store_data)
    await interaction.response.send_message(f"✅ تم تحديد روم الطلبات: {channel.mention}", ephemeral=True)

# === تحديد رابط الدفع ===
@tree.command(name="تحديد_رابط_الدفع", description="تحديد رابط الدفع الذي يظهر في الفاتورة")
@app_commands.describe(link="رابط الدفع")
async def set_payment_link(interaction: discord.Interaction, link: str):
    guild_id = str(interaction.guild.id)
    if guild_id not in store_data:
        await interaction.response.send_message("❌ يجب إنشاء المتجر أولاً.", ephemeral=True)
        return
    store_data[guild_id]["payment_link"] = link
    save_data(store_data)
    await interaction.response.send_message(f"✅ تم تعيين رابط الدفع للمتجر!", ephemeral=True)

bot.run(os.getenv("TOKEN"))
