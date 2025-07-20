import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# قاعدة بيانات مؤقتة لكل سيرفر
servers_data = {}

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ تم تشغيل البوت - {bot.user}")

# إنشاء متجر
@tree.command(name="إنشاء_متجر")
@app_commands.describe(الاسم="اسم المتجر")
async def create_store(interaction: Interaction, الاسم: str):
    guild_id = interaction.guild_id
    if guild_id not in servers_data:
        servers_data[guild_id] = {"store_name": الاسم, "categories": {}, "payment_link": None, "orders_channel": None}
        await interaction.response.send_message(embed=Embed(title="✅ تم إنشاء المتجر", description=f"اسم المتجر: **{الاسم}**", color=0x00ff00), ephemeral=True)
    else:
        await interaction.response.send_message(embed=Embed(title="⚠️ المتجر موجود مسبقًا", color=0xff0000), ephemeral=True)

# إضافة قسم
@tree.command(name="إضافة_قسم")
@app_commands.describe(الاسم="اسم القسم")
async def add_category(interaction: Interaction, الاسم: str):
    guild_id = interaction.guild_id
    if guild_id in servers_data:
        servers_data[guild_id]["categories"][الاسم] = {}
        await interaction.response.send_message(embed=Embed(title="✅ تم إضافة القسم", description=الاسم, color=0x00ff00), ephemeral=True)
    else:
        await interaction.response.send_message(embed=Embed(title="❌ يجب إنشاء متجر أولاً", color=0xff0000), ephemeral=True)

# إضافة منتج
@tree.command(name="إضافة_منتج")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج", الكمية="الكمية", السعر="السعر")
async def add_product(interaction: Interaction, القسم: str, المنتج: str, الكمية: int, السعر: int):
    guild_id = interaction.guild_id
    data = servers_data.get(guild_id)
    if data and القسم in data["categories"]:
        data["categories"][القسم][المنتج] = {"quantity": الكمية, "price": السعر}
        await interaction.response.send_message(embed=Embed(title="✅ تم إضافة المنتج", description=f"{المنتج} | {الكمية} قطعة | {السعر} ريال", color=0x00ff00), ephemeral=True)
    else:
        await interaction.response.send_message(embed=Embed(title="❌ القسم غير موجود", color=0xff0000), ephemeral=True)

# تحديد رابط دفع
@tree.command(name="تحديد_رابط_الدفع")
@app_commands.describe(الرابط="رابط الدفع")
async def set_payment(interaction: Interaction, الرابط: str):
    guild_id = interaction.guild_id
    if guild_id in servers_data:
        servers_data[guild_id]["payment_link"] = الرابط
        await interaction.response.send_message(embed=Embed(title="✅ تم حفظ رابط الدفع", description=الرابط, color=0x00ff00), ephemeral=True)
    else:
        await interaction.response.send_message(embed=Embed(title="❌ يجب إنشاء متجر أولاً", color=0xff0000), ephemeral=True)

# تحديد روم الطلبات
@tree.command(name="تحديد_روم_الطلبات")
@app_commands.describe(الروم="الروم")
async def set_order_channel(interaction: Interaction, الروم: discord.TextChannel):
    guild_id = interaction.guild_id
    if guild_id in servers_data:
        servers_data[guild_id]["orders_channel"] = الروم.id
        await interaction.response.send_message(embed=Embed(title="✅ تم تحديد روم الطلبات", description=الروم.mention, color=0x00ff00), ephemeral=True)
    else:
        await interaction.response.send_message(embed=Embed(title="❌ يجب إنشاء متجر أولاً", color=0xff0000), ephemeral=True)

# حذف متجر / قسم / منتج / رابط
@tree.command(name="حذف")
@app_commands.describe(نوع="نوع الحذف", الاسم="اسم القسم أو المنتج")
async def delete_item(interaction: Interaction, نوع: str, الاسم: str):
    guild_id = interaction.guild_id
    data = servers_data.get(guild_id)
    if not data:
        await interaction.response.send_message(embed=Embed(title="❌ لا يوجد متجر", color=0xff0000), ephemeral=True)
        return

    if نوع == "متجر":
        servers_data.pop(guild_id)
        await interaction.response.send_message(embed=Embed(title="🗑️ تم حذف المتجر بالكامل", color=0xff0000), ephemeral=True)
    elif نوع == "قسم":
        if الاسم in data["categories"]:
            data["categories"].pop(الاسم)
            await interaction.response.send_message(embed=Embed(title="🗑️ تم حذف القسم", description=الاسم, color=0xff0000), ephemeral=True)
        else:
            await interaction.response.send_message(embed=Embed(title="❌ القسم غير موجود", color=0xff0000), ephemeral=True)
    elif نوع == "منتج":
        for قسم, المنتجات in data["categories"].items():
            if الاسم in المنتجات:
                المنتجات.pop(الاسم)
                await interaction.response.send_message(embed=Embed(title="🗑️ تم حذف المنتج", description=الاسم, color=0xff0000), ephemeral=True)
                return
        await interaction.response.send_message(embed=Embed(title="❌ المنتج غير موجود", color=0xff0000), ephemeral=True)
    elif نوع == "رابط":
        data["payment_link"] = None
        await interaction.response.send_message(embed=Embed(title="🗑️ تم حذف رابط الدفع", color=0xff0000), ephemeral=True)
    else:
        await interaction.response.send_message(embed=Embed(title="❌ نوع غير معروف", color=0xff0000), ephemeral=True)

