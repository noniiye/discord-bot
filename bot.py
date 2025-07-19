import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction, Embed
import json, os
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

data_file = "store_data.json"
if not os.path.exists(data_file):
    with open(data_file, "w") as f:
        json.dump({}, f)

def load_data():
    with open(data_file, "r") as f:
        return json.load(f)

def save_data(data):
    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)

# Flask server to keep the bot alive on Render
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

@bot.event
async def on_ready():
    Thread(target=run_flask).start()
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

# === أوامر المتجر ===

@tree.command(name="انشاء_متجر", description="انشاء متجر باسم مخصص")
@app_commands.describe(اسم_المتجر="اكتب اسم المتجر")
async def create_store(interaction: Interaction, اسم_المتجر: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data:
        await interaction.response.send_message("⚠️ المتجر موجود مسبقًا.", ephemeral=True)
        return
    data[gid] = {
        "store_name": اسم_المتجر,
        "categories": {},
        "payment_link": "",
        "order_channel": None
    }
    save_data(data)
    await interaction.response.send_message(f"✅ تم إنشاء المتجر باسم **{اسم_المتجر}**", ephemeral=True)

@tree.command(name="تحديد_روم_الطلبات", description="حدد روم استقبال الطلبات")
async def set_order_channel(interaction: Interaction, channel: discord.TextChannel):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("⚠️ يجب إنشاء متجر أولًا.", ephemeral=True)
        return
    data[gid]["order_channel"] = channel.id
    save_data(data)
    await interaction.response.send_message(f"✅ تم تحديد روم الطلبات: {channel.mention}", ephemeral=True)

@tree.command(name="اضافة_قسم", description="اضافة قسم جديد للمتجر")
async def add_category(interaction: Interaction, اسم_القسم: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("⚠️ يجب إنشاء متجر أولًا.", ephemeral=True)
        return
    data[gid]["categories"][اسم_القسم] = {}
    save_data(data)
    await interaction.response.send_message(f"✅ تم إضافة القسم: {اسم_القسم}", ephemeral=True)

@tree.command(name="اضافة_منتج", description="اضافة منتج لقسم محدد")
async def add_product(interaction: Interaction, اسم_القسم: str, اسم_المنتج: str, الكمية: int, السعر: int):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data or اسم_القسم not in data[gid]["categories"]:
        await interaction.response.send_message("⚠️ المتجر أو القسم غير موجود.", ephemeral=True)
        return
    data[gid]["categories"][اسم_القسم][اسم_المنتج] = {
        "quantity": الكمية,
        "price": السعر
    }
    save_data(data)
    await interaction.response.send_message(f"✅ تم إضافة المنتج **{اسم_المنتج}** إلى القسم **{اسم_القسم}**", ephemeral=True)

@tree.command(name="رابط_الدفع", description="تحديد رابط الدفع للفاتورة")
async def set_payment_link(interaction: Interaction, الرابط: str):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data:
        await interaction.response.send_message("⚠️ يجب إنشاء متجر أولًا.", ephemeral=True)
        return
    data[gid]["payment_link"] = الرابط
    save_data(data)
    await interaction.response.send_message(f"✅ تم تعيين رابط الدفع: {الرابط}", ephemeral=True)

@tree.command(name="حذف_متجر", description="حذف المتجر بالكامل")
async def delete_store(interaction: Interaction):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid in data:
        del data[gid]
        save_data(data)
        await interaction.response.send_message("✅ تم حذف المتجر بنجاح.", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ لا يوجد متجر لحذفه.", ephemeral=True)

@tree.command(name="طلب", description="تنفيذ طلب منتج من المتجر")
async def order(interaction: Interaction):
    data = load_data()
    gid = str(interaction.guild_id)
    if gid not in data or not data[gid]["categories"]:
        await interaction.response.send_message("⚠️ لا يوجد أقسام أو منتجات للطلب.", ephemeral=True)
        return

    class CategorySelect(ui.Select):
        def __init__(self):
            options = [discord.SelectOption(label=cat) for cat in data[gid]["categories"]]
            super().__init__(placeholder="اختر القسم", options=options)

        async def callback(self, interaction2: Interaction):
            category = self.values[0]
            products = data[gid]["categories"][category]
            if not products:
                await interaction2.response.send_message("⚠️ لا يوجد منتجات في هذا القسم.", ephemeral=True)
                return

            class ProductSelect(ui.Select):
                def __init__(self):
                    options = [discord.SelectOption(label=p) for p in products]
                    super().__init__(placeholder="اختر المنتج", options=options)

                async def callback(self, interaction3: Interaction):
                    product = self.values[0]

                    class QuantityModal(ui.Modal, title="الكمية المطلوبة"):
                        qty = ui.TextInput(label="اكتب الكمية", required=True)

                        async def on_submit(self, interaction4: Interaction):
                            quantity = int(self.qty.value)
                            info = data[gid]["categories"][category][product]
                            total_price = info["price"] * quantity
                            store_name = data[gid]["store_name"]
                            invoice = Embed(title="فاتورتك", description=f"**{store_name}**
🛒 المنتج: {product}
📦 الكمية: {quantity}
💰 السعر: {total_price}
🔗 الدفع: {data[gid]['payment_link']}", color=0x00ff00)
                            await interaction4.user.send(embed=invoice)
                            await interaction4.response.send_message("📩 تم إرسال الفاتورة في الخاص.", ephemeral=True)

                            order_channel = bot.get_channel(data[gid]["order_channel"])
                            if order_channel:
                                await order_channel.send(f"📥 طلب جديد من <@{interaction4.user.id}>:
🛍️ القسم: {category}
📦 المنتج: {product}
📦 الكمية: {quantity}")

                    await interaction3.response.send_modal(QuantityModal())

            view2 = ui.View()
            view2.add_item(ProductSelect())
            await interaction2.response.send_message("اختر المنتج:", view=view2, ephemeral=True)

    view = ui.View()
    view.add_item(CategorySelect())
    await interaction.response.send_message("اختر القسم:", view=view, ephemeral=True)

bot.run(os.getenv("TOKEN"))
