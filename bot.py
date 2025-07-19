# bot.py

import discord
from discord.ext import commands
from discord import app_commands, Intents, Interaction, Embed, ButtonStyle
from discord.ui import View, Button, Select
import json
import os
import flask
from threading import Thread

intents = Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# تأكيد وجود ملف البيانات
if not os.path.exists("data.json"):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=4)

def load_data():
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

@tree.command(name="إنشاء_متجر", description="إنشاء متجر جديد باسم مخصص")
async def create_shop(interaction: Interaction, الاسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data:
        return await interaction.response.send_message("⚠️ المتجر موجود بالفعل", ephemeral=True)
    data[gid] = {"store_name": الاسم, "categories": {}, "payment": "", "orders_channel": None}
    save_data(data)
    await interaction.response.send_message(f"✅ تم إنشاء المتجر باسم: **{الاسم}**", ephemeral=True)

@tree.command(name="تحديد_روم_الطلبات", description="حدد الروم الذي ستصله الطلبات")
async def set_orders_channel(interaction: Interaction, channel: discord.TextChannel):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        return await interaction.response.send_message("❌ لم يتم إنشاء المتجر بعد", ephemeral=True)
    data[gid]["orders_channel"] = channel.id
    save_data(data)
    await interaction.response.send_message("✅ تم تحديد روم الطلبات بنجاح", ephemeral=True)

@tree.command(name="إضافة_قسم", description="إضافة قسم جديد إلى المتجر")
async def add_category(interaction: Interaction, القسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        return await interaction.response.send_message("❌ لم يتم إنشاء المتجر بعد", ephemeral=True)
    if القسم in data[gid]["categories"]:
        return await interaction.response.send_message("⚠️ القسم موجود مسبقًا", ephemeral=True)
    data[gid]["categories"][القسم] = {}
    save_data(data)
    await interaction.response.send_message(f"✅ تم إضافة القسم: **{القسم}**", ephemeral=True)

@tree.command(name="إضافة_منتج", description="إضافة منتج داخل قسم")
async def add_product(interaction: Interaction, القسم: str, اسم_المنتج: str, الكمية: int, السعر: int):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        return await interaction.response.send_message("❌ لم يتم إنشاء المتجر بعد", ephemeral=True)
    if القسم not in data[gid]["categories"]:
        return await interaction.response.send_message("❌ القسم غير موجود", ephemeral=True)
    data[gid]["categories"][القسم][اسم_المنتج] = {"quantity": الكمية, "price": السعر}
    save_data(data)
    await interaction.response.send_message(f"✅ تم إضافة المنتج **{اسم_المنتج}** إلى القسم **{القسم}**", ephemeral=True)

@tree.command(name="إضافة_رابط_دفع", description="أضف رابط الدفع الذي سيظهر بالفاتورة")
async def add_payment_link(interaction: Interaction, الرابط: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        return await interaction.response.send_message("❌ لم يتم إنشاء المتجر بعد", ephemeral=True)
    data[gid]["payment"] = الرابط
    save_data(data)
    await interaction.response.send_message("✅ تم حفظ رابط الدفع بنجاح", ephemeral=True)

@tree.command(name="طلب", description="طلب منتج من المتجر")
async def make_order(interaction: Interaction):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data or not data[gid]["categories"]:
        return await interaction.response.send_message("❌ المتجر غير جاهز أو لا يحتوي منتجات", ephemeral=True)

    class ProductSelect(Select):
        def __init__(self, options):
            super().__init__(placeholder="اختر منتجًا", min_values=1, max_values=1, options=options)

        async def callback(self, select_interaction: Interaction):
            المنتج = self.values[0]
            category, product_name = المنتج.split("::")
            المنتج_البيانات = data[gid]["categories"][category][product_name]
            السعر = المنتج_البيانات["price"]
            رابط_الدفع = data[gid]["payment"]
            الطلبات_الروم = data[gid]["orders_channel"]
            
            embed = Embed(title="📦 فاتورة الطلب", color=discord.Color.green())
            embed.add_field(name="المتجر", value=data[gid]["store_name"], inline=False)
            embed.add_field(name="المنتج", value=product_name, inline=True)
            embed.add_field(name="القسم", value=category, inline=True)
            embed.add_field(name="السعر", value=f"{السعر} ريال", inline=True)
            embed.add_field(name="رابط الدفع", value=رابط_الدفع or "❌ لا يوجد", inline=False)
            await select_interaction.user.send(embed=embed)
            
            await select_interaction.user.send("✨ كيف تقيم تجربتك من 1 إلى 5؟")
            
            class RateButtons(View):
                def __init__(self):
                    super().__init__(timeout=None)
                    for i in range(1, 6):
                        self.add_item(Button(label=str(i), style=ButtonStyle.primary))

                @discord.ui.button(label="1", style=ButtonStyle.secondary)
                async def rate1(self, _, button_interaction):
                    await self.finish_rating(button_interaction, 1)

                async def finish_rating(self, interaction, rate):
                    await interaction.response.send_message("✅ شكرًا لتقييمك!", ephemeral=True)
                    if الطلبات_الروم:
                        ch = bot.get_channel(الطلبات_الروم)
                        if ch:
                            await ch.send(f"✅ طلب جديد: {product_name} من {interaction.user.mention} - التقييم: {rate}/5")

            await select_interaction.user.send(view=RateButtons())
            await interaction.followup.send("✅ تم إرسال الفاتورة إلى الخاص", ephemeral=True)

    الخيارات = []
    for category, products in data[gid]["categories"].items():
        for name, info in products.items():
            if info["quantity"] > 0:
                الخيارات.append(discord.SelectOption(label=f"{name} ({category})", value=f"{category}::{name}"))

    if not الخيارات:
        return await interaction.response.send_message("❌ لا توجد منتجات متاحة حاليًا", ephemeral=True)

    view = View()
    view.add_item(ProductSelect(الخيارات))
    await interaction.response.send_message("🔽 اختر منتجًا من القائمة:", view=view, ephemeral=True)

# Flask keep_alive
app = flask.Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run).start()

bot.run(os.getenv("TOKEN"))
