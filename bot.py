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

# تعديل المودال لإضافة أزرار تأكيد وإلغاء
class QuantityModal(ui.Modal, title="🔢 أدخل الكمية"):
    الكمية = ui.TextInput(label="الكمية", placeholder="مثلاً: 2", required=True)

    def __init__(self, القسم, المنتج, interaction):
        super().__init__()
        self.القسم = القسم
        self.المنتج = المنتج
        self.original_interaction = interaction

    async def on_submit(self, interaction: Interaction):
        try:
            الكمية = int(self.كمية.value)
        except ValueError:
            await interaction.response.send_message("❌ أدخل رقمًا صحيحًا.", ephemeral=True)
            return

        data = load_data()
        gid = str(interaction.guild_id)
        info = data[gid]
        المنتج = info["categories"][self.القسم][self.المنتج]
        السعر_الإجمالي = الكمية * المنتج["price"]

        embed = Embed(title=f"🧾 فاتورة الشراء من {info['store_name']}", color=0x00ff00)
        embed.add_field(name="📦 المنتج", value=self.المنتج, inline=False)
        embed.add_field(name="📁 القسم", value=self.القسم, inline=False)
        embed.add_field(name="🔢 الكمية", value=str(الكمية), inline=True)
        embed.add_field(name="💰 السعر الإجمالي", value=f"{السعر_الإجمالي} ريال", inline=True)
        embed.add_field(name="💳 الدفع", value=info["payment_link"] or "لا يوجد رابط دفع", inline=False)

        class تأكيد_الطلب(ui.View):
            def __init__(self):
                super().__init__()
                self.value = None

            @ui.button(label="✅ تأكيد الطلب", style=ButtonStyle.success)
            async def confirm(self, interaction: Interaction, button: ui.Button):
                await interaction.response.send_message("✅ تم تأكيد الطلب! ستصلك الفاتورة في الخاص.", ephemeral=True)
                await interaction.user.send(embed=embed)
                order_channel = bot.get_channel(info["order_channel"])
                if order_channel:
                    await order_channel.send(f"🛒 طلب جديد من {interaction.user.mention}\n📦 المنتج: {self.المنتج}\n📁 القسم: {self.القسم}\n🔢 الكمية: {الكمية}\n💰 السعر الإجمالي: {السعر_الإجمالي} ريال")

            @ui.button(label="❌ إلغاء الطلب", style=ButtonStyle.danger)
            async def cancel(self, interaction: Interaction, button: ui.Button):
                await interaction.response.send_message("❌ تم إلغاء الطلب.", ephemeral=True)

        await interaction.response.send_message("📋 تأكيد الطلب:", view=تأكيد_الطلب(), ephemeral=True)

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
            super().__init__(timeout=None)
            for القسم in الأقسام:
                self.add_item(self.قسمButton(القسم))

        class قسمButton(ui.Button):
            def __init__(self, القسم):
                super().__init__(label=القسم, style=ButtonStyle.secondary)
                self.القسم = القسم

            async def callback(inner_self, interaction: Interaction):
                المنتجات = list(data[gid]["categories"][inner_self.القسم].keys())
                if not المنتجات:
                    await interaction.response.send_message("❌ لا توجد منتجات في هذا القسم.", ephemeral=True)
                    return

                class اختيارمنتج(ui.View):
                    def __init__(self):
                        super().__init__(timeout=None)
                        for منتج in المنتجات:
                            self.add_item(self.منتجButton(منتج))
                        self.add_item(self.رجوعButton())

                    class منتجButton(ui.Button):
                        def __init__(self, المنتج):
                            super().__init__(label=المنتج, style=ButtonStyle.primary)
                            self.المنتج = المنتج

                        async def callback(button_self, interaction: Interaction):
                            await interaction.response.send_modal(QuantityModal(inner_self.القسم, button_self.المنتج, interaction))

                    class رجوعButton(ui.Button):
                        def __init__(self):
                            super().__init__(label="🔙 رجوع", style=ButtonStyle.danger)

                        async def callback(self, interaction: Interaction):
                            await طلب(interaction)

                await interaction.response.send_message("اختر المنتج:", view=اختيارمنتج(), ephemeral=True)

    await interaction.response.send_message("اختر القسم:", view=اختيارالقسم(), ephemeral=True)

# تشغيل البوت و Keep Alive
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل"

Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

bot.run(os.getenv("TOKEN"))
