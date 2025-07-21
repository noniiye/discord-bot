import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction
import json
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

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
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# أوامر التاجر ======================

@bot.tree.command(name="انشاء_متجر", description="إنشاء متجر باسم معين")
@app_commands.describe(الاسم="اسم المتجر")
async def انشاء_متجر(interaction: discord.Interaction, الاسم: str):
    guild_id = str(interaction.guild.id)
    data[guild_id] = {"store_name": الاسم, "categories": {}, "trader_channel_id": None, "payment_link": None, "order_channel_id": None}
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم إنشاء المتجر باسم: **{الاسم}**", ephemeral=True)

@bot.tree.command(name="رابط_دفع", description="تحديد رابط الدفع ليظهر في الفاتورة")
@app_commands.describe(الرابط="رابط الدفع")
async def رابط_دفع(interaction: discord.Interaction, الرابط: str):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        await interaction.response.send_message("❌ المتجر غير موجود.", ephemeral=True)
        return
    data[guild_id]["payment_link"] = الرابط
    حفظ_البيانات()
    await interaction.response.send_message("✅ تم حفظ رابط الدفع بنجاح.", ephemeral=True)

@bot.tree.command(name="روم_التاجر", description="تحديد روم استقبال الطلبات")
@app_commands.describe(الروم="روم الطلبات")
async def روم_التاجر(interaction: discord.Interaction, الروم: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        await interaction.response.send_message("❌ المتجر غير موجود.", ephemeral=True)
        return
    data[guild_id]["trader_channel_id"] = الروم.id
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم تعيين روم التاجر إلى: {الروم.mention}", ephemeral=True)

@bot.tree.command(name="روم_الطلبات", description="تحديد الروم الذي يُسمح فيه بتنفيذ أمر /طلب")
@app_commands.describe(الروم="روم الطلبات")
async def روم_الطلبات(interaction: discord.Interaction, الروم: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        await interaction.response.send_message("❌ المتجر غير موجود.", ephemeral=True)
        return
    data[guild_id]["order_channel_id"] = الروم.id
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم تعيين روم الطلبات إلى: {الروم.mention}", ephemeral=True)

@bot.tree.command(name="اضافة_قسم", description="إضافة قسم جديد إلى المتجر")
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

@bot.tree.command(name="اضافة_منتج", description="إضافة منتج إلى قسم معين")
@app_commands.describe(القسم="اسم القسم", الاسم="اسم المنتج", الكمية="الكمية", السعر="سعر المنتج")
async def اضافة_منتج(interaction: discord.Interaction, القسم: str, الاسم: str, الكمية: int, السعر: int):
    guild_id = str(interaction.guild.id)
    if القسم not in data.get(guild_id, {}).get("categories", {}):
        await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)
        return
    data[guild_id]["categories"][القسم][الاسم] = {"الكمية": الكمية, "السعر": السعر}
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم إضافة المنتج: {الاسم} إلى القسم: {القسم}", ephemeral=True)

@bot.tree.command(name="الاقسام", description="عرض أقسام المتجر")
async def الاقسام(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id not in data or not data[guild_id]["categories"]:
        await interaction.response.send_message("❌ لا توجد أقسام حالياً.", ephemeral=True)
        return
    اقسام = list(data[guild_id]["categories"].keys())
    embed = discord.Embed(title="📦 أقسام المتجر", description="\n".join(اقسام), color=0x00ff00)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="عرض", description="عرض منتجات قسم معين")
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

# تقييمView نجوم
class تقييمView(discord.ui.View):
    @discord.ui.button(label="⭐", style=discord.ButtonStyle.secondary)
    async def one_star(self, interaction_button: discord.Interaction, button: discord.ui.Button):
        await handle_rating(interaction_button, 1)

    @discord.ui.button(label="⭐⭐", style=discord.ButtonStyle.secondary)
    async def two_star(self, interaction_button: discord.Interaction, button: discord.ui.Button):
        await handle_rating(interaction_button, 2)

    @discord.ui.button(label="⭐⭐⭐", style=discord.ButtonStyle.secondary)
    async def three_star(self, interaction_button: discord.Interaction, button: discord.ui.Button):
        await handle_rating(interaction_button, 3)

    @discord.ui.button(label="⭐⭐⭐⭐", style=discord.ButtonStyle.secondary)
    async def four_star(self, interaction_button: discord.Interaction, button: discord.ui.Button):
        await handle_rating(interaction_button, 4)

    @discord.ui.button(label="⭐⭐⭐⭐⭐", style=discord.ButtonStyle.secondary)
    async def five_star(self, interaction_button: discord.Interaction, button: discord.ui.Button):
        await handle_rating(interaction_button, 5)

async def handle_rating(interaction_button, rating):
    await interaction_button.response.send_message("✅ شكراً لتقييمك!", ephemeral=True)
    guild_id = str(interaction_button.guild.id)
    user = interaction_button.user
    trader_channel_id = data[guild_id].get("trader_channel_id")
    if trader_channel_id:
        trader_channel = bot.get_channel(trader_channel_id)
        if trader_channel:
            await trader_channel.send(f"📢 تقييم جديد من {user.mention} على طلبه: {'⭐' * rating}")

@bot.tree.command(name="تأكيد_الدفع", description="إرسال إيصال للتاجر بعد الدفع")
@app_commands.describe(محتوى="محتوى الإيصال")
async def تأكيد_الدفع(interaction: discord.Interaction, محتوى: str):
    guild_id = str(interaction.guild.id)
    trader_channel_id = data.get(guild_id, {}).get("trader_channel_id")
    if trader_channel_id:
        trader_channel = bot.get_channel(trader_channel_id)
        if trader_channel:
            await trader_channel.send(f"📥 تم إرسال الإيصال من {interaction.user.mention}:\n{محتوى}")
            await interaction.response.send_message("✅ تم إرسال الإيصال للتاجر بنجاح.\n📌 تأكد من إرسال صورة أو إثبات الدفع للتاجر.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ لم يتم العثور على روم التاجر.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ لم يتم تحديد روم التاجر بعد.", ephemeral=True)

keep_alive()
bot.run(os.getenv("TOKEN"))
