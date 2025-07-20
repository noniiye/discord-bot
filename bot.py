import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed, ButtonStyle
from discord.ui import View, Button, Select
import asyncio
import json
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

data_file = "data.json"

# حفظ البيانات
def save_data(data):
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# تحميل البيانات
def load_data():
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

data = load_data()

# حفظ المتغيرات بعد كل تعديل
def update():
    save_data(data)

# ====== KEEP ALIVE FOR RENDER ======
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ====== EVENTS ======
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await tree.sync()

# ====== أوامر المتجر ======

@tree.command(name="انشاء_متجر", description="انشاء متجر خاص بالسيرفر")
@app_commands.describe(اسم_المتجر="اكتب اسم المتجر")
async def create_store(interaction: Interaction, اسم_المتجر: str):
    guild_id = str(interaction.guild.id)
    if guild_id in data:
        return await interaction.response.send_message("❌ المتجر موجود بالفعل.", ephemeral=True)
    data[guild_id] = {
        "store_name": اسم_المتجر,
        "sections": {},
        "payment_link": "",
        "order_channel": None
    }
    update()
    await interaction.response.send_message(f"✅ تم إنشاء المتجر باسم **{اسم_المتجر}**", ephemeral=True)

@tree.command(name="اضافة_قسم", description="أضف قسم جديد للمتجر")
@app_commands.describe(اسم_القسم="اكتب اسم القسم")
async def add_section(interaction: Interaction, اسم_القسم: str):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        return await interaction.response.send_message("❌ يجب أولاً إنشاء متجر.", ephemeral=True)
    if اسم_القسم in data[guild_id]["sections"]:
        return await interaction.response.send_message("❌ القسم موجود مسبقاً.", ephemeral=True)
    data[guild_id]["sections"][اسم_القسم] = {}
    update()
    await interaction.response.send_message(f"✅ تم إضافة القسم **{اسم_القسم}**", ephemeral=True)

@tree.command(name="اضافة_منتج", description="أضف منتج داخل قسم")
@app_commands.describe(اسم_القسم="القسم الموجود", اسم_المنتج="اسم المنتج", الكمية="الكمية المتاحة", السعر="سعر المنتج")
async def add_product(interaction: Interaction, اسم_القسم: str, اسم_المنتج: str, الكمية: int, السعر: float):
    guild_id = str(interaction.guild.id)
    if guild_id not in data or اسم_القسم not in data[guild_id]["sections"]:
        return await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)
    data[guild_id]["sections"][اسم_القسم][اسم_المنتج] = {"quantity": الكمية, "price": السعر}
    update()
    await interaction.response.send_message(f"✅ تم إضافة المنتج **{اسم_المنتج}** إلى قسم **{اسم_القسم}**", ephemeral=True)

@tree.command(name="رابط_الدفع", description="حدد رابط الدفع للفواتير")
@app_commands.describe(الرابط="أدخل رابط الدفع")
async def set_payment_link(interaction: Interaction, الرابط: str):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        return await interaction.response.send_message("❌ يجب أولاً إنشاء متجر.", ephemeral=True)
    data[guild_id]["payment_link"] = الرابط
    update()
    await interaction.response.send_message("✅ تم تعيين رابط الدفع.", ephemeral=True)

@tree.command(name="تحديد_روم_الطلبات", description="حدد روم الطلبات")
@app_commands.describe(channel="اختر الروم الذي تصلك عليه الطلبات")
async def set_order_channel(interaction: Interaction, channel: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        return await interaction.response.send_message("❌ يجب أولاً إنشاء متجر.", ephemeral=True)
    data[guild_id]["order_channel"] = channel.id
    update()
    await interaction.response.send_message(f"✅ تم تحديد روم الطلبات: {channel.mention}", ephemeral=True)

@tree.command(name="طلب", description="قم بطلب منتج")
async def make_order(interaction: Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id not in data or not data[guild_id]["sections"]:
        return await interaction.response.send_message("❌ لا يوجد أقسام لعرضها.", ephemeral=True)

    class SectionView(View):
        def __init__(self):
            super().__init__(timeout=60)
            options = [discord.SelectOption(label=sec) for sec in data[guild_id]["sections"].keys()]
            self.select = Select(placeholder="اختر القسم", options=options)
            self.select.callback = self.section_selected
            self.add_item(self.select)

        async def section_selected(self, interaction2: Interaction):
            selected_section = self.select.values[0]
            products = data[guild_id]["sections"][selected_section]
            if not products:
                return await interaction2.response.send_message("❌ لا يوجد منتجات في هذا القسم.", ephemeral=True)

            class ProductView(View):
                def __init__(self):
                    super().__init__(timeout=60)
                    options = [discord.SelectOption(label=p) for p in products]
                    self.select = Select(placeholder="اختر المنتج", options=options)
                    self.select.callback = self.product_selected
                    self.add_item(self.select)

                async def product_selected(self, interaction3: Interaction):
                    selected_product = self.select.values[0]

                    await interaction3.response.send_message(f"اكتب الكمية المطلوبة من **{selected_product}**:", ephemeral=True)

                    def check(msg):
                        return msg.author == interaction3.user and msg.channel == interaction3.channel

                    try:
                        msg = await bot.wait_for('message', check=check, timeout=60)
                        quantity = int(msg.content)
                        product_info = products[selected_product]

                        if quantity > product_info["quantity"]:
                            return await interaction3.followup.send("❌ الكمية غير متوفرة.", ephemeral=True)

                        # تقليل الكمية
                        product_info["quantity"] -= quantity
                        update()

                        # إرسال الطلب
                        ch_id = data[guild_id]["order_channel"]
                        if ch_id:
                            ch = bot.get_channel(ch_id)
                            order_desc = f"📦 طلب جديد من <@{interaction.user.id}>:
المنتج: {selected_product}
الكمية: {quantity}"
                            await ch.send(order_desc)

                        # إرسال الفاتورة
                        store_name = data[guild_id]["store_name"]
                        pay_link = data[guild_id]["payment_link"]
                        embed = Embed(title="فاتورتك", description=f"**{store_name}**
المنتج: {selected_product}
الكمية: {quantity}
السعر: {product_info['price']} ريال")
                        embed.add_field(name="رابط الدفع", value=pay_link, inline=False)
                        await interaction3.user.send(embed=embed)

                        # رسالة التقييم
                        class RateView(View):
                            def __init__(self):
                                super().__init__(timeout=60)
                                for star in range(1, 6):
                                    self.add_item(Button(label=f"{star}⭐", style=ButtonStyle.primary, custom_id=str(star)))

                            @discord.ui.button(label="⭐", style=ButtonStyle.secondary, custom_id="rate")
                            async def on_click(self, button, interaction4):
                                rating = button.custom_id
                                await interaction4.response.send_message("✅ شكرًا لتقييمك!", ephemeral=True)
                                if ch_id:
                                    await ch.send(f"⭐ تقييم جديد من <@{interaction.user.id}>: {rating}/5")

                        await interaction3.user.send("كيف تقيم الطلب؟", view=RateView())

                    except asyncio.TimeoutError:
                        await interaction3.followup.send("⏰ انتهى الوقت.", ephemeral=True)

            await interaction2.response.send_message("اختر المنتج:", view=ProductView(), ephemeral=True)

    await interaction.response.send_message("اختر القسم:", view=SectionView(), ephemeral=True)

# ====== تشغيل البوت ======
keep_alive()
bot.run("YOUR_BOT_TOKEN")
