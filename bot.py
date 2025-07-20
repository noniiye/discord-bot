import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive
import os

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

بيانات_المتاجر = {}

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

# إنشاء متجر
@tree.command(name="إنشاء_متجر")
@app_commands.describe(اسم="اسم المتجر")
async def create_store(interaction: discord.Interaction, اسم: str):
    await interaction.response.defer(thinking=True, ephemeral=True)
    بيانات_المتاجر[interaction.guild.id] = {
        "اسم": اسم,
        "الأقسام": {},
        "رابط_الدفع": None,
        "روم_الطلبات": None
    }
    await interaction.followup.send(embed=discord.Embed(title="✅ تم إنشاء المتجر", description=f"اسم المتجر: **{اسم}**", color=0x00ff00), ephemeral=True)

# إضافة قسم
@tree.command(name="إضافة_قسم")
@app_commands.describe(اسم="اسم القسم")
async def add_category(interaction: discord.Interaction, اسم: str):
    await interaction.response.defer(thinking=True, ephemeral=True)
    متجر = بيانات_المتاجر.get(interaction.guild.id)
    if not متجر:
        await interaction.followup.send("❌ لا يوجد متجر.", ephemeral=True)
        return
    متجر["الأقسام"][اسم] = {}
    await interaction.followup.send(embed=discord.Embed(title="✅ تم إضافة القسم", description=اسم, color=0x00ff00), ephemeral=True)

# إضافة منتج
@tree.command(name="إضافة_منتج")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج", الكمية="الكمية", السعر="السعر")
async def add_product(interaction: discord.Interaction, القسم: str, المنتج: str, الكمية: int, السعر: int):
    await interaction.response.defer(thinking=True, ephemeral=True)
    متجر = بيانات_المتاجر.get(interaction.guild.id)
    if not متجر or القسم not in متجر["الأقسام"]:
        await interaction.followup.send("❌ القسم غير موجود.", ephemeral=True)
        return
    متجر["الأقسام"][القسم][المنتج] = {"الكمية": الكمية, "السعر": السعر}
    await interaction.followup.send(embed=discord.Embed(title="✅ تم إضافة المنتج", description=f"{المنتج} - {السعر}$ × {الكمية}", color=0x00ff00), ephemeral=True)

# رابط دفع
@tree.command(name="تحديد_رابط_الدفع")
@app_commands.describe(الرابط="الرابط الكامل")
async def set_payment(interaction: discord.Interaction, الرابط: str):
    await interaction.response.defer(thinking=True, ephemeral=True)
    متجر = بيانات_المتاجر.get(interaction.guild.id)
    if not متجر:
        await interaction.followup.send("❌ لا يوجد متجر.", ephemeral=True)
        return
    متجر["رابط_الدفع"] = الرابط
    await interaction.followup.send(embed=discord.Embed(title="✅ تم تحديد رابط الدفع", description=الرابط, color=0x00ff00), ephemeral=True)

# روم الطلبات
@tree.command(name="تحديد_روم_الطلبات")
@app_commands.describe(الروم: "الروم")
async def set_order_channel(interaction: discord.Interaction, الروم: discord.TextChannel):
    await interaction.response.defer(thinking=True, ephemeral=True)
    متجر = بيانات_المتاجر.get(interaction.guild.id)
    if not متجر:
        await interaction.followup.send("❌ لا يوجد متجر.", ephemeral=True)
        return
    متجر["روم_الطلبات"] = الروم.id
    await interaction.followup.send(embed=discord.Embed(title="✅ تم تحديد روم الطلبات", description=الروم.mention, color=0x00ff00), ephemeral=True)

# حذف متجر
@tree.command(name="حذف_متجر")
async def delete_store(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)
    if interaction.guild.id in بيانات_المتاجر:
        del بيانات_المتاجر[interaction.guild.id]
        await interaction.followup.send("✅ تم حذف المتجر.", ephemeral=True)
    else:
        await interaction.followup.send("❌ لا يوجد متجر.", ephemeral=True)

# حذف قسم
@tree.command(name="حذف_قسم")
@app_commands.describe(القسم="اسم القسم")
async def delete_category(interaction: discord.Interaction, القسم: str):
    await interaction.response.defer(thinking=True, ephemeral=True)
    متجر = بيانات_المتاجر.get(interaction.guild.id)
    if متجر and القسم in متجر["الأقسام"]:
        del متجر["الأقسام"][القسم]
        await interaction.followup.send("✅ تم حذف القسم.", ephemeral=True)
    else:
        await interaction.followup.send("❌ القسم غير موجود.", ephemeral=True)

