import discord
from discord.ext import commands
from discord import app_commands
import os
import json
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = False
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# تخزين البيانات
if not os.path.exists("data.json"):
    with open("data.json", "w") as f:
        json.dump({}, f)

def load_data():
    with open("data.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# إنشاء متجر
@tree.command(name="إنشاء_متجر")
@app_commands.describe(الاسم="اسم المتجر")
async def create_store(interaction: discord.Interaction, الاسم: str):
    data = load_data()
    data[str(interaction.guild_id)] = {"store_name": الاسم, "categories": {}, "payment_link": "", "order_channel": None}
    save_data(data)
    embed = discord.Embed(title="✅ تم إنشاء المتجر", description=f"اسم المتجر: **{الاسم}**", color=0x00ff00)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# إضافة قسم
@tree.command(name="إضافة_قسم")
@app_commands.describe(الاسم="اسم القسم")
async def add_category(interaction: discord.Interaction, الاسم: str):
    data = load_data()
    store = data.get(str(interaction.guild_id))
    if not store:
        await interaction.response.send_message("❌ لم يتم إنشاء المتجر بعد.", ephemeral=True)
        return
    store["categories"][الاسم] = {}
    save_data(data)
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم إضافة القسم", description=الاسم, color=0x00ff00), ephemeral=True)

# إضافة منتج
@tree.command(name="إضافة_منتج")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج", الكمية="الكمية المتوفرة", السعر="سعر المنتج")
async def add_product(interaction: discord.Interaction, القسم: str, المنتج: str, الكمية: int, السعر: float):
    data = load_data()
    store = data.get(str(interaction.guild_id))
    if not store or القسم not in store["categories"]:
        await interaction.response.send_message("❌ القسم غير موجود أو المتجر غير مُنشأ.", ephemeral=True)
        return
    store["categories"][القسم][المنتج] = {"الكمية": الكمية, "السعر": السعر}
    save_data(data)
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم إضافة المنتج", description=f"{المنتج} - {السعر}$ (x{الكمية})", color=0x00ff00), ephemeral=True)

# تحديد رابط الدفع
@tree.command(name="رابط_الدفع")
@app_commands.describe(الرابط="رابط الدفع")
async def set_payment(interaction: discord.Interaction, الرابط: str):
    data = load_data()
    if str(interaction.guild_id) not in data:
        await interaction.response.send_message("❌ لم يتم إنشاء المتجر بعد.", ephemeral=True)
        return
    data[str(interaction.guild_id)]["payment_link"] = الرابط
    save_data(data)
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم تحديد رابط الدفع", description=رابط, color=0x00ff00), ephemeral=True)

# تحديد روم الطلبات
@tree.command(name="تحديد_روم_الطلبات")
@app_commands.describe(الروم="الروم")
async def set_order_channel(interaction: discord.Interaction, الروم: discord.TextChannel):
    data = load_data()
    if str(interaction.guild_id) not in data:
        await interaction.response.send_message("❌ لم يتم إنشاء المتجر بعد.", ephemeral=True)
        return
    data[str(interaction.guild_id)]["order_channel"] = الروم.id
    save_data(data)
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم تحديد روم الطلبات", description=روم.mention, color=0x00ff00), ephemeral=True)

# تنفيذ الطلب
class QuantityModal(discord.ui.Modal, title="أدخل الكمية"):
    الكمية = discord.ui.TextInput(label="الكمية", placeholder="أدخل عدد الكمية المطلوبة")

    def __init__(self, interaction, القسم, المنتج):
        super().__init__()
        self.interaction = interaction
        self.القسم = القسم
        self.المنتج = المنتج

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        store = data[str(interaction.guild_id)]
        المنتج_بيانات = store["categories"][self.القسم][self.المنتج]
        السعر = المنتج_بيانات["السعر"] * int(self.الكمية.value)
        رابط = store["payment_link"]
        قناة_الطلبات = store.get("order_channel")

        embed = discord.Embed(title="🧾 فاتورتك", description=f"**{store['store_name']}**\n\n**المنتج:** {self.المنتج}\n**القسم:** {self.القسم}\n**الكمية:** {self.الكمية.value}\n**السعر الكلي:** {السعر}$", color=0x3498db)
        embed.add_field(name="رابط الدفع", value=رابط, inline=False)
        await interaction.user.send(embed=embed)

        if قناة_الطلبات:
            channel = interaction.client.get_channel(قناة_الطلبات)
            if channel:
                await channel.send(f"📦 طلب جديد من <@{interaction.user.id}>\n**القسم:** {self.القسم}\n**المنتج:** {self.المنتج}\n**الكمية:** {self.الكمية.value}")

        await interaction.response.send_message("✅ تم تنفيذ الطلب!", ephemeral=True)

@tree.command(name="طلب")
async def طلب(interaction: discord.Interaction):
    data = load_data()
    store = data.get(str(interaction.guild_id))
    if not store:
        await interaction.response.send_message("❌ المتجر غير موجود.", ephemeral=True)
        return

    الأقسام = list(store["categories"].keys())

    class SectionView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)

            for القسم in الأقسام:
                self.add_item(discord.ui.Button(label=القسم, style=discord.ButtonStyle.primary, custom_id=القسم))

        @discord.ui.button(label="إلغاء", style=discord.ButtonStyle.danger)
        async def cancel(self, interaction2: discord.Interaction, button: discord.ui.Button):
            await interaction2.response.send_message("❌ تم إلغاء الطلب.", ephemeral=True)
            self.stop()

        async def interaction_check(self, i: discord.Interaction) -> bool:
            return i.user.id == interaction.user.id

        async def on_timeout(self):
            try:
                await interaction.followup.send("⏰ انتهى الوقت.", ephemeral=True)
            except:
                pass

        async def on_error(self, interaction, error, item):
            print("Error in SectionView", error)

        async def on_submit(self, interaction2):
            القسم = interaction2.data['custom_id']
            المنتجات = list(store["categories"][القسم].keys())

            class ProductView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=60)
                    for منتج in المنتجات:
                        self.add_item(discord.ui.Button(label=منتج, style=discord.ButtonStyle.secondary, custom_id=منتج))

                async def interaction_check(self, i: discord.Interaction) -> bool:
                    return i.user.id == interaction.user.id

                async def on_timeout(self):
                    try:
                        await interaction.followup.send("⏰ انتهى الوقت.", ephemeral=True)
                    except:
                        pass

                async def on_submit(self, interaction3):
                    المنتج = interaction3.data['custom_id']
                    await interaction3.response.send_modal(QuantityModal(interaction3, القسم, المنتج))

            await interaction2.response.send_message("اختر المنتج:", view=ProductView(), ephemeral=True)

    await interaction.response.send_message("اختر القسم:", view=SectionView(), ephemeral=True)

keep_alive()
bot.run(os.getenv("TOKEN"))

