import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction, Embed
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

# المودال لإدخال الكمية
class QuantityModal(ui.Modal, title="🧾 أدخل الكمية"):
    الكمية = ui.TextInput(label="الكمية", placeholder="مثال: 2", required=True)

    def __init__(self, interaction: Interaction, القسم: str, المنتج: str):
        super().__init__()
        self.interaction = interaction
        self.القسم = القسم
        self.المنتج = المنتج

    async def on_submit(self, interaction: Interaction):
        data = load_data()
        gid = str(interaction.guild_id)
        uid = str(interaction.user.id)
        الكمية = int(self.الكمية.value)

        المنتج_البيانات = data[gid]["categories"][self.القسم][self.المنتج]
        السعر = المنتج_البيانات["price"]
        المجموع = السعر * الكمية
        رابط_الدفع = data[gid].get("payment", "غير محدد")
        اسم_المتجر = data[gid]["store_name"]

        # إرسال الفاتورة في الخاص
        embed = Embed(title=f"🧾 فاتورة الطلب من متجر {اسم_المتجر}", color=0x2ecc71)
        embed.add_field(name="المنتج", value=self.المنتج, inline=True)
        embed.add_field(name="القسم", value=self.القسم, inline=True)
        embed.add_field(name="الكمية", value=str(الكمية), inline=True)
        embed.add_field(name="السعر الكلي", value=f"{المجموع} ريال", inline=True)
        embed.add_field(name="رابط الدفع", value=رابط_الدفع, inline=False)
        try:
            await interaction.user.send(embed=embed)
        except:
            await interaction.response.send_message("❌ لم أتمكن من إرسال الفاتورة في الخاص.", ephemeral=True)
            return

        await interaction.response.send_message("✅ تم إرسال الفاتورة في الخاص.", ephemeral=True)

        # إرسال الطلب إلى روم التاجر
        طلب = f"🛒 طلب جديد من <@{uid}>\nالقسم: {self.القسم}\nالمنتج: {self.المنتج}\nالكمية: {الكمية}\nالسعر الكلي: {المجموع} ريال"
        order_channel_id = data[gid].get("order_channel")
        if order_channel_id:
            channel = bot.get_channel(order_channel_id)
            if channel:
                await channel.send(طلب)

        # إرسال التقييم للعميل
        view = ui.View()
        for i in range(1, 6):
            view.add_item(ui.Button(label=str(i), style=discord.ButtonStyle.primary, custom_id=f"rate_{i}_{gid}_{uid}_{self.المنتج}"))

        await interaction.user.send(embed=Embed(title="⭐ قيّم طلبك من 1 إلى 5", description="اضغط على رقم للتقييم"), view=view)

# حدث استقبال التقييم
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component and interaction.data["custom_id"].startswith("rate_"):
        _, rating, gid, uid, المنتج = interaction.data["custom_id"].split("_", 4)
        data = load_data()
        order_channel_id = data.get(gid, {}).get("order_channel")
        if order_channel_id:
            channel = bot.get_channel(int(order_channel_id))
            if channel:
                await channel.send(f"⭐ تقييم جديد من <@{uid}> للمنتج **{المنتج}**: {rating}/5")
        await interaction.response.send_message("شكراً لتقييمك!", ephemeral=True)

@bot.tree.command(name="شراء")
async def شراء(interaction: Interaction):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ لا يوجد متجر في هذا السيرفر.", ephemeral=True)
        return

    store_data = data[gid]
    if not store_data["categories"]:
        await interaction.response.send_message("❌ لا يوجد أقسام حالياً.", ephemeral=True)
        return

    class CategoryView(ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            for القسم in store_data["categories"]:
                self.add_item(ui.Button(label=القسم, custom_id=f"select_category_{القسم}"))

        async def interaction_check(self, i: Interaction) -> bool:
            return i.user.id == interaction.user.id

        async def on_timeout(self):
            await interaction.edit_original_response(content="⏱️ انتهى الوقت", view=None)

    await interaction.response.send_message("اختر القسم:", view=CategoryView(), ephemeral=True)

    async def category_listener():
        def check(i): return i.type == discord.InteractionType.component and i.user.id == interaction.user.id and i.data["custom_id"].startswith("select_category_")
        i = await bot.wait_for("interaction", check=check, timeout=60)
        القسم = i.data["custom_id"][len("select_category_"):]

        المنتجات = store_data["categories"].get(القسم, {})
        if not المنتجات:
            await i.response.send_message("❌ لا يوجد منتجات في هذا القسم", ephemeral=True)
            return

        class ProductView(ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                for المنتج in المنتجات:
                    self.add_item(ui.Button(label=المنتج, custom_id=f"select_product_{المنتج}"))

            async def interaction_check(self, j: Interaction) -> bool:
                return j.user.id == interaction.user.id

            async def on_timeout(self):
                await i.edit_original_response(content="⏱️ انتهى الوقت", view=None)

        await i.response.send_message("اختر المنتج:", view=ProductView(), ephemeral=True)

        def check2(j): return j.type == discord.InteractionType.component and j.user.id == interaction.user.id and j.data["custom_id"].startswith("select_product_")
        j = await bot.wait_for("interaction", check=check2, timeout=60)
        المنتج = j.data["custom_id"][len("select_product_"):]

        await j.response.send_modal(QuantityModal(j, القسم, المنتج))

    await category_listener()

# باقي أوامر الإدارة نفسها كما في الكود الحالي (انشاء متجر، روم التاجر، إضافة/حذف قسم ومنتج، رابط الدفع)

# Flask للتشغيل في Render
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل"

Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

bot.run(os.getenv("TOKEN"))
