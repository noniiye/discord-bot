
import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed, ButtonStyle
from discord.ui import View, Button
import os
import json
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# لتشغيل السيرفر Flask
keep_alive()

# قاعدة بيانات بسيطة باستخدام JSON
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@tree.command(name="انشاء_متجر", description="إنشاء متجر جديد مع اسم مخصص")
@app_commands.describe(اسم="اسم المتجر")
async def انشاء_متجر(interaction: Interaction, اسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data:
        return await interaction.response.send_message("❌ يوجد متجر بالفعل لهذا السيرفر.", ephemeral=True)
    data[gid] = {"store_name": اسم, "categories": {}, "pay_link": "", "order_channel": None}
    save_data(data)
    await interaction.response.send_message(f"✅ تم إنشاء المتجر باسم: `{اسم}`", ephemeral=True)

@tree.command(name="اضافة_قسم", description="إضافة قسم داخل المتجر")
@app_commands.describe(اسم="اسم القسم")
async def اضافة_قسم(interaction: Interaction, اسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        return await interaction.response.send_message("❌ لم يتم إنشاء متجر لهذا السيرفر.", ephemeral=True)
    if اسم in data[gid]["categories"]:
        return await interaction.response.send_message("❌ هذا القسم موجود بالفعل.", ephemeral=True)
    data[gid]["categories"][اسم] = {}
    save_data(data)
    await interaction.response.send_message(f"✅ تم إضافة القسم `{اسم}`", ephemeral=True)

@tree.command(name="اضافة_منتج", description="إضافة منتج داخل قسم")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج", الكمية="الكمية", السعر="السعر")
async def اضافة_منتج(interaction: Interaction, القسم: str, المنتج: str, الكمية: int, السعر: float):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data or القسم not in data[gid]["categories"]:
        return await interaction.response.send_message("❌ القسم غير موجود أو لم يتم إنشاء متجر.", ephemeral=True)
    data[gid]["categories"][القسم][المنتج] = {"quantity": الكمية, "price": السعر}
    save_data(data)
    await interaction.response.send_message(f"✅ تمت إضافة المنتج `{المنتج}` إلى القسم `{القسم}`", ephemeral=True)

@tree.command(name="تحديد_روم_الطلبات", description="تحديد الروم الذي تصلك فيه الطلبات")
@app_commands.describe(channel="اختيار روم الطلبات")
async def تحديد_روم_الطلبات(interaction: Interaction, channel: discord.TextChannel):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        return await interaction.response.send_message("❌ يجب إنشاء متجر أولاً.", ephemeral=True)
    data[gid]["order_channel"] = channel.id
    save_data(data)
    await interaction.response.send_message(f"✅ تم تحديد روم الطلبات: {channel.mention}", ephemeral=True)

@tree.command(name="اضافة_رابط_دفع", description="إعداد رابط الدفع الخاص بالمتجر")
@app_commands.describe(الرابط="رابط الدفع")
async def اضافة_رابط_دفع(interaction: Interaction, الرابط: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        return await interaction.response.send_message("❌ لم يتم إعداد المتجر.", ephemeral=True)
    data[gid]["pay_link"] = الرابط
    save_data(data)
    await interaction.response.send_message("✅ تم تعيين رابط الدفع بنجاح.", ephemeral=True)

# سيتم إكمال باقي الأوامر (الطلب + تنفيذ الطلب + التقييم + الحذف) في الجزء التالي

@tree.command(name="طلب", description="طلب منتج من المتجر")
async def طلب(interaction: Interaction):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data or not data[gid]["categories"]:
        return await interaction.response.send_message("❌ لا يوجد متجر أو أقسام متاحة.", ephemeral=True)

    view = View(timeout=60)
    for category in data[gid]["categories"]:
        view.add_item(Button(label=category, style=ButtonStyle.primary, custom_id=f"cat:{category}"))
    await interaction.response.send_message("🛒 اختر القسم:", view=view, ephemeral=True)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return
    custom_id = interaction.data.get("custom_id")
    if not custom_id:
        return

    data = load_data()
    gid = str(interaction.guild_id)

    if custom_id.startswith("cat:"):
        category = custom_id.split(":")[1]
        products = data[gid]["categories"].get(category, {})
        if not products:
            return await interaction.response.send_message("❌ لا يوجد منتجات في هذا القسم.", ephemeral=True)

        view = View(timeout=60)
        for product in products:
            view.add_item(Button(label=product, style=ButtonStyle.success, custom_id=f"prod:{category}:{product}"))
        await interaction.response.send_message("📦 اختر المنتج:", view=view, ephemeral=True)

    elif custom_id.startswith("prod:"):
        _, category, product = custom_id.split(":")
        await interaction.response.send_modal(طلبModal(category, product))

class طلبModal(discord.ui.Modal, title="طلب المنتج"):
    def __init__(self, category, product):
        super().__init__()
        self.category = category
        self.product = product

        self.qty = discord.ui.TextInput(label="الكمية المطلوبة", style=discord.TextStyle.short, required=True)
        self.add_item(self.qty)

    async def on_submit(self, interaction: Interaction):
        data = load_data()
        gid = str(interaction.guild_id)
        cid = str(interaction.channel.id)

        item = data[gid]["categories"][self.category][self.product]
        price = item["price"]
        link = data[gid]["pay_link"]
        total = price * int(self.qty.value)
        store_name = data[gid]["store_name"]
        order_desc = f"🛍️ الطلب من متجر: **{store_name}**\nالقسم: {self.category}\nالمنتج: {self.product}\nالكمية: {self.qty.value}\nالسعر الإجمالي: {total} ريال"

        embed = Embed(title="📦 فاتورتك", description=order_desc, color=0x00b0f4)
        embed.add_field(name="رابط الدفع", value=link if link else "❌ لم يتم تعيين رابط الدفع", inline=False)
        await interaction.user.send(embed=embed)

        # التقييم
        view = View()
        view.add_item(Button(label="⭐", style=ButtonStyle.secondary, custom_id="rate:1"))
        view.add_item(Button(label="⭐⭐", style=ButtonStyle.secondary, custom_id="rate:2"))
        view.add_item(Button(label="⭐⭐⭐", style=ButtonStyle.secondary, custom_id="rate:3"))
        view.add_item(Button(label="⭐⭐⭐⭐", style=ButtonStyle.secondary, custom_id="rate:4"))
        view.add_item(Button(label="⭐⭐⭐⭐⭐", style=ButtonStyle.secondary, custom_id="rate:5"))
        await interaction.user.send("يرجى تقييم طلبك:", view=view)

        # إرسال الطلب لروم الطلبات
        order_room_id = data[gid]["order_channel"]
        if order_room_id:
            ch = bot.get_channel(order_room_id)
            if ch:
                await ch.send(f"📥 طلب جديد:
{order_desc}
🧾 العميل: <@{interaction.user.id}>")

        await interaction.response.send_message("✅ تم إرسال الطلب وفاتورتك في الخاص.", ephemeral=True)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id", "")
        if custom_id.startswith("rate:"):
            rating = custom_id.split(":")[1]
            await interaction.response.send_message("✅ شكرًا لتقييمك!", ephemeral=True)

            # إرسال التقييم لروم الطلبات
            data = load_data()
            gid = str(interaction.guild_id)
            room_id = data[gid]["order_channel"]
            if room_id:
                ch = bot.get_channel(room_id)
                if ch:
                    await ch.send(f"⭐ تقييم جديد من <@{interaction.user.id}>: {rating}/5")

# أوامر الحذف
@tree.command(name="حذف_متجر", description="حذف متجر السيرفر بالكامل")
async def حذف_متجر(interaction: Interaction):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data:
        del data[gid]
        save_data(data)
        return await interaction.response.send_message("✅ تم حذف المتجر.", ephemeral=True)
    await interaction.response.send_message("❌ لا يوجد متجر لحذفه.", ephemeral=True)

@tree.command(name="حذف_قسم", description="حذف قسم معين")
@app_commands.describe(اسم="اسم القسم")
async def حذف_قسم(interaction: Interaction, اسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data and اسم in data[gid]["categories"]:
        del data[gid]["categories"][اسم]
        save_data(data)
        return await interaction.response.send_message(f"✅ تم حذف القسم `{اسم}`", ephemeral=True)
    await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)

@tree.command(name="حذف_منتج", description="حذف منتج من قسم")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج")
async def حذف_منتج(interaction: Interaction, القسم: str, المنتج: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data and القسم in data[gid]["categories"] and المنتج in data[gid]["categories"][القسم]:
        del data[gid]["categories"][القسم][المنتج]
        save_data(data)
        return await interaction.response.send_message(f"✅ تم حذف المنتج `{المنتج}` من القسم `{القسم}`", ephemeral=True)
    await interaction.response.send_message("❌ لم يتم العثور على المنتج.", ephemeral=True)

@tree.command(name="حذف_رابط_دفع", description="حذف رابط الدفع")
async def حذف_رابط_دفع(interaction: Interaction):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data:
        data[gid]["pay_link"] = ""
        save_data(data)
        return await interaction.response.send_message("✅ تم حذف رابط الدفع.", ephemeral=True)
    await interaction.response.send_message("❌ لم يتم إعداد المتجر.", ephemeral=True)

bot.run(os.getenv("TOKEN"))
