import os
import discord
from discord.ext import commands
from discord import app_commands, Embed, Interaction
from flask import Flask
import threading

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# بيانات المتاجر (لكل سيرفر متجر مستقل)
stores = {}

# Flask للتشغيل في Render
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

@bot.event
async def on_ready():
    threading.Thread(target=run_flask).start()
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

# أمر إنشاء متجر
@tree.command(name="إنشاء_متجر", description="إنشاء متجر جديد")
@app_commands.describe(الاسم="اسم المتجر")
async def create_store(interaction: Interaction, الاسم: str):
    guild_id = interaction.guild_id
    if guild_id in stores:
        await interaction.response.send_message("⚠️ تم إنشاء المتجر مسبقًا.", ephemeral=True)
    else:
        stores[guild_id] = {
            "store_name": الاسم,
            "sections": {},
            "orders_channel": None,
            "payment_link": ""
        }
        await interaction.response.send_message(f"✅ تم إنشاء المتجر باسم: **{الاسم}**", ephemeral=True)

# أمر إضافة قسم
@tree.command(name="إضافة_قسم", description="إضافة قسم إلى المتجر")
@app_commands.describe(اسم_القسم="اسم القسم")
async def add_section(interaction: Interaction, اسم_القسم: str):
    guild_id = interaction.guild_id
    if guild_id not in stores:
        await interaction.response.send_message("⚠️ يجب أولاً إنشاء المتجر.", ephemeral=True)
        return
    stores[guild_id]["sections"][اسم_القسم] = {}
    await interaction.response.send_message(f"✅ تم إضافة القسم: **{اسم_القسم}**", ephemeral=True)

# أمر إضافة منتج
@tree.command(name="إضافة_منتج", description="إضافة منتج إلى قسم")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج", الكمية="الكمية", السعر="السعر")
async def add_product(interaction: Interaction, القسم: str, المنتج: str, الكمية: int, السعر: float):
    guild_id = interaction.guild_id
    if guild_id not in stores:
        await interaction.response.send_message("⚠️ يجب أولاً إنشاء المتجر.", ephemeral=True)
        return
    if القسم not in stores[guild_id]["sections"]:
        await interaction.response.send_message("⚠️ القسم غير موجود.", ephemeral=True)
        return
    stores[guild_id]["sections"][القسم][المنتج] = {"quantity": الكمية, "price": السعر}
    await interaction.response.send_message(f"✅ تمت إضافة المنتج **{المنتج}** في القسم **{القسم}**", ephemeral=True)

# أمر تحديد رابط الدفع
@tree.command(name="تحديد_رابط_دفع", description="تحديد رابط الدفع الذي يظهر في الفاتورة")
@app_commands.describe(الرابط="رابط الدفع")
async def set_payment_link(interaction: Interaction, الرابط: str):
    guild_id = interaction.guild_id
    if guild_id not in stores:
        await interaction.response.send_message("⚠️ يجب أولاً إنشاء المتجر.", ephemeral=True)
        return
    stores[guild_id]["payment_link"] = الرابط
    await interaction.response.send_message("✅ تم حفظ رابط الدفع بنجاح.", ephemeral=True)

# أمر تحديد روم الطلبات
@tree.command(name="تحديد_روم_الطلبات", description="تحديد روم تُرسل إليه الطلبات")
@app_commands.describe(channel="اختيار الروم")
async def set_order_channel(interaction: Interaction, channel: discord.TextChannel):
    guild_id = interaction.guild_id
    if guild_id not in stores:
        await interaction.response.send_message("⚠️ يجب أولاً إنشاء المتجر.", ephemeral=True)
        return
    stores[guild_id]["orders_channel"] = channel.id
    await interaction.response.send_message(f"✅ تم تعيين روم الطلبات: {channel.mention}", ephemeral=True)

# أمر تقديم الطلب
@tree.command(name="طلب", description="تنفيذ طلب منتج")
@app_commands.describe(القسم="القسم", المنتج="المنتج", الكمية="الكمية")
async def order(interaction: Interaction, القسم: str, المنتج: str, الكمية: int):
    guild_id = interaction.guild_id
    user = interaction.user

    if guild_id not in stores:
        await interaction.response.send_message("⚠️ لا يوجد متجر في هذا السيرفر.", ephemeral=True)
        return

    data = stores[guild_id]
    if القسم not in data["sections"] or المنتج not in data["sections"][القسم]:
        await interaction.response.send_message("⚠️ المنتج غير موجود.", ephemeral=True)
        return

    price = data["sections"][القسم][المنتج]["price"]
    total = price * الكمية
    store_name = data["store_name"]
    order_description = f"**المنتج:** {المنتج}
**الكمية:** {الكمية}
**السعر الكلي:** {total} ريال"
    payment_link = data["payment_link"] or "لا يوجد رابط دفع"

    invoice = Embed(
        title="فاتورتك",
        description=f"""**{store_name}**

{order_description}

رابط الدفع: {payment_link}""",
        color=0x00ff00
    )
    await user.send(embed=invoice)

    if data["orders_channel"]:
        ch = bot.get_channel(data["orders_channel"])
        if ch:
            await ch.send(f"📥 طلب جديد:
{order_description}
ID: {user.id}")

    await interaction.response.send_message("✅ تم إرسال الفاتورة إلى الخاص.", ephemeral=True)

bot.run(os.getenv("TOKEN"))

