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

# تهيئة الأوامر عند التشغيل
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ تم تسجيل {len(bot.tree.get_commands())} أمر سلاش")

# أوامر الإدارة
@bot.tree.command(name="إنشاء_متجر")
@app_commands.describe(الاسم="اسم المتجر")
async def انشاء_متجر(interaction: Interaction, الاسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    data[gid] = {
        "store_name": الاسم,
        "categories": {},
        "payment": "غير محدد",
        "order_channel": None,
        "client_order_channel": None
    }
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

@bot.tree.command(name="روم_الطلبات")
@app_commands.describe(الروم="حدد روم الطلبات الخاص بالعملاء")
async def روم_الطلبات(interaction: Interaction, الروم: discord.TextChannel):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ يجب إنشاء متجر أولاً.", ephemeral=True)
        return
    data[gid]["client_order_channel"] = الروم.id
    save_data(data)
    await interaction.response.send_message(f"✅ تم تعيين روم الطلبات الخاص بالعملاء: {الروم.mention}", ephemeral=True)

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

@bot.tree.command(name="طلب")
async def طلب(interaction: Interaction):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data or not data[gid]["categories"]:
        await interaction.response.send_message("❌ لا توجد منتجات للعرض.", ephemeral=True)
        return

    class ProductView(ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            for القسم, المنتجات in data[gid]["categories"].items():
                for اسم_المنتج, تفاصيل in المنتجات.items():
                    self.add_item(ui.Button(label=f"{اسم_المنتج} - {تفاصيل['price']} ريال", custom_id=f"طلب:{القسم}:{اسم_المنتج}"))

        @ui.button(label="إلغاء", style=ButtonStyle.danger, custom_id="إلغاء")
        async def cancel(self, interaction: Interaction, button: ui.Button):
            await interaction.message.delete()

    await interaction.response.send_message("📦 اختر منتج للطلب:", view=ProductView(), ephemeral=True)

class QuantityModal(ui.Modal, title="تحديد الكمية"):
    def __init__(self, القسم, المنتج):
        super().__init__()
        self.القسم = القسم
        self.المنتج = المنتج
        self.input = ui.TextInput(label="اكتب الكمية المطلوبة:", style=discord.TextStyle.short)
        self.add_item(self.input)

    async def on_submit(self, interaction: Interaction):
        data = load_data()
        gid = str(interaction.guild_id)
        تفاصيل = data[gid]["categories"][self.القسم][self.المنتج]
        الكمية = int(self.input.value)
        السعر_الإجمالي = الكمية * تفاصيل["price"]
        المستخدم = interaction.user

        # إرسال الطلب لروم التاجر
        order_channel = interaction.guild.get_channel(data[gid]["order_channel"])
        if order_channel:
            await order_channel.send(
                f"🛒 طلب جديد من {المستخدم.mention}\n"
                f"📦 المنتج: {self.المنتج}\n"
                f"📁 القسم: {self.القسم}\n"
                f"🔢 الكمية: {الكمية}\n"
                f"💰 السعر الإجمالي: {السعر_الإجمالي} ريال"
            )

        # إرسال الفاتورة للعميل
        try:
            await المستخدم.send(embed=Embed(
                title="🧾 فاتورة الطلب",
                description=(
                    f"**المتجر:** {data[gid]['store_name']}\n"
                    f"**المنتج:** {self.المنتج}\n"
                    f"**الكمية:** {الكمية}\n"
                    f"**الإجمالي:** {السعر_الإجمالي} ريال\n"
                    f"**رابط الدفع:** {data[gid]['payment']}"
                ),
                color=0x00ff00
            ))
        except:
            pass

        await interaction.response.send_message("✅ تم تنفيذ الطلب! تحقق من الخاص للفاتورة.", ephemeral=True)

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data["custom_id"].startswith("طلب:"):
            _, القسم, المنتج = interaction.data["custom_id"].split(":")
            await interaction.response.send_modal(QuantityModal(القسم, المنتج))

# حذف المتجر
@bot.tree.command(name="حذف_المتجر")
async def حذف_المتجر(interaction: Interaction):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data:
        del data[gid]
        save_data(data)
        await interaction.response.send_message("✅ تم حذف المتجر.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ لا يوجد متجر لحذفه.", ephemeral=True)

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

# Flask للتشغيل في Render
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل"

Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

bot.run(os.getenv("TOKEN"))
