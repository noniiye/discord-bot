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

@bot.tree.command(name="عرض_المنتجات")
async def عرض_المنتجات(interaction: Interaction):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data or not data[gid]["categories"]:
        await interaction.response.send_message("❌ لا يوجد منتجات.", ephemeral=True)
        return
    msg = "📦 المنتجات المتاحة:\n"
    for قسم, منتجات in data[gid]["categories"].items():
        msg += f"\n__{قسم}__:\n"
        for اسم, تفاصيل in منتجات.items():
            msg += f"- {اسم}: {تفاصيل['quantity']} قطعة | {تفاصيل['price']} ريال\n"
    await interaction.response.send_message(msg, ephemeral=True)

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

# أمر تنفيذ الطلب
@bot.tree.command(name="طلب")
async def طلب(interaction: Interaction):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data or not data[gid]["categories"]:
        await interaction.response.send_message("❌ لا يوجد متجر أو أقسام.", ephemeral=True)
        return

    class ProductQuantityModal(ui.Modal, title="📦 تحديد الكمية"):
        def __init__(self, القسم, المنتج):
            super().__init__()
            self.القسم = القسم
            self.المنتج = المنتج
            self.quantity = ui.TextInput(label="أدخل الكمية", style=discord.TextStyle.short, required=True)
            self.add_item(self.quantity)

        async def on_submit(self, interaction: Interaction):
            الكمية = int(self.quantity.value)
            المنتج_البيانات = data[gid]["categories"][self.القسم][self.المنتج]
            if الكمية > المنتج_البيانات["quantity"]:
                await interaction.response.send_message("❌ الكمية غير متوفرة.", ephemeral=True)
                return
            المنتج_البيانات["quantity"] -= الكمية
            save_data(data)

            الطلب = f"🛒 الطلب: {self.المنتج} من قسم {self.القسم} × {الكمية}"
            رابط_الدفع = data[gid].get("payment", "غير محدد")
            embed = Embed(title=f"فاتورة من متجر {data[gid]['store_name']}", description=الطلب, color=0x00ff00)
            embed.add_field(name="رابط الدفع", value=رابط_الدفع, inline=False)
            await interaction.user.send(embed=embed)

            order_channel_id = data[gid].get("order_channel")
            if order_channel_id:
                channel = bot.get_channel(order_channel_id)
                if channel:
                    await channel.send(f"📥 طلب جديد من {interaction.user.mention}:\n{الطلب}")

            await interaction.response.send_message("✅ تم تنفيذ الطلب وتم إرسال الفاتورة في الخاص.", ephemeral=True)

    class منتجView(ui.View):
        def __init__(self, القسم):
            super().__init__(timeout=60)
            for منتج in data[gid]["categories"][القسم]:
                self.add_item(ui.Button(label=منتج, style=ButtonStyle.secondary, custom_id=f"product_{القسم}_{منتج}"))

        async def interaction_check(self, i: Interaction):
            return i.user.id == interaction.user.id

    class قسمView(ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            for قسم in data[gid]["categories"]:
                self.add_item(ui.Button(label=قسم, style=ButtonStyle.primary, custom_id=f"section_{قسم}"))

        async def interaction_check(self, i: Interaction):
            return i.user.id == interaction.user.id

    view = قسمView()
    msg = await interaction.response.send_message("📁 اختر القسم:", view=view, ephemeral=True)

    async def wait_for_interaction():
        try:
            interaction2 = await bot.wait_for("interaction", check=lambda i: i.user == interaction.user and i.data["custom_id"].startswith("section_"), timeout=60)
            القسم = interaction2.data["custom_id"][8:]
            await interaction2.response.edit_message(content=f"🗂️ اختر المنتج من قسم: {القسم}", view=منتجView(القسم))

            interaction3 = await bot.wait_for("interaction", check=lambda i: i.user == interaction.user and i.data["custom_id"].startswith("product_"), timeout=60)
            _, القسم, المنتج = interaction3.data["custom_id"].split("_", 2)
            await interaction3.response.send_modal(ProductQuantityModal(القسم, المنتج))

        except Exception:
            pass

    await wait_for_interaction()

# Flask للتشغيل في Render
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل"

Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

bot.run(os.getenv("TOKEN"))
