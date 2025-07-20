import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction, Embed, ButtonStyle
import os, json
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ملف البيانات
DATA_FILE = "data.json"
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# أوامر الإدارة
@bot.tree.command(name="إنشاء_متجر")
@app_commands.describe(الاسم="اسم المتجر")
async def انشاء_متجر(interaction: Interaction, الاسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    data[gid] = {"store_name": الاسم, "categories": {}, "payment": "غير محدد", "order_channel": None}
    save_data(data)
    await interaction.response.send_message(f"✅ تم إنشاء المتجر باسم: {الاسم}", ephemeral=True)

@bot.tree.command(name="روم_التاجر")
@app_commands.describe(الروم="حدد روم استلام الطلبات")
async def روم_التاجر(interaction: Interaction, الروم: discord.TextChannel):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ يجب إنشاء متجر أولاً.", ephemeral=True)
        return
    data[gid]["order_channel"] = الروم.id
    save_data(data)
    await interaction.response.send_message(f"✅ تم تعيين روم التاجر: {الروم.mention}", ephemeral=True)

@bot.tree.command(name="إضافة_قسم")
@app_commands.describe(الاسم="اسم القسم")
async def اضافة_قسم(interaction: Interaction, الاسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ يجب إنشاء متجر أولاً.", ephemeral=True)
        return
    data[gid]["categories"][الاسم] = {}
    save_data(data)
    await interaction.response.send_message(f"✅ تم إضافة القسم: {الاسم}", ephemeral=True)

@bot.tree.command(name="إضافة_منتج")
@app_commands.describe(القسم="اسم القسم", الاسم="اسم المنتج", الكمية="الكمية المتوفرة", السعر="السعر")
async def اضافة_منتج(interaction: Interaction, القسم: str, الاسم: str, الكمية: int, السعر: int):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data or القسم not in data[gid]["categories"]:
        await interaction.response.send_message("❌ تأكد من وجود المتجر والقسم.", ephemeral=True)
        return
    data[gid]["categories"][القسم][الاسم] = {"quantity": الكمية, "price": السعر}
    save_data(data)
    await interaction.response.send_message(f"✅ تمت إضافة المنتج: {الاسم} في القسم: {القسم}", ephemeral=True)

@bot.tree.command(name="حذف_قسم")
@app_commands.describe(الاسم="اسم القسم")
async def حذف_قسم(interaction: Interaction, الاسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data and الاسم in data[gid]["categories"]:
        del data[gid]["categories"][الاسم]
        save_data(data)
        await interaction.response.send_message(f"✅ تم حذف القسم: {الاسم}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)

@bot.tree.command(name="حذف_منتج")
@app_commands.describe(القسم="اسم القسم", الاسم="اسم المنتج")
async def حذف_منتج(interaction: Interaction, القسم: str, الاسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data and القسم in data[gid]["categories"] and الاسم in data[gid]["categories"][القسم]:
        del data[gid]["categories"][القسم][الاسم]
        save_data(data)
        await interaction.response.send_message(f"✅ تم حذف المنتج: {الاسم} من القسم: {القسم}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ المنتج أو القسم غير موجود.", ephemeral=True)

@bot.tree.command(name="تحديد_رابط_الدفع")
@app_commands.describe(الرابط="رابط الدفع")
async def تحديد_رابط_الدفع(interaction: Interaction, الرابط: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ يجب إنشاء متجر أولاً.", ephemeral=True)
        return
    data[gid]["payment"] = الرابط
    save_data(data)
    await interaction.response.send_message("✅ تم تحديث رابط الدفع", ephemeral=True)

class QuantityModal(ui.Modal, title="أدخل الكمية"):
    الكمية = ui.TextInput(label="الكمية", style=discord.TextStyle.short)

    def __init__(self, القسم, المنتج, interaction: Interaction):
        super().__init__()
        self.القسم = القسم
        self.المنتج = المنتج
        self.original_interaction = interaction

    async def on_submit(self, interaction: Interaction):
        data = load_data()
        gid = str(interaction.guild_id)
        المنتج = data[gid]["categories"][self.القسم][self.المنتج]
        if int(self.الكمية.value) > المنتج["quantity"]:
            await interaction.response.send_message("❌ الكمية غير متوفرة.", ephemeral=True)
            return

        # خصم الكمية
        المنتج["quantity"] -= int(self.الكمية.value)
        save_data(data)

        # إرسال الفاتورة في الخاص
        الدفع = data[gid].get("payment", "غير محدد")
        embed = Embed(title="فاتورة الطلب", description=f"**{data[gid]['store_name']}**\n\nالقسم: {self.القسم}\nالمنتج: {self.المنتج}\nالكمية: {self.الكمية.value}\nالسعر: {المنتج['price']} ريال\n\nرابط الدفع: {الدفع}", color=0x00ff00)
        try:
            await interaction.user.send(embed=embed)
        except:
            await self.original_interaction.followup.send("❌ لم يتم إرسال الفاتورة في الخاص.", ephemeral=True)
            return

        await interaction.response.send_message("✅ تم تنفيذ الطلب، وتم إرسال الفاتورة في الخاص.", ephemeral=True)

        # إرسال الطلب لروم التاجر
        order_channel_id = data[gid].get("order_channel")
        if order_channel_id:
            channel = bot.get_channel(order_channel_id)
            if channel:
                await channel.send(f"📦 طلب جديد من {interaction.user.mention}\nالقسم: {self.القسم}\nالمنتج: {self.المنتج}\nالكمية: {self.الكمية.value}")

        # إرسال التقييم
        class RatingView(ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                for i in range(1, 6):
                    self.add_item(ui.Button(label="⭐" * i, style=ButtonStyle.primary, custom_id=f"rating_{i}"))

        await interaction.user.send("يرجى تقييم طلبك:", view=RatingView())

@bot.event
async def on_interaction(interaction: Interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data["custom_id"].startswith("rating_"):
            rating = interaction.data["custom_id"].split("_")[1]
            await interaction.response.send_message("✅ شكرًا لتقييمك!", ephemeral=True)
            data = load_data()
            gid = str(interaction.guild_id)
            order_channel_id = data.get(gid, {}).get("order_channel")
            if order_channel_id:
                channel = bot.get_channel(order_channel_id)
                if channel:
                    await channel.send(f"🌟 تقييم من {interaction.user.mention}: {rating} نجوم")

@bot.tree.command(name="طلب")
async def طلب(interaction: Interaction):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ لا يوجد متجر في هذا السيرفر.", ephemeral=True)
        return

    class CategoryView(ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            for قسم in data[gid]["categories"]:
                self.add_item(ui.Button(label=قسم, custom_id=f"category_{قسم}"))

    await interaction.response.send_message("اختر القسم:", view=CategoryView(), ephemeral=True)

    async def category_callback(i: Interaction):
        القسم = i.data["custom_id"].split("_", 1)[1]
        class ProductView(ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                for منتج in data[gid]["categories"][القسم]:
                    self.add_item(ui.Button(label=منتج, custom_id=f"product_{القسم}_{منتج}"))
        await i.response.send_message("اختر المنتج:", view=ProductView(), ephemeral=True)

    async def product_callback(i: Interaction):
        _, القسم, المنتج = i.data["custom_id"].split("_", 2)
        await i.response.send_modal(QuantityModal(القسم, المنتج, i))

    bot.add_view(ui.View())  # لتفعيل الأزرار

# Flask للتشغيل في Render
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل"

Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

bot.run(os.getenv("TOKEN"))
