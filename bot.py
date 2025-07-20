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

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ تم تسجيل {len(bot.tree.get_commands())} أمر سلاش")

# أوامر إعداد المتجر
@bot.tree.command(name="انشاء_متجر")
@app_commands.describe(اسم_المتجر="اسم المتجر الخاص بك")
async def انشاء_متجر(interaction: Interaction, اسم_المتجر: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data:
        await interaction.response.send_message("⚠️ المتجر موجود بالفعل.", ephemeral=True)
        return
    data[gid] = {"store_name": اسم_المتجر, "categories": {}, "payment_link": "", "order_channel": None, "client_order_channel": None}
    save_data(data)
    await interaction.response.send_message(f"✅ تم إنشاء المتجر: {اسم_المتجر}", ephemeral=True)

@bot.tree.command(name="روم_التاجر")
@app_commands.describe(الروم="حدد الروم الذي يستقبل طلبات العملاء")
async def روم_التاجر(interaction: Interaction, الروم: discord.TextChannel):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ يجب أولاً إنشاء متجر.", ephemeral=True)
        return
    data[gid]["order_channel"] = الروم.id
    save_data(data)
    await interaction.response.send_message(f"✅ تم تحديد روم التاجر: {الروم.mention}", ephemeral=True)

@bot.tree.command(name="روم_الطلبات")
@app_commands.describe(الروم="حدد الروم الذي يستقبل أوامر العملاء")
async def روم_الطلبات(interaction: Interaction, الروم: discord.TextChannel):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ يجب أولاً إنشاء متجر.", ephemeral=True)
        return
    data[gid]["client_order_channel"] = الروم.id
    save_data(data)
    await interaction.response.send_message(f"✅ تم تحديد روم الطلبات للعملاء: {الروم.mention}", ephemeral=True)

@bot.tree.command(name="اضافة_قسم")
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

@bot.tree.command(name="حذف_قسم")
@app_commands.describe(الاسم="اسم القسم المراد حذفه")
async def حذف_قسم(interaction: Interaction, الاسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data and الاسم in data[gid]["categories"]:
        del data[gid]["categories"][الاسم]
        save_data(data)
        await interaction.response.send_message(f"✅ تم حذف القسم: {الاسم}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)

@bot.tree.command(name="اضافة_منتج")
@app_commands.describe(القسم="القسم التابع له المنتج", الاسم="اسم المنتج", الكمية="عدد القطع", السعر="سعر المنتج")
async def اضافة_منتج(interaction: Interaction, القسم: str, الاسم: str, الكمية: int, السعر: int):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data or القسم not in data[gid]["categories"]:
        await interaction.response.send_message("❌ تأكد من وجود المتجر والقسم.", ephemeral=True)
        return
    data[gid]["categories"][القسم][الاسم] = {"quantity": الكمية, "price": السعر}
    save_data(data)
    await interaction.response.send_message(f"✅ تم إضافة المنتج: {الاسم} لقسم {القسم}", ephemeral=True)

@bot.tree.command(name="حذف_منتج")
@app_commands.describe(القسم="القسم الذي فيه المنتج", الاسم="اسم المنتج المراد حذفه")
async def حذف_منتج(interaction: Interaction, القسم: str, الاسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data and القسم in data[gid]["categories"] and الاسم in data[gid]["categories"][القسم]:
        del data[gid]["categories"][القسم][الاسم]
        save_data(data)
        await interaction.response.send_message(f"✅ تم حذف المنتج: {الاسم} من قسم {القسم}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ المنتج غير موجود.", ephemeral=True)

@bot.tree.command(name="رابط_الدفع")
@app_commands.describe(الرابط="أدخل رابط الدفع")
async def رابط_الدفع(interaction: Interaction, الرابط: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ يجب إنشاء متجر أولاً.", ephemeral=True)
        return
    data[gid]["payment_link"] = الرابط
    save_data(data)
    await interaction.response.send_message("✅ تم حفظ رابط الدفع", ephemeral=True)

class QuantityModal(ui.Modal, title="🔢 أدخل الكمية"):
    الكمية = ui.TextInput(label="الكمية", placeholder="مثلاً: 2", required=True)

    def __init__(self, القسم, المنتج, interaction):
        super().__init__()
        self.القسم = القسم
        self.المنتج = المنتج
        self.original_interaction = interaction

    async def on_submit(self, interaction: Interaction):
        data = load_data()
        gid = str(interaction.guild_id)
        info = data[gid]
        المنتج = info["categories"][self.القسم][self.المنتج]
        الكمية = int(self.كمية.value)
        السعر_الإجمالي = الكمية * المنتج["price"]

        embed = Embed(title=f"🧾 فاتورة الشراء من {info['store_name']}", color=0x00ff00)
        embed.add_field(name="📦 المنتج", value=self.المنتج, inline=False)
        embed.add_field(name="📁 القسم", value=self.القسم, inline=False)
        embed.add_field(name="🔢 الكمية", value=str(الكمية), inline=True)
        embed.add_field(name="💰 السعر الإجمالي", value=f"{السعر_الإجمالي} ريال", inline=True)
        embed.add_field(name="💳 الدفع", value=info["payment_link"] or "لا يوجد رابط دفع", inline=False)

        view = ui.View()

        class تقييم(ui.View):
            def __init__(self, الطلب_embed):
                super().__init__()
                self.embed = الطلب_embed

            @ui.button(label="⭐", style=ButtonStyle.success)
            async def rate(self, interaction: Interaction, button: ui.Button):
                await interaction.response.send_message("✅ شكرًا لتقييمك!", ephemeral=True)
                order_channel = bot.get_channel(data[gid]["order_channel"])
                if order_channel:
                    await order_channel.send(f"📥 تقييم جديد:", embed=self.embed)

        await interaction.user.send(embed=embed, view=تقييم(embed))

        order_channel = bot.get_channel(data[gid]["order_channel"])
        if order_channel:
            await order_channel.send(f"🛒 طلب جديد من {interaction.user.mention}\n📦 المنتج: {self.المنتج}\n📁 القسم: {self.القسم}\n🔢 الكمية: {الكمية}\n💰 السعر الإجمالي: {السعر_الإجمالي} ريال")

        await interaction.response.send_message("✅ تم إرسال الفاتورة في الخاص", ephemeral=True)

@bot.tree.command(name="طلب")
async def طلب(interaction: Interaction):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("❌ لم يتم إعداد متجر بعد.", ephemeral=True)
        return

    الأقسام = list(data[gid]["categories"].keys())
    if not الأقسام:
        await interaction.response.send_message("❌ لا يوجد أقسام متاحة حاليًا.", ephemeral=True)
        return

    class اختيارالقسم(ui.View):
        def __init__(self):
            super().__init__()
            for القسم in الأقسام:
                self.add_item(ui.Button(label=القسم, style=ButtonStyle.secondary, custom_id=القسم))

        async def interaction_check(self, interaction_: Interaction) -> bool:
            return interaction.user == interaction_.user

        @ui.button(label="إلغاء", style=ButtonStyle.danger)
        async def cancel(self, interaction: Interaction, button: ui.Button):
            await interaction.response.send_message("تم الإلغاء.", ephemeral=True)

        async def on_timeout(self):
            for child in self.children:
                child.disabled = True

        async def on_error(self, interaction: Interaction, error: Exception, item):
            await interaction.response.send_message("حدث خطأ.", ephemeral=True)

        async def on_button_click(self, interaction: Interaction):
            القسم = interaction.data["custom_id"]
            المنتجات = list(data[gid]["categories"][القسم].keys())

            class اختيارمنتج(ui.View):
                def __init__(self):
                    super().__init__()
                    for منتج in المنتجات:
                        self.add_item(ui.Button(label=منتج, style=ButtonStyle.primary, custom_id=منتج))

                async def on_button_click(self, interaction: Interaction):
                    await interaction.response.send_modal(QuantityModal(القسم, interaction.data["custom_id"], interaction))

            await interaction.response.send_message("اختر المنتج:", view=اختيارمنتج(), ephemeral=True)

    await interaction.response.send_message("اختر القسم:", view=اختيارالقسم(), ephemeral=True)

# تشغيل البوت و Keep Alive
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل"

Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

bot.run(os.getenv("TOKEN"))
