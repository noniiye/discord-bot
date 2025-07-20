
import discord
from discord.ext import commands, tasks
from discord import app_commands, Interaction, Embed, ButtonStyle
from discord.ui import View, Button, Select
import json, os
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# بيانات المتاجر لكل سيرفر
data = {}

# ملف Keep Alive لتشغيل البوت على Render
app = Flask('')
@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# تحميل البيانات عند التشغيل
def load_data():
    global data
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            data = json.load(f)
    else:
        data = {}

def save_data():
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    load_data()
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

def ensure_guild(guild_id):
    if str(guild_id) not in data:
        data[str(guild_id)] = {
            "store_name": "",
            "categories": {},
            "payment_link": "",
            "orders_channel": None
        }

# أمر إنشاء متجر
@tree.command(name="انشاء_متجر", description="إنشاء متجر جديد باسم مخصص")
@app_commands.describe(الاسم="اسم المتجر")
async def انشاء_متجر(interaction: Interaction, الاسم: str):
    ensure_guild(interaction.guild_id)
    data[str(interaction.guild_id)]["store_name"] = الاسم
    save_data()
    await interaction.response.send_message(embed=Embed(description=f"✅ تم إنشاء المتجر باسم **{الاسم}**", color=0x2ecc71), ephemeral=True)

# أمر إضافة قسم
@tree.command(name="اضافة_قسم", description="إضافة قسم جديد")
@app_commands.describe(اسم_القسم="اسم القسم")
async def اضافة_قسم(interaction: Interaction, اسم_القسم: str):
    ensure_guild(interaction.guild_id)
    data[str(interaction.guild_id)]["categories"][اسم_القسم] = {}
    save_data()
    await interaction.response.send_message(embed=Embed(description=f"✅ تم إضافة القسم **{اسم_القسم}**", color=0x2ecc71), ephemeral=True)

# أمر إضافة منتج
@tree.command(name="اضافة_منتج", description="إضافة منتج إلى قسم")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج", الكمية="الكمية", السعر="السعر")
async def اضافة_منتج(interaction: Interaction, القسم: str, المنتج: str, الكمية: int, السعر: float):
    ensure_guild(interaction.guild_id)
    if القسم in data[str(interaction.guild_id)]["categories"]:
        data[str(interaction.guild_id)]["categories"][القسم][المنتج] = {"quantity": الكمية, "price": السعر}
        save_data()
        await interaction.response.send_message(embed=Embed(description=f"✅ تمت إضافة المنتج **{المنتج}** إلى قسم **{القسم}**", color=0x2ecc71), ephemeral=True)
    else:
        await interaction.response.send_message(embed=Embed(description="❌ القسم غير موجود", color=0xe74c3c), ephemeral=True)

# أمر تحديد رابط الدفع
@tree.command(name="تحديد_رابط_دفع", description="إعداد رابط الدفع للمتجر")
@app_commands.describe(الرابط="الرابط")
async def تحديد_رابط_دفع(interaction: Interaction, الرابط: str):
    ensure_guild(interaction.guild_id)
    data[str(interaction.guild_id)]["payment_link"] = الرابط
    save_data()
    await interaction.response.send_message(embed=Embed(description="✅ تم حفظ رابط الدفع", color=0x2ecc71), ephemeral=True)

# أمر تحديد روم الطلبات
@tree.command(name="تحديد_روم_طلبات", description="تحديد روم استقبال الطلبات")
@app_commands.describe(channel="روم الطلبات")
async def تحديد_روم_طلبات(interaction: Interaction, channel: discord.TextChannel):
    ensure_guild(interaction.guild_id)
    data[str(interaction.guild_id)]["orders_channel"] = channel.id
    save_data()
    await interaction.response.send_message(embed=Embed(description=f"✅ تم تحديد روم الطلبات: {channel.mention}", color=0x2ecc71), ephemeral=True)

# أمر حذف متجر / قسم / منتج / رابط
@tree.command(name="حذف", description="حذف متجر أو قسم أو منتج أو رابط")
@app_commands.describe(نوع="ما الذي تريد حذفه", الاسم="اسم القسم أو المنتج إن وجد")
async def حذف(interaction: Interaction, نوع: str, الاسم: str = None):
    ensure_guild(interaction.guild_id)
    store = data[str(interaction.guild_id)]
    if نوع == "متجر":
        del data[str(interaction.guild_id)]
        save_data()
        await interaction.response.send_message(embed=Embed(description="🗑️ تم حذف المتجر بالكامل", color=0xe74c3c), ephemeral=True)
    elif نوع == "رابط":
        store["payment_link"] = ""
        save_data()
        await interaction.response.send_message(embed=Embed(description="🗑️ تم حذف رابط الدفع", color=0xe74c3c), ephemeral=True)
    elif نوع == "قسم" and الاسم:
        if الاسم in store["categories"]:
            del store["categories"][الاسم]
            save_data()
            await interaction.response.send_message(embed=Embed(description=f"🗑️ تم حذف القسم **{الاسم}**", color=0xe74c3c), ephemeral=True)
    elif نوع == "منتج" and الاسم:
        for قسم in store["categories"]:
            if الاسم in store["categories"][قسم]:
                del store["categories"][قسم][الاسم]
                save_data()
                await interaction.response.send_message(embed=Embed(description=f"🗑️ تم حذف المنتج **{الاسم}**", color=0xe74c3c), ephemeral=True)
                return

