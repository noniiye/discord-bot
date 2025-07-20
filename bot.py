import discord
from discord.ext import commands, tasks
from discord import app_commands
from keep_alive import keep_alive
import asyncio

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
client = commands.Bot(command_prefix="!", intents=intents)

متاجر = {}

class Dropdown(discord.ui.Select):
    def __init__(self, الخيارات):
        options = [discord.SelectOption(label=label) for label in الخيارات]
        super().__init__(placeholder="اختر", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.value = self.values[0]
        self.view.stop()

class DropdownView(discord.ui.View):
    def __init__(self, الخيارات):
        super().__init__()
        self.value = None
        self.add_item(Dropdown(الخيارات))

async def ask_dropdown(interaction, الخيارات, النص):
    view = DropdownView(الخيارات)
    await interaction.followup.send(النص, view=view, ephemeral=True)
    await view.wait()
    return view.value

@client.event
async def on_ready():
    try:
        synced = await client.tree.sync()
        print(f"✅ تم تشغيل البوت وتمت مزامنة {len(synced)} أمر (slash commands).")
    except Exception as e:
        print(e)

@client.tree.command(name="إنشاء_متجر")
@app_commands.describe(الاسم="اسم المتجر")
async def create_store(interaction: discord.Interaction, الاسم: str):
    await interaction.response.defer(thinking=True, ephemeral=True)
    متاجر[interaction.guild.id] = {"اسم": الاسم, "أقسام": {}, "رابط الدفع": None, "روم الطلبات": None}
    await interaction.followup.send(embed=discord.Embed(title="✅ تم إنشاء المتجر", description=f"اسم المتجر: **{الاسم}**", color=0x00ff00), ephemeral=True)

@client.tree.command(name="إضافة_قسم")
@app_commands.describe(الاسم="اسم القسم")
async def add_category(interaction: discord.Interaction, الاسم: str):
    await interaction.response.defer(thinking=True, ephemeral=True)
    المتجر = متاجر.get(interaction.guild.id)
    if not المتجر:
        await interaction.followup.send(embed=discord.Embed(title="❌ لم يتم إنشاء متجر بعد", color=0xff0000), ephemeral=True)
        return
    المتجر["أقسام"][الاسم] = {}
    await interaction.followup.send(embed=discord.Embed(title="✅ تم إضافة القسم", description=الاسم, color=0x00ff00), ephemeral=True)

@client.tree.command(name="إضافة_منتج")
@app_commands.describe(القسم="اسم القسم", الاسم="اسم المنتج", الكمية="الكمية المتوفرة", السعر="سعر المنتج")
async def add_product(interaction: discord.Interaction, القسم: str, الاسم: str, الكمية: int, السعر: int):
    await interaction.response.defer(thinking=True, ephemeral=True)
    المتجر = متاجر.get(interaction.guild.id)
    if not المتجر or القسم not in المتجر["أقسام"]:
        await interaction.followup.send(embed=discord.Embed(title="❌ القسم غير موجود أو لم يتم إنشاء متجر", color=0xff0000), ephemeral=True)
        return
    المتجر["أقسام"][القسم][الاسم] = {"الكمية": الكمية, "السعر": السعر}
    await interaction.followup.send(embed=discord.Embed(title="✅ تم إضافة المنتج", description=f"{الاسم} - {السعر} ريال (x{الكمية})", color=0x00ff00), ephemeral=True)

@client.tree.command(name="رابط_دفع")
@app_commands.describe(الرابط="رابط الدفع")
async def set_payment(interaction: discord.Interaction, الرابط: str):
    await interaction.response.defer(thinking=True, ephemeral=True)
    if interaction.guild.id in متاجر:
        متاجر[interaction.guild.id]["رابط الدفع"] = الرابط
        await interaction.followup.send(embed=discord.Embed(title="✅ تم تعيين رابط الدفع", description=الرابط, color=0x00ff00), ephemeral=True)
    else:
        await interaction.followup.send(embed=discord.Embed(title="❌ لم يتم إنشاء متجر بعد", color=0xff0000), ephemeral=True)

@client.tree.command(name="تحديد_روم_الطلبات")
@app_commands.describe(channel="الروم الذي سيتم إرسال الطلبات إليه")
async def تحديد_روم_الطلبات(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.defer(thinking=True, ephemeral=True)
    server_id = interaction.guild.id
    if server_id not in متاجر:
        await interaction.followup.send(embed=discord.Embed(title="❌ لم يتم إنشاء متجر بعد", color=0xff0000), ephemeral=True)
        return
    متاجر[server_id]["روم الطلبات"] = channel.id
    await interaction.followup.send(embed=discord.Embed(title="✅ تم تحديد روم الطلبات", description=channel.mention, color=0x00ff00), ephemeral=True)

@client.tree.command(name="طلب")
async def order(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)
    المتجر = متاجر.get(interaction.guild.id)
    if not المتجر:
        await interaction.followup.send(embed=discord.Embed(title="❌ لم يتم إنشاء متجر بعد", color=0xff0000), ephemeral=True)
        return

    الأقسام = list(المتجر["أقسام"].keys())
    if not الأقسام:
        await interaction.followup.send(embed=discord.Embed(title="❌ لا توجد أقسام مضافة", color=0xff0000), ephemeral=True)
        return

    القسم = await ask_dropdown(interaction, الأقسام, "اختر القسم")
    المنتجات = list(المتجر["أقسام"][القسم].keys())
    if not المنتجات:
        await interaction.followup.send(embed=discord.Embed(title="❌ لا توجد منتجات في هذا القسم", color=0xff0000), ephemeral=True)
        return

    المنتج_الاسم = await ask_dropdown(interaction, المنتجات, "اختر المنتج")
    المنتج = المتجر["أقسام"][القسم][المنتج_الاسم]
    الكميات = [str(i) for i in range(1, min(26, المنتج['الكمية'] + 1))]
    الكمية = await ask_dropdown(interaction, الكميات, "اختر الكمية")

    السعر_الإجمالي = int(كمية := int(الكمية)) * المنتج["السعر"]
    الطلب_embed = discord.Embed(title="🛒 طلب جديد", color=0x00ff00)
    الطلب_embed.add_field(name="القسم", value=القسم)
    الطلب_embed.add_field(name="المنتج", value=المنتج_الاسم)
    الطلب_embed.add_field(name="الكمية", value=الكمية)
    الطلب_embed.add_field(name="السعر الإجمالي", value=f"{السعر_الإجمالي} ريال")
    الطلب_embed.set_footer(text=f"ID: {interaction.user.id}")

    روم_الطلبات = المتجر["روم الطلبات"]
    if روم_الطلبات:
        channel = client.get_channel(روم_الطلبات)
        if channel:
            await channel.send(embed=طلب_embed)

    رابط = المتجر.get("رابط الدفع", "لم يتم تحديد رابط")
    فاتورة = discord.Embed(title="📦 فاتورتك", description=f"**{المتجر['اسم']}**\n\nالقسم: {القسم}\nالمنتج: {المنتج_الاسم}\nالكمية: {الكمية}\nالسعر: {السعر_الإجمالي} ريال", color=0x3498db)
    فاتورة.add_field(name="رابط الدفع", value=رابط)
    await interaction.user.send(embed=فاتورة)

    view = discord.ui.View()
    for i in range(1, 6):
        button = discord.ui.Button(label=str(i), style=discord.ButtonStyle.primary)
        async def callback(interaction, rating=i):
            await interaction.response.send_message("✅ شكرًا لتقييمك", ephemeral=True)
            if روم_الطلبات and channel:
                await channel.send(embed=discord.Embed(title="⭐ تقييم جديد", description=f"التقييم: {rating}\nالطلب: {المنتج_الاسم}\nID: {interaction.user.id}", color=0xffff00))
        button.callback = callback
        view.add_item(button)
    await interaction.user.send(content="يرجى تقييم الطلب من 1 إلى 5:", view=view)

@client.tree.command(name="حذف_متجر")
async def delete_store(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)
    if interaction.guild.id in متاجر:
        del متاجر[interaction.guild.id]
        await interaction.followup.send(embed=discord.Embed(title="✅ تم حذف المتجر", color=0xff0000), ephemeral=True)
    else:
        await interaction.followup.send(embed=discord.Embed(title="❌ لا يوجد متجر لحذفه", color=0xff0000), ephemeral=True)

@client.tree.command(name="حذف_قسم")
@app_commands.describe(القسم="اسم القسم")
async def delete_category(interaction: discord.Interaction, القسم: str):
    await interaction.response.defer(thinking=True, ephemeral=True)
    المتجر = متاجر.get(interaction.guild.id)
    if المتجر and القسم in المتجر["أقسام"]:
        del المتجر["أقسام"][القسم]
        await interaction.followup.send(embed=discord.Embed(title="✅ تم حذف القسم", color=0xff0000), ephemeral=True)
    else:
        await interaction.followup.send(embed=discord.Embed(title="❌ القسم غير موجود", color=0xff0000), ephemeral=True)

@client.tree.command(name="حذف_منتج")
@app_commands.describe(القسم="اسم القسم", الاسم="اسم المنتج")
async def delete_product(interaction: discord.Interaction, القسم: str, الاسم: str):
    await interaction.response.defer(thinking=True, ephemeral=True)
    المتجر = متاجر.get(interaction.guild.id)
    if المتجر and القسم in المتجر["أقسام"] and الاسم in المتجر["أقسام"][القسم]:
        del المتجر["أقسام"][القسم][الاسم]
        await interaction.followup.send(embed=discord.Embed(title="✅ تم حذف المنتج", color=0xff0000), ephemeral=True)
    else:
        await interaction.followup.send(embed=discord.Embed(title="❌ المنتج أو القسم غير موجود", color=0xff0000), ephemeral=True)

@client.tree.command(name="حذف_رابط")
async def delete_link(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)
    المتجر = متاجر.get(interaction.guild.id)
    if المتجر:
        المتجر["رابط الدفع"] = None
        await interaction.followup.send(embed=discord.Embed(title="✅ تم حذف رابط الدفع", color=0xff0000), ephemeral=True)
    else:
        await interaction.followup.send(embed=discord.Embed(title="❌ لا يوجد متجر", color=0xff0000), ephemeral=True)

keep_alive()
client.run("YOUR_TOKEN_HERE")
