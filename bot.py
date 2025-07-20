import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
from keep_alive import keep_alive

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# قاعدة بيانات مؤقتة لكل سيرفر
servers_data = {}

class تقييمView(discord.ui.View):
    def __init__(self, وصف_الطلب, user_id):
        super().__init__(timeout=None)
        self.وصف_الطلب = وصف_الطلب
        self.user_id = user_id

    @discord.ui.button(label="⭐", style=discord.ButtonStyle.primary)
    async def نجمة_واحدة(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ارسل_التقييم(interaction, 1)

    @discord.ui.button(label="⭐⭐", style=discord.ButtonStyle.primary)
    async def نجمتين(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ارسل_التقييم(interaction, 2)

    @discord.ui.button(label="⭐⭐⭐", style=discord.ButtonStyle.primary)
    async def ثلاث_نجوم(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ارسل_التقييم(interaction, 3)

    @discord.ui.button(label="⭐⭐⭐⭐", style=discord.ButtonStyle.primary)
    async def اربع_نجوم(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ارسل_التقييم(interaction, 4)

    @discord.ui.button(label="⭐⭐⭐⭐⭐", style=discord.ButtonStyle.primary)
    async def خمس_نجوم(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.ارسل_التقييم(interaction, 5)

    async def ارسل_التقييم(self, interaction, rating):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ لا يمكنك تقييم طلب شخص آخر!", ephemeral=True)
            return

        await interaction.response.send_message("✅ شكرًا لتقييمك!", ephemeral=True)
        بيانات_السيرفر = servers_data.get(interaction.guild_id)
        if not بيانات_السيرفر:
            return
        روم_الطلبات = بيانات_السيرفر.get("order_channel")
        if روم_الطلبات:
            channel = bot.get_channel(Rوم_الطلبات)
            if channel:
                await channel.send(embed=discord.Embed(
                    title="⭐ تقييم جديد",
                    description=f"**الطلب:** {self.وصف_الطلب}\n**معرّف العميل:** {self.user_id}\n**التقييم:** {rating} ⭐",
                    color=discord.Color.gold()
                ))

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ تم تسجيل الدخول باسم {bot.user}")

@tree.command(name="انشاء_متجر", description="إنشاء متجر جديد باسم مخصص")
@app_commands.describe(الاسم="اسم المتجر")
async def انشاء_متجر(interaction: discord.Interaction, الاسم: str):
    servers_data[interaction.guild_id] = {
        "store_name": الاسم,
        "categories": {},
        "payment_link": None,
        "order_channel": None
    }
    await interaction.response.send_message(embed=discord.Embed(
        title="✅ تم إنشاء المتجر",
        description=f"تم إنشاء المتجر باسم **{الاسم}**",
        color=discord.Color.green()
    ))

@tree.command(name="اضافة_قسم", description="إضافة قسم إلى المتجر")
@app_commands.describe(اسم_القسم="اسم القسم الجديد")
async def اضافة_قسم(interaction: discord.Interaction, اسم_القسم: str):
    بيانات = servers_data.get(interaction.guild_id)
    if not بيانات:
        await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد.", ephemeral=True)
        return
    بيانات["categories"][اسم_القسم] = {}
    await interaction.response.send_message(embed=discord.Embed(
        title="✅ تم إضافة القسم",
        description=f"تمت إضافة القسم **{اسم_القسم}**",
        color=discord.Color.green()
    ))

@tree.command(name="اضافة_منتج", description="إضافة منتج إلى قسم معين")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج", الكمية="الكمية المتوفرة", السعر="سعر المنتج")
async def اضافة_منتج(interaction: discord.Interaction, القسم: str, المنتج: str, الكمية: int, السعر: float):
    بيانات = servers_data.get(interaction.guild_id)
    if not بيانات or القسم not in بيانات["categories"]:
        await interaction.response.send_message("❌ القسم غير موجود أو لم يتم إنشاء متجر بعد.", ephemeral=True)
        return
    بيانات["categories"][القسم][المنتج] = {"الكمية": الكمية, "السعر": السعر}
    await interaction.response.send_message(embed=discord.Embed(
        title="✅ تم إضافة المنتج",
        description=f"تمت إضافة **{المنتج}** إلى قسم **{القسم}**",
        color=discord.Color.green()
    ))

@tree.command(name="رابط_دفع", description="تحديد رابط الدفع")
@app_commands.describe(الرابط="رابط الدفع")
async def رابط_دفع(interaction: discord.Interaction, الرابط: str):
    بيانات = servers_data.get(interaction.guild_id)
    if not بيانات:
        await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد.", ephemeral=True)
        return
    بيانات["payment_link"] = الرابط
    await interaction.response.send_message(embed=discord.Embed(
        title="✅ تم تحديد رابط الدفع",
        description=f"[اضغط هنا للدفع]({الرابط})",
        color=discord.Color.green()
    ))

@tree.command(name="تحديد_روم_الطلبات", description="تحديد الروم الذي يستقبل التقييمات")
@app_commands.describe(الروم="اختيار روم الطلبات")
async def تحديد_روم_الطلبات(interaction: discord.Interaction, الروم: discord.TextChannel):
    بيانات = servers_data.get(interaction.guild_id)
    if not بيانات:
        await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد.", ephemeral=True)
        return
    بيانات["order_channel"] = الروم.id
    await interaction.response.send_message(embed=discord.Embed(
        title="✅ تم تحديد روم الطلبات",
        description=f"سيتم إرسال التقييمات إلى: {الروم.mention}",
        color=discord.Color.green()
    ))

# أكمل الباقي: حذف متجر / قسم / منتج، تنفيذ الطلب، إرسال الفاتورة والتقييم...

keep_alive()
bot.run(os.getenv("TOKEN"))