# أمر الطلب
@tree.command(name="طلب", description="طلب منتج من المتجر")
async def طلب(interaction: Interaction):
    ensure_guild(interaction.guild_id)
    store = data[str(interaction.guild_id)]
    if not store["categories"]:
        await interaction.response.send_message(embed=Embed(description="❌ لا توجد أقسام متاحة", color=0xe74c3c), ephemeral=True)
        return

    class ProductSelect(Select):
        def __init__(self, category_name):
            self.category_name = category_name
            options = [
                discord.SelectOption(label=product, description=f"السعر: {info['price']} | الكمية: {info['quantity']}")
                for product, info in store["categories"][category_name].items()
            ]
            super().__init__(placeholder="اختر منتج", options=options)

        async def callback(self, interaction2: Interaction):
            المنتج = self.values[0]
            await interaction2.response.send_modal(QuantityModal(self.category_name, المنتج))

    class QuantityModal(discord.ui.Modal, title="أدخل الكمية المطلوبة"):
        def __init__(self, القسم, المنتج):
            super().__init__()
            self.القسم = القسم
            self.المنتج = المنتج
            self.add_item(discord.ui.TextInput(label="الكمية", placeholder="مثال: 2", required=True))

        async def on_submit(self, interaction3: Interaction):
            الكمية = int(self.children[0].value)
            القسم = self.القسم
            المنتج = self.المنتج
            سعر = store["categories"][القسم][المنتج]["price"]
            رابط = store["payment_link"]
            اسم_المتجر = store["store_name"]
            روم_الطلبات = store["orders_channel"]
            وصف_الطلب = f"**القسم:** {القسم}
**المنتج:** {المنتج}
**الكمية:** {الكمية}
**السعر:** {سعر * الكمية} ريال"

            if روم_الطلبات:
                ch = bot.get_channel(int(Rوم_الطلبات))
                if ch:
                    await ch.send(embed=Embed(title="📥 طلب جديد", description=f"{وصف_الطلب}

👤 <@{interaction.user.id}>", color=0x3498db))

            # إرسال الفاتورة في الخاص
            try:
                فاتورة = Embed(title="🧾 فاتورتك", description=f"**{اسم_المتجر}**

{وصف_الطلب}

🔗 [رابط الدفع]({رابط})", color=0xf1c40f)
                await interaction3.user.send(embed=فاتورة)
                await interaction3.user.send(embed=Embed(description="يرجى تقييم تجربتك:", color=0x95a5a6), view=RatingButtons(interaction3.user.id, وصف_الطلب, روم_الطلبات))
            except:
                pass

            await interaction3.response.send_message(embed=Embed(description="✅ تم إرسال الطلب والفاتورة إلى الخاص", color=0x2ecc71), ephemeral=True)

    class CategorySelect(Select):
        def __init__(self):
            options = [discord.SelectOption(label=cat) for cat in store["categories"].keys()]
            super().__init__(placeholder="اختر قسم", options=options)

        async def callback(self, interaction2: Interaction):
            await interaction2.response.send_message(view=View(ProductSelect(self.values[0])), ephemeral=True)

    class RatingButtons(View):
        def __init__(self, user_id, وصف_الطلب, روم):
            super().__init__()
            self.user_id = user_id
            self.وصف_الطلب = وصف_الطلب
            self.روم = روم

            for i in range(1, 6):
                self.add_item(Button(label=str(i), style=ButtonStyle.primary))

        @discord.ui.button(label="⭐", style=discord.ButtonStyle.primary)
        async def rate_button(self, interaction: Interaction, button: Button):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ هذا التقييم ليس لك", ephemeral=True)
                return
            await interaction.response.send_message("✅ شكرًا لتقييمك!", ephemeral=True)
            if self.روم:
                ch = bot.get_channel(int(self.روم))
                if ch:
                    await ch.send(embed=Embed(description=f"⭐ تقييم جديد من <@{self.user_id}>:
{self.وصف_الطلب}", color=0x3498db))

    await interaction.response.send_message(view=View(CategorySelect()), ephemeral=True)

keep_alive()
bot.run(os.getenv("TOKEN"))

