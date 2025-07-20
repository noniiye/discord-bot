import discord
from discord.ext import commands
from discord import app_commands, ui
import asyncio, threading
from flask import Flask

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
servers_data = {}

# === واجهة الويب لإبقاء البوت نشط (لـ Render) ===
app = Flask('')
@app.route('/')
def home(): return "Bot is running"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): threading.Thread(target=run).start()

# === أوامر المتجر ===

@tree.command(name="انشاء_متجر", description="إنشاء متجر باسم مخصص")
@app_commands.describe(الاسم="اسم المتجر")
async def انشاء_متجر(interaction: discord.Interaction, الاسم: str):
    servers_data[interaction.guild_id] = {
        "store_name": الاسم,
        "categories": {},
        "payment_link": None,
        "orders_channel": None
    }
    await interaction.response.send_message(embed=discord.Embed(
        title="✅ تم إنشاء المتجر",
        description=f"اسم المتجر: {الاسم}",
        color=discord.Color.green()
    ))

@tree.command(name="تحديد_روم_الطلبات", description="تحديد الروم الذي تُرسل إليه الطلبات")
@app_commands.describe(الروم="اختر روم الطلبات")
async def تحديد_روم_الطلبات(interaction: discord.Interaction, الروم: discord.TextChannel):
    if interaction.guild_id in servers_data:
        servers_data[interaction.guild_id]["orders_channel"] = الروم.id
        await interaction.response.send_message(embed=discord.Embed(
            title="📥 تم تحديد روم الطلبات",
            description=f"الروم: {الروم.mention}",
            color=discord.Color.green()
        ))
    else:
        await interaction.response.send_message("❌ يجب أولاً إنشاء متجر باستخدام /انشاء_متجر", ephemeral=True)

@tree.command(name="تحديد_رابط_الدفع", description="تحديد رابط الدفع")
@app_commands.describe(الرابط="رابط الدفع")
async def تحديد_رابط_الدفع(interaction: discord.Interaction, الرابط: str):
    if interaction.guild_id in servers_data:
        servers_data[interaction.guild_id]["payment_link"] = الرابط
        await interaction.response.send_message(embed=discord.Embed(
            title="💳 تم حفظ رابط الدفع",
            description=رابط,
            color=discord.Color.green()
        ))
    else:
        await interaction.response.send_message("❌ يجب أولاً إنشاء متجر.", ephemeral=True)

@tree.command(name="اضافة_قسم", description="إضافة قسم جديد")
@app_commands.describe(الاسم="اسم القسم")
async def اضافة_قسم(interaction: discord.Interaction, الاسم: str):
    data = servers_data.get(interaction.guild_id)
    if data:
        data["categories"][الاسم] = {}
        await interaction.response.send_message(embed=discord.Embed(
            title="📂 تم إضافة القسم",
            description=الاسم,
            color=discord.Color.green()
        ))
    else:
        await interaction.response.send_message("❌ يجب أولاً إنشاء متجر.", ephemeral=True)

@tree.command(name="اضافة_منتج", description="إضافة منتج داخل قسم")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج", الكمية="الكمية", السعر="السعر")
async def اضافة_منتج(interaction: discord.Interaction, القسم: str, المنتج: str, الكمية: int, السعر: int):
    data = servers_data.get(interaction.guild_id)
    if not data or القسم not in data["categories"]:
        await interaction.response.send_message("❌ تأكد من وجود المتجر والقسم.", ephemeral=True)
        return
    data["categories"][القسم][المنتج] = {"quantity": الكمية, "price": السعر}
    await interaction.response.send_message(embed=discord.Embed(
        title="📦 تم إضافة المنتج",
        description=f"{المنتج}\nالكمية: {الكمية}\nالسعر: {السعر} ريال",
        color=discord.Color.green()
    ))

@tree.command(name="حذف_متجر", description="حذف المتجر بالكامل")
async def حذف_متجر(interaction: discord.Interaction):
    servers_data.pop(interaction.guild_id, None)
    await interaction.response.send_message("🗑️ تم حذف المتجر.")

@tree.command(name="حذف_قسم", description="حذف قسم")
@app_commands.describe(القسم="اسم القسم")
async def حذف_قسم(interaction: discord.Interaction, القسم: str):
    data = servers_data.get(interaction.guild_id)
    if data and القسم in data["categories"]:
        del data["categories"][القسم]
        await interaction.response.send_message(f"🗑️ تم حذف القسم {القسم}.")
    else:
        await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)

@tree.command(name="حذف_منتج", description="حذف منتج")
@app_commands.describe(القسم="القسم", المنتج="المنتج")
async def حذف_منتج(interaction: discord.Interaction, القسم: str, المنتج: str):
    data = servers_data.get(interaction.guild_id)
    if data and القسم in data["categories"] and المنتج in data["categories"][القسم]:
        del data["categories"][القسم][المنتج]
        await interaction.response.send_message(f"🗑️ تم حذف المنتج {المنتج}.")
    else:
        await interaction.response.send_message("❌ تحقق من القسم والمنتج.", ephemeral=True)

@tree.command(name="حذف_رابط_الدفع", description="حذف رابط الدفع")
async def حذف_رابط_الدفع(interaction: discord.Interaction):
    data = servers_data.get(interaction.guild_id)
    if data:
        data["payment_link"] = None
        await interaction.response.send_message("✅ تم حذف رابط الدفع.")
    else:
        await interaction.response.send_message("❌ لم يتم العثور على متجر.", ephemeral=True)

# === الطلب والتقييم سيُضاف في القسم التالي ===

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ تسجيل الدخول باسم: {bot.user}")

keep_alive()
bot.run("توكن_البوت_هنا")
