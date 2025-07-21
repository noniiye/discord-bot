import discord
from discord.ext import commands
from discord import app_commands, ui
import json
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = app_commands.CommandTree(bot)

# تحميل البيانات من ملف JSON
try:
    with open("data.json", "r") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {}

# حفظ البيانات في ملف JSON
def حفظ_البيانات():
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

# أوامر التاجر ======================

@tree.command(name="انشاء_متجر", description="إنشاء متجر باسم معين")
@app_commands.describe(الاسم="اسم المتجر")
async def انشاء_متجر(interaction: discord.Interaction, الاسم: str):
    guild_id = str(interaction.guild.id)
    data[guild_id] = {"store_name": الاسم, "categories": {}, "trader_channel_id": None, "payment_link": None, "order_channel_id": None}
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم إنشاء المتجر باسم: **{الاسم}**", ephemeral=True)

@tree.command(name="رابط_دفع", description="تحديد رابط الدفع ليظهر في الفاتورة")
@app_commands.describe(الرابط="رابط الدفع")
async def رابط_دفع(interaction: discord.Interaction, الرابط: str):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        await interaction.response.send_message("❌ المتجر غير موجود.", ephemeral=True)
        return
    data[guild_id]["payment_link"] = الرابط
    حفظ_البيانات()
    await interaction.response.send_message("✅ تم حفظ رابط الدفع بنجاح.", ephemeral=True)

@tree.command(name="روم_التاجر", description="تحديد روم استقبال الطلبات")
@app_commands.describe(الروم="روم الطلبات")
async def روم_التاجر(interaction: discord.Interaction, الروم: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        await interaction.response.send_message("❌ المتجر غير موجود.", ephemeral=True)
        return
    data[guild_id]["trader_channel_id"] = الروم.id
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم تعيين روم التاجر إلى: {الروم.mention}", ephemeral=True)

@tree.command(name="روم_الطلبات", description="تحديد الروم الذي يُسمح فيه بتنفيذ أمر /طلب")
@app_commands.describe(الروم="روم الطلبات")
async def روم_الطلبات(interaction: discord.Interaction, الروم: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        await interaction.response.send_message("❌ المتجر غير موجود.", ephemeral=True)
        return
    data[guild_id]["order_channel_id"] = الروم.id
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم تعيين روم الطلبات إلى: {الروم.mention}", ephemeral=True)

# إضافة قسم
@tree.command(name="اضافة_قسم", description="إضافة قسم جديد إلى المتجر")
@app_commands.describe(القسم="اسم القسم")
async def اضافة_قسم(interaction: discord.Interaction, القسم: str):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        await interaction.response.send_message("❌ المتجر غير موجود.", ephemeral=True)
        return
    if القسم in data[guild_id]["categories"]:
        await interaction.response.send_message("⚠️ القسم موجود مسبقًا.", ephemeral=True)
        return
    data[guild_id]["categories"][القسم] = {}
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم إضافة القسم: {القسم}", ephemeral=True)

# إضافة منتج إلى قسم
@tree.command(name="اضافة_منتج", description="إضافة منتج إلى قسم معين")
@app_commands.describe(القسم="اسم القسم", الاسم="اسم المنتج", الكمية="الكمية", السعر="سعر المنتج")
async def اضافة_منتج(interaction: discord.Interaction, القسم: str, الاسم: str, الكمية: int, السعر: int):
    guild_id = str(interaction.guild.id)
    if القسم not in data.get(guild_id, {}).get("categories", {}):
        await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)
        return
    data[guild_id]["categories"][القسم][الاسم] = {"الكمية": الكمية, "السعر": السعر}
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم إضافة المنتج: {الاسم} إلى القسم: {القسم}", ephemeral=True)

# عرض الأقسام
@tree.command(name="الاقسام", description="عرض أقسام المتجر")
async def الاقسام(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id not in data or not data[guild_id]["categories"]:
        await interaction.response.send_message("❌ لا توجد أقسام حالياً.", ephemeral=True)
        return
    اقسام = list(data[guild_id]["categories"].keys())
    embed = discord.Embed(title="📦 أقسام المتجر", description="\n".join(اقسام), color=0x00ff00)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# عرض منتجات قسم
@tree.command(name="عرض", description="عرض منتجات قسم معين")
@app_commands.describe(القسم="اسم القسم")
async def عرض(interaction: discord.Interaction, القسم: str):
    guild_id = str(interaction.guild.id)
    المنتجات = data.get(guild_id, {}).get("categories", {}).get(القسم)
    if not المنتجات:
        await interaction.response.send_message("❌ هذا القسم غير موجود أو لا يحتوي على منتجات.", ephemeral=True)
        return

    embed = discord.Embed(title=f"📋 منتجات قسم: {القسم}", color=0x00ff00)
    for اسم, تفاصيل in المنتجات.items():
        embed.add_field(name=اسم, value=f"الكمية: {تفاصيل['الكمية']}\nالسعر: {تفاصيل['السعر']} ريال", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# طلب (لزبون)
@tree.command(name="طلب", description="تنفيذ طلب")
@app_commands.describe(القسم="القسم", المنتج="المنتج", الكمية="الكمية")
async def طلب(interaction: discord.Interaction, القسم: str, المنتج: str, الكمية: int):
    guild_id = str(interaction.guild.id)
    user = interaction.user

    if guild_id not in data or not data[guild_id].get("categories"):
        await interaction.response.send_message("❌ المتجر غير موجود.", ephemeral=True)
        return

    if القسم not in data[guild_id]["categories"] or المنتج not in data[guild_id]["categories"][القسم]:
        await interaction.response.send_message("❌ القسم أو المنتج غير موجود.", ephemeral=True)
        return

    تفاصيل = data[guild_id]["categories"][القسم][المنتج]
    if الكمية > تفاصيل["الكمية"]:
        await interaction.response.send_message("❌ الكمية المطلوبة غير متوفرة.", ephemeral=True)
        return

    السعر_الاجمالي = تفاصيل["السعر"] * الكمية

    embed = discord.Embed(title="🧾 فاتورة الطلب", color=0x2ecc71)
    embed.add_field(name="🛍️ المتجر", value=data[guild_id]["store_name"], inline=False)
    embed.add_field(name="📁 القسم", value=القسم, inline=True)
    embed.add_field(name="📦 المنتج", value=المنتج, inline=True)
    embed.add_field(name="🔢 الكمية", value=str(الكمية), inline=True)
    embed.add_field(name="💰 السعر الإجمالي", value=f"{السعر_الاجمالي} ريال", inline=True)
    embed.add_field(name="🔗 رابط الدفع", value=data[guild_id].get("payment_link", "❌ لا يوجد"), inline=False)
    embed.set_footer(text="📩 شكراً لطلبك!")

    try:
        await user.send(embed=embed)
    except:
        await interaction.response.send_message("❌ لم أستطع إرسال الفاتورة في الخاص.", ephemeral=True)
        return

    trader_channel_id = data[guild_id].get("trader_channel_id")
    if trader_channel_id:
        trader_channel = bot.get_channel(trader_channel_id)
        if trader_channel:
            await trader_channel.send(f"📥 طلب جديد من {user.mention}\n📦 المنتج: {المنتج}\n📁 القسم: {القسم}\n🔢 الكمية: {الكمية}\n💰 السعر: {السعر_الاجمالي} ريال")

    await interaction.response.send_message("✅ تم إرسال الفاتورة في الخاص.", ephemeral=True)

keep_alive()
bot.run(os.getenv("TOKEN"))
