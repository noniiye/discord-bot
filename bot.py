
import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed
from flask import Flask
import os, json

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# نظام السيرفر المصغر لتشغيل Render
app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"
def run():
    from threading import Thread
    app.run(host='0.0.0.0', port=8080)
run()

# تحميل البيانات
if not os.path.exists("data.json"):
    with open("data.json", "w") as f:
        json.dump({}, f)

def load_data():
    with open("data.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

@tree.command(name="انشاء_متجر", description="إنشاء متجر جديد للسيرفر")
async def create_store(interaction: Interaction):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data:
        await interaction.response.send_message("❌ المتجر موجود مسبقًا", ephemeral=True)
    else:
        data[gid] = {"name": "متجرك", "sections": {}, "paylink": "", "order_channel": None}
        save_data(data)
        await interaction.response.send_message("✅ تم إنشاء المتجر بنجاح", ephemeral=True)

@tree.command(name="اضافة_قسم", description="أضف قسم داخل المتجر")
@app_commands.describe(name="اسم القسم")
async def add_section(interaction: Interaction, name: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد", ephemeral=True)
        return
    data[gid]["sections"][name] = {}
    save_data(data)
    await interaction.response.send_message(f"✅ تم إضافة القسم `{name}`", ephemeral=True)

@tree.command(name="اضافة_منتج", description="أضف منتج داخل قسم")
@app_commands.describe(section="القسم", product="اسم المنتج", details="تفاصيل المنتج")
async def add_product(interaction: Interaction, section: str, product: str, details: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data or section not in data[gid]["sections"]:
        await interaction.response.send_message("❌ القسم غير موجود", ephemeral=True)
        return
    data[gid]["sections"][section][product] = details
    save_data(data)
    await interaction.response.send_message(f"✅ تم إضافة المنتج `{product}` في القسم `{section}`", ephemeral=True)

@tree.command(name="تحديد_روم_الطلبات", description="حدد روم لاستقبال الطلبات")
@app_commands.describe(channel="الروم")
async def set_order_channel(interaction: Interaction, channel: discord.TextChannel):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد", ephemeral=True)
        return
    data[gid]["order_channel"] = channel.id
    save_data(data)
    await interaction.response.send_message(f"✅ تم تحديد روم الطلبات: {channel.mention}", ephemeral=True)

@tree.command(name="طلب", description="طلب منتج من المتجر")
@app_commands.describe(section="القسم", product="المنتج")
async def order_product(interaction: Interaction, section: str, product: str):
    data = load_data()
    gid = str(interaction.guild_id)
    uid = str(interaction.user.id)
    if gid not in data or section not in data[gid]["sections"] or product not in data[gid]["sections"][section]:
        await interaction.response.send_message("❌ المنتج أو القسم غير موجود", ephemeral=True)
        return
    order_channel_id = data[gid].get("order_channel")
    if not order_channel_id:
        await interaction.response.send_message("❌ لم يتم تحديد روم الطلبات", ephemeral=True)
        return
    order_channel = bot.get_channel(order_channel_id)
    embed = Embed(title="طلب جديد", description=f"**من:** {interaction.user.mention}
**القسم:** {section}
**المنتج:** {product}", color=0x00ff00)
    await order_channel.send(embed=embed)
    await interaction.response.send_message("✅ تم تنفيذ الطلب! سيتم التواصل معك قريبًا.", ephemeral=True)

    # إرسال الفاتورة ورابط التقييم
    paylink = data[gid].get("paylink", "لا يوجد")
    try:
        embed_invoice = Embed(title="فاتورة الطلب", description=f"**المنتج:** {product}
**رابط الدفع:** {paylink}", color=0xffcc00)
        await interaction.user.send(embed=embed_invoice)
        embed_rate = Embed(title="تقييم الطلب", description="ما رأيك بالخدمة؟ 🌟", color=0x00ffff)
        await interaction.user.send(embed=embed_rate)
    except:
        pass

@tree.command(name="تحديد_رابط_الدفع", description="ضع رابط الدفع الذي يظهر في الفاتورة")
@app_commands.describe(link="رابط الدفع")
async def set_pay_link(interaction: Interaction, link: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد", ephemeral=True)
        return
    data[gid]["paylink"] = link
    save_data(data)
    await interaction.response.send_message("✅ تم تحديث رابط الدفع بنجاح", ephemeral=True)

bot.run(os.getenv("TOKEN"))
