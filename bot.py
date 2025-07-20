import discord
from discord.ext import commands
from discord import app_commands, Embed, Intents
import asyncio
import os
from flask import Flask
from threading import Thread

intents = Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# المتاجر لكل سيرفر
المتاجر = {}

@tree.command(name="إنشاء_متجر", description="إنشاء متجر باسم مخصص")
@app_commands.describe(الاسم="اسم المتجر")
async def إنشاء_متجر(interaction: discord.Interaction, الاسم: str):
    المتاجر[interaction.guild.id] = {
        "اسم": الاسم,
        "الأقسام": {},
        "رابط_الدفع": "",
        "روم_الطلبات": None
    }
    await interaction.response.send_message(embed=Embed(
        title="تم إنشاء المتجر",
        description=f"✅ تم إنشاء المتجر باسم: **{الاسم}**"
    ), ephemeral=True)

@tree.command(name="إضافة_قسم", description="أضف قسم للمتجر")
@app_commands.describe(القسم="اسم القسم")
async def إضافة_قسم(interaction: discord.Interaction, القسم: str):
    store = المتاجر.get(interaction.guild.id)
    if not store:
        return await interaction.response.send_message("❌ لا يوجد متجر. أنشئ متجر أولاً.", ephemeral=True)
    store["الأقسام"][القسم] = []
    await interaction.response.send_message(embed=Embed(title="✅ تم إضافة القسم", description=f"📂 القسم: **{القسم}**"), ephemeral=True)

@tree.command(name="إضافة_منتج", description="أضف منتج لقسم معين")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج", الكمية="كمية المنتج", السعر="سعر المنتج")
async def إضافة_منتج(interaction: discord.Interaction, القسم: str, المنتج: str, الكمية: int, السعر: float):
    store = المتاجر.get(interaction.guild.id)
    if not store or القسم not in store["الأقسام"]:
        return await interaction.response.send_message("❌ تأكد من وجود المتجر والقسم", ephemeral=True)
    store["الأقسام"][القسم].append({"اسم": المنتج, "الكمية": الكمية, "السعر": السعر})
    await interaction.response.send_message(embed=Embed(title="✅ تمت إضافة المنتج", description=f"📦 {المنتج} - {السعر} ريال - الكمية: {الكمية}"), ephemeral=True)

@tree.command(name="تحديد_رابط_الدفع", description="حدد رابط الدفع للمتجر")
@app_commands.describe(الرابط="رابط الدفع")
async def تحديد_رابط_الدفع(interaction: discord.Interaction, الرابط: str):
    store = المتاجر.get(interaction.guild.id)
    if not store:
        return await interaction.response.send_message("❌ لا يوجد متجر", ephemeral=True)
    store["رابط_الدفع"] = الرابط
    await interaction.response.send_message(embed=Embed(title="✅ تم تحديد رابط الدفع", description=r"🔗 الرابط محفوظ"), ephemeral=True)

@tree.command(name="تحديد_روم_الطلبات", description="حدد روم الطلبات")
@app_commands.describe(channel="الروم")
async def تحديد_روم_الطلبات(interaction: discord.Interaction, channel: discord.TextChannel):
    store = المتاجر.get(interaction.guild.id)
    if not store:
        return await interaction.response.send_message("❌ لا يوجد متجر", ephemeral=True)
    store["روم_الطلبات"] = channel.id
    await interaction.response.send_message(embed=Embed(title="✅ تم تحديد روم الطلبات", description=f"📥 الطلبات ستصل إلى: {channel.mention}"), ephemeral=True)

@tree.command(name="طلب", description="طلب منتج من المتجر")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج", الكمية="كمية الطلب")
async def طلب(interaction: discord.Interaction, القسم: str, المنتج: str, الكمية: int):
    store = المتاجر.get(interaction.guild.id)
    if not store or القسم not in store["الأقسام"]:
        return await interaction.response.send_message("❌ القسم غير موجود", ephemeral=True)

    المنتجات = store["الأقسام"][القسم]
    المنتج_المطلوب = next((p for p in المنتجات if p["اسم"] == المنتج), None)
    if not المنتج_المطلوب:
        return await interaction.response.send_message("❌ المنتج غير موجود", ephemeral=True)

    if المنتج_المطلوب["الكمية"] < الكمية:
        return await interaction.response.send_message("❌ الكمية غير متوفرة", ephemeral=True)

    المنتج_المطلوب["الكمية"] -= الكمية
    وصف_الطلب = f"**القسم:** {القسم}
**المنتج:** {المنتج}
**الكمية:** {الكمية}"

    # إرسال الطلب إلى روم الطلبات
    if store["روم_الطلبات"]:
        ch = interaction.guild.get_channel(store["روم_الطلبات"])
        if ch:
            await ch.send(f"📥 طلب جديد:
{وصف_الطلب}
**العميل:** {interaction.user.mention}")

    # إرسال الفاتورة
    رابط_الدفع = store["رابط_الدفع"]
    المتجر_الاسم = store["اسم"]
    فاتورة = Embed(title="فاتورتك", description=f"**{المتجر_الاسم}**

{وصف_الطلب}

💰 [رابط الدفع]({رابط_الدفع})")
    await interaction.user.send(embed=فاتورة)

    # إرسال التقييم
    view = discord.ui.View()
    for i in range(1, 6):
        view.add_item(discord.ui.Button(label=str(i), style=discord.ButtonStyle.primary, custom_id=f"rate_{i}"))
    await interaction.user.send("📊 قيّم تجربتك:", view=view)
    await interaction.response.send_message("✅ تم إرسال الفاتورة في الخاص.", ephemeral=True)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component and interaction.data.get("custom_id", "").startswith("rate_"):
        rating = interaction.data["custom_id"].split("_")[1]
        await interaction.response.send_message("✅ شكرًا لتقييمك!", ephemeral=True)

        for g in bot.guilds:
            store = المتاجر.get(g.id)
            if store and store["روم_الطلبات"]:
                ch = g.get_channel(store["روم_الطلبات"])
                if ch:
                    await ch.send(f"⭐ تقييم جديد من {interaction.user.mention}: {rating}/5")

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

keep_alive()
bot.run(os.getenv("TOKEN"))
