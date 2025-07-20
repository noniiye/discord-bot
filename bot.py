import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

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
        روم_التاجر = بيانات_السيرفر.get("admin_channel")
        if روم_التاجر:
            channel = bot.get_channel(روم_التاجر)
            if channel:
                await channel.send(embed=discord.Embed(
                    title="⭐ تقييم جديد",
                    description=f"**الطلب:** {self.وصف_الطلب}\n**معرّف العميل:** {self.user_id}\n**التقييم:** {rating} ⭐",
                    color=discord.Color.gold()
                ))

@tree.command(name="انشاء_متجر", description="إنشاء متجر جديد باسم مخصص")
@app_commands.describe(اسم_المتجر="اسم المتجر")
async def انشاء_متجر(interaction: discord.Interaction, اسم_المتجر: str):
    servers_data[interaction.guild_id] = {
        "store_name": اسم_المتجر,
        "categories": {},
        "payment_link": None,
        "order_channel": None,
        "admin_channel": None
    }
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم إنشاء المتجر", description=f"اسم المتجر: {اسم_المتجر}", color=discord.Color.green()), ephemeral=True)

@tree.command(name="روم_الطلب", description="تحديد روم الطلبات")
@app_commands.describe(روم="الروم الذي يتم الطلب منه")
async def روم_الطلب(interaction: discord.Interaction, روم: discord.TextChannel):
    بيانات = servers_data.get(interaction.guild_id)
    if not بيانات:
        await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد.", ephemeral=True)
        return
    بيانات["order_channel"] = روم.id
    await interaction.response.send_message(f"✅ تم تحديد روم الطلبات: {روم.mention}", ephemeral=True)

@tree.command(name="روم_التاجر", description="تحديد روم التاجر لاستقبال التقييمات والطلبات")
@app_commands.describe(روم="الروم الخاص بالتاجر")
async def روم_التاجر(interaction: discord.Interaction, روم: discord.TextChannel):
    بيانات = servers_data.get(interaction.guild_id)
    if not بيانات:
        await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد.", ephemeral=True)
        return
    بيانات["admin_channel"] = روم.id
    await interaction.response.send_message(f"✅ تم تحديد روم التاجر: {روم.mention}", ephemeral=True)

@tree.command(name="رابط_دفع", description="تحديد رابط الدفع")
@app_commands.describe(الرابط="الرابط الذي سيتم إرساله للعميل")
async def رابط_دفع(interaction: discord.Interaction, الرابط: str):
    بيانات = servers_data.get(interaction.guild_id)
    if not بيانات:
        await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد.", ephemeral=True)
        return
    بيانات["payment_link"] = الرابط
    await interaction.response.send_message("✅ تم تحديث رابط الدفع.", ephemeral=True)

@tree.command(name="إضافة_قسم", description="إضافة قسم جديد")
@app_commands.describe(اسم_القسم="اسم القسم")
async def إضافة_قسم(interaction: discord.Interaction, اسم_القسم: str):
    بيانات = servers_data.get(interaction.guild_id)
    if not بيانات:
        await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد.", ephemeral=True)
        return
    بيانات["categories"][اسم_القسم] = {}
    await interaction.response.send_message(f"✅ تم إضافة القسم: {اسم_القسم}", ephemeral=True)

@tree.command(name="إضافة_منتج", description="إضافة منتج داخل قسم")
@app_commands.describe(اسم_القسم="القسم", اسم_المنتج="اسم المنتج", الكمية="الكمية", السعر="السعر")
async def إضافة_منتج(interaction: discord.Interaction, اسم_القسم: str, اسم_المنتج: str, الكمية: int, السعر: float):
    بيانات = servers_data.get(interaction.guild_id)
    if not بيانات or اسم_القسم not in بيانات["categories"]:
        await interaction.response.send_message("❌ القسم غير موجود أو لم يتم إنشاء متجر بعد.", ephemeral=True)
        return
    بيانات["categories"][اسم_القسم][اسم_المنتج] = {"الكمية": الكمية, "السعر": السعر}
    await interaction.response.send_message(f"✅ تم إضافة المنتج {اسم_المنتج} إلى القسم {اسم_القسم}", ephemeral=True)

@tree.command(name="حذف_متجر", description="حذف المتجر الحالي")
async def حذف_متجر(interaction: discord.Interaction):
    if interaction.guild_id in servers_data:
        del servers_data[interaction.guild_id]
        await interaction.response.send_message("✅ تم حذف المتجر.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ لا يوجد متجر لحذفه.", ephemeral=True)

@tree.command(name="حذف_قسم", description="حذف قسم من المتجر")
@app_commands.describe(اسم_القسم="اسم القسم الذي تريد حذفه")
async def حذف_قسم(interaction: discord.Interaction, اسم_القسم: str):
    بيانات = servers_data.get(interaction.guild_id)
    if not بيانات or اسم_القسم not in بيانات["categories"]:
        await interaction.response.send_message("❌ لا يوجد هذا القسم أو لم يتم إنشاء متجر بعد.", ephemeral=True)
        return
    del بيانات["categories"][اسم_القسم]
    await interaction.response.send_message(f"✅ تم حذف القسم {اسم_القسم}.", ephemeral=True)

@tree.command(name="حذف_منتج", description="حذف منتج من قسم")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج")
async def حذف_منتج(interaction: discord.Interaction, القسم: str, المنتج: str):
    بيانات = servers_data.get(interaction.guild_id)
    if not بيانات or القسم not in بيانات["categories"]:
        await interaction.response.send_message("❌ القسم غير موجود أو لم يتم إنشاء متجر بعد.", ephemeral=True)
        return
    if المنتج not in بيانات["categories"][القسم]:
        await interaction.response.send_message("❌ المنتج غير موجود في هذا القسم.", ephemeral=True)
        return
    del بيانات["categories"][القسم][المنتج]
    await interaction.response.send_message(f"✅ تم حذف المنتج {المنتج} من القسم {القسم}.", ephemeral=True)

@tree.command(name="حذف_رابط", description="حذف رابط الدفع")
async def حذف_رابط(interaction: discord.Interaction):
    بيانات = servers_data.get(interaction.guild_id)
    if not بيانات:
        await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد.", ephemeral=True)
        return
    بيانات["payment_link"] = None
    await interaction.response.send_message("✅ تم حذف رابط الدفع.", ephemeral=True)

keep_alive()
bot.run(os.getenv("TOKEN"))