# حذف منتج
@tree.command(name="حذف_منتج")
@app_commands.describe(القسم="القسم", المنتج="المنتج")
async def delete_product(interaction: discord.Interaction, القسم: str, المنتج: str):
    await interaction.response.defer(thinking=True, ephemeral=True)
    متجر = بيانات_المتاجر.get(interaction.guild.id)
    if متجر and القسم in متجر["الأقسام"] and المنتج in متجر["الأقسام"][القسم]:
        del متجر["الأقسام"][القسم][المنتج]
        await interaction.followup.send("✅ تم حذف المنتج.", ephemeral=True)
    else:
        await interaction.followup.send("❌ المنتج أو القسم غير موجود.", ephemeral=True)

# حذف رابط
@tree.command(name="حذف_رابط")
async def delete_link(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)
    متجر = بيانات_المتاجر.get(interaction.guild.id)
    if متجر:
        متجر["رابط_الدفع"] = None
        await interaction.followup.send("✅ تم حذف رابط الدفع.", ephemeral=True)
    else:
        await interaction.followup.send("❌ لا يوجد متجر.", ephemeral=True)

# أمر الطلب التفاعلي
@tree.command(name="طلب")
async def order(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)
    متجر = بيانات_المتاجر.get(interaction.guild.id)
    if not متجر or not متجر["الأقسام"]:
        await interaction.followup.send("❌ لا يوجد متجر أو لا توجد أقسام.", ephemeral=True)
        return

    async def ask_dropdown(options, placeholder):
        class Dropdown(discord.ui.Select):
            def __init__(self):
                super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=[discord.SelectOption(label=str(opt)) for opt in options[:25]])

            async def callback(self, interaction2: discord.Interaction):
                self.view.value = self.values[0]
                self.view.stop()

        class DropdownView(discord.ui.View):
            def __init__(self):
                super().__init__()
                self.value = None
                self.add_item(Dropdown())

        view = DropdownView()
        await interaction.followup.send("اختر:", view=view, ephemeral=True)
        await view.wait()
        return view.value

    القسم = await ask_dropdown(list(متجر["الأقسام"].keys()), "اختر القسم")
    المنتج = await ask_dropdown(list(متجر["الأقسام"][القسم].keys()), "اختر المنتج")
    المنتج_البيانات = متجر["الأقسام"][القسم][المنتج]
    الكميات = [str(i) for i in range(1, min(26, المنتج_البيانات["الكمية"] + 1))]
    الكمية = await ask_dropdown(الكميات, "اختر الكمية")

    الطلب = f"المنتج: {المنتج}\nالقسم: {القسم}\nالكمية: {الكمية}"
    فاتورة = discord.Embed(title=f"🧾 فاتورة من متجر {متجر['اسم']}", description=الطلب, color=0x3498db)
    if متجر["رابط_الدفع"]:
        فاتورة.add_field(name="💳 رابط الدفع", value=متجر["رابط_الدفع"], inline=False)

    await interaction.user.send(embed=فاتورة)

    # تقييم
    class تقييم(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="⭐", style=discord.ButtonStyle.primary)
        async def star1(self, interaction2, button):
            await interaction2.response.send_message("شكراً لتقييمك ⭐", ephemeral=True)
            await send_review("⭐")

        @discord.ui.button(label="⭐⭐", style=discord.ButtonStyle.primary)
        async def star2(self, interaction2, button):
            await interaction2.response.send_message("شكراً لتقييمك ⭐⭐", ephemeral=True)
            await send_review("⭐⭐")

        @discord.ui.button(label="⭐⭐⭐", style=discord.ButtonStyle.primary)
        async def star3(self, interaction2, button):
            await interaction2.response.send_message("شكراً لتقييمك ⭐⭐⭐", ephemeral=True)
            await send_review("⭐⭐⭐")

    async def send_review(التقييم):
        if متجر["روم_الطلبات"]:
            روم = bot.get_channel(متجر["روم_الطلبات"])
            await روم.send(f"📦 {interaction.user.mention} طلب: {الطلب}\n⭐ التقييم: {التقييم}")

    await interaction.user.send("يرجى تقييم طلبك:", view=تقييم())

keep_alive()
bot.run(os.getenv("TOKEN"))