# تنفيذ الطلب
from discord.ui import Select, View, Button

async def ask_dropdown(options, placeholder, interaction):
    class DropdownView(View):
        def __init__(self):
            super().__init__(timeout=60)
            self.selected = None

            select = Select(placeholder=placeholder, options=[discord.SelectOption(label=o) for o in options])
            select.callback = self.select_callback
            self.add_item(select)

        async def select_callback(self, select_interaction):
            self.selected = select_interaction.data['values'][0]
            self.stop()

    view = DropdownView()
    await interaction.followup.send("اختر:", view=view, ephemeral=True)
    await view.wait()
    return view.selected

@tree.command(name="طلب")
async def order(interaction: Interaction):
    await interaction.response.defer(ephemeral=True)
    guild_id = interaction.guild_id
    data = servers_data.get(guild_id)
    if not data:
        await interaction.followup.send("❌ لا يوجد متجر", ephemeral=True)
        return

    الأقسام = list(data["categories"].keys())
    if not الأقسام:
        await interaction.followup.send("❌ لا توجد أقسام", ephemeral=True)
        return

    القسم = await ask_dropdown(الأقسام, "اختر القسم", interaction)
    المنتجات = list(data["categories"][القسم].keys())
    المنتج = await ask_dropdown(المنتجات, "اختر المنتج", interaction)
    الكميات = [str(i) for i in range(1, data["categories"][القسم][المنتج]["quantity"] + 1)]
    الكمية = await ask_dropdown(الكميات, "اختر الكمية", interaction)

    الطلب = f"قسم: {القسم}\nمنتج: {المنتج}\nالكمية: {الكمية}"
    العميل = interaction.user
    embed = Embed(title="🧾 فاتورة الطلب", description=طلب, color=0x00ff00)
    embed.add_field(name="رابط الدفع", value=data["payment_link"] or "❌ لم يتم تحديد رابط")
    embed.set_footer(text=f"المتجر: {data['store_name']}")
    try:
        await العميل.send(embed=embed)
    except:
        await interaction.followup.send("❌ لا يمكن إرسال فاتورة للخاص", ephemeral=True)
        return

    # إرسال الطلب لروم الطلبات
    orders_channel_id = data["orders_channel"]
    if orders_channel_id:
        channel = bot.get_channel(orders_channel_id)
        if channel:
            await channel.send(f"🛒 طلب جديد من: {العميل.mention}\n{الطلب}")

    # تقييم
    class RateView(View):
        def __init__(self):
            super().__init__(timeout=60)
            for i in range(1, 6):
                self.add_item(Button(label=str(i), style=discord.ButtonStyle.primary, custom_id=f"rate_{i}"))

        @discord.ui.button(label="1", style=discord.ButtonStyle.primary, custom_id="rate_1")
        async def rate_1(self, interaction, button): await self.rate(interaction, 1)

        async def rate(self, interaction, stars):
            await interaction.response.send_message("🌟 شكرًا لتقييمك", ephemeral=True)
            if orders_channel_id:
                channel = bot.get_channel(orders_channel_id)
                await channel.send(f"⭐ تقييم جديد من {العميل.mention} على طلبه:\n{الطلب}\nالتقييم: {stars} نجوم")

    try:
        await العميل.send("🌟 قيّم طلبك من 1 إلى 5:", view=RateView())
    except:
        pass

    await interaction.followup.send("✅ تم تنفيذ الطلب وإرسال الفاتورة في الخاص", ephemeral=True)

# تشغيل السيرفر للـ keep_alive
keep_alive()

# تشغيل البوت باستخدام التوكن من متغير البيئة
bot.run(os.getenv("TOKEN"))
