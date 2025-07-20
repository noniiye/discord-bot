import discord
from discord.ext import commands
from discord import app_commands, ui
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

servers_data = {}

class ReviewButtons(ui.View):
    def __init__(self, user_id, order_desc, guild_id):
        super().__init__()
        self.user_id = user_id
        self.order_desc = order_desc
        self.guild_id = guild_id

    @ui.button(label="⭐", style=discord.ButtonStyle.primary)
    async def one_star(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_review(interaction, 1)

    @ui.button(label="⭐⭐", style=discord.ButtonStyle.primary)
    async def two_star(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_review(interaction, 2)

    @ui.button(label="⭐⭐⭐", style=discord.ButtonStyle.primary)
    async def three_star(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_review(interaction, 3)

    async def send_review(self, interaction, stars):
        await interaction.response.send_message("شكرًا لتقييمك!", ephemeral=True)
        channel_id = servers_data[self.guild_id].get("orders_channel")
        if channel_id:
            channel = bot.get_channel(channel_id)
            await channel.send(embed=discord.Embed(
                title="⭐ تقييم جديد",
                description=f"الطلب:\n{self.order_desc}\nالعميل: <@{self.user_id}>\nالتقييم: {'⭐'*stars}",
                color=discord.Color.yellow()
            ))

@tree.command(name="انشاء_متجر", description="إنشاء متجر جديد باسم معين")
@app_commands.describe(store_name="اسم المتجر")
async def انشاء_متجر(interaction: discord.Interaction, store_name: str):
    servers_data[interaction.guild_id] = {
        "store_name": store_name,
        "categories": {},
        "payment_link": "",
        "orders_channel": None
    }
    await interaction.response.send_message(embed=discord.Embed(
        title="✅ تم إنشاء المتجر",
        description=f"اسم المتجر: **{store_name}**",
        color=discord.Color.green()
    ))

@tree.command(name="تحديد_روم_الطلبات", description="تحديد الروم الذي تُرسل إليه الطلبات")
async def تحديد_روم_الطلبات(interaction: discord.Interaction, channel: discord.TextChannel):
    servers_data[interaction.guild_id]["orders_channel"] = channel.id
    await interaction.response.send_message(embed=discord.Embed(
        title="📥 تم تعيين روم الطلبات",
        description=f"{channel.mention}",
        color=discord.Color.blue()
    ))

@tree.command(name="اضافة_قسم", description="إضافة قسم جديد للمتجر")
async def اضافة_قسم(interaction: discord.Interaction, category_name: str):
    servers_data[interaction.guild_id]["categories"][category_name] = {}
    await interaction.response.send_message(embed=discord.Embed(
        title="📁 تم إضافة القسم",
        description=category_name,
        color=discord.Color.green()
    ))

@tree.command(name="اضافة_منتج", description="إضافة منتج داخل قسم")
async def اضافة_منتج(interaction: discord.Interaction, category_name: str, product_name: str, quantity: int, price: float):
    cats = servers_data[interaction.guild_id]["categories"]
    if category_name not in cats:
        await interaction.response.send_message("❌ القسم غير موجود", ephemeral=True)
        return
    cats[category_name][product_name] = {"quantity": quantity, "price": price}
    await interaction.response.send_message(embed=discord.Embed(
        title="📦 تم إضافة المنتج",
        description=f"القسم: {category_name}\nالمنتج: {product_name}\nالكمية: {quantity}\nالسعر: {price} ريال",
        color=discord.Color.green()
    ))

@tree.command(name="تحديد_رابط_الدفع", description="تحديد رابط الدفع")
async def تحديد_رابط_الدفع(interaction: discord.Interaction, link: str):
    servers_data[interaction.guild_id]["payment_link"] = link
    await interaction.response.send_message("💳 تم تعيين رابط الدفع.")

@tree.command(name="حذف_متجر", description="حذف المتجر")
async def حذف_متجر(interaction: discord.Interaction):
    servers_data.pop(interaction.guild_id, None)
    await interaction.response.send_message("🗑️ تم حذف المتجر.")

@tree.command(name="حذف_قسم", description="حذف قسم من المتجر")
async def حذف_قسم(interaction: discord.Interaction, category_name: str):
    servers_data[interaction.guild_id]["categories"].pop(category_name, None)
    await interaction.response.send_message("🗑️ تم حذف القسم.")

@tree.command(name="حذف_منتج", description="حذف منتج من قسم")
async def حذف_منتج(interaction: discord.Interaction, category_name: str, product_name: str):
    servers_data[interaction.guild_id]["categories"][category_name].pop(product_name, None)
    await interaction.response.send_message("🗑️ تم حذف المنتج.")

@tree.command(name="حذف_رابط_الدفع", description="حذف رابط الدفع")
async def حذف_رابط_الدفع(interaction: discord.Interaction):
    servers_data[interaction.guild_id]["payment_link"] = ""
    await interaction.response.send_message("🗑️ تم حذف رابط الدفع.")

class OrderView(ui.View):
    def __init__(self, guild_id, user_id):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.user_id = user_id
        self.category = None
        self.product = None
        self.add_item(self.CategorySelect(self))

    class CategorySelect(ui.Select):
        def __init__(self, parent):
            self.parent = parent
            options = [discord.SelectOption(label=cat) for cat in servers_data[parent.guild_id]["categories"].keys()]
            super().__init__(placeholder="اختر القسم", options=options)

        async def callback(self, interaction: discord.Interaction):
            self.parent.category = self.values[0]
            self.parent.clear_items()
            self.parent.add_item(OrderView.ProductSelect(self.parent))
            await interaction.response.edit_message(
                embed=discord.Embed(title="📦 اختر المنتج", color=discord.Color.blurple()),
                view=self.parent
            )

    class ProductSelect(ui.Select):
        def __init__(self, parent):
            self.parent = parent
            products = servers_data[parent.guild_id]["categories"][parent.category]
            options = [discord.SelectOption(label=prod) for prod in products.keys()]
            super().__init__(placeholder="اختر المنتج", options=options)

        async def callback(self, interaction: discord.Interaction):
            self.parent.product = self.values[0]
            self.parent.clear_items()
            self.parent.add_item(OrderView.QuantityButton(self.parent))
            await interaction.response.edit_message(
                embed=discord.Embed(title="🔢 اضغط لإدخال الكمية", color=discord.Color.blurple()),
                view=self.parent
            )

    class QuantityButton(ui.Button):
        def __init__(self, parent):
            self.parent = parent
            super().__init__(label="إدخال الكمية", style=discord.ButtonStyle.success)

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_message("من فضلك اكتب الكمية المطلوبة:", ephemeral=True)

            def check(m):
                return m.author.id == self.parent.user_id and m.channel == interaction.channel

            try:
                msg = await bot.wait_for("message", check=check, timeout=60)
                quantity = int(msg.content)

                product_data = servers_data[self.parent.guild_id]["categories"][self.parent.category][self.parent.product]
                if quantity > product_data["quantity"]:
                    await interaction.followup.send("❌ الكمية غير متوفرة.", ephemeral=True)
                    return

                product_data["quantity"] -= quantity
                desc = f"القسم: {self.parent.category}\nالمنتج: {self.parent.product}\nالكمية: {quantity}"
                orders_channel_id = servers_data[self.parent.guild_id]["orders_channel"]
                store_name = servers_data[self.parent.guild_id]["store_name"]
                payment_link = servers_data[self.parent.guild_id]["payment_link"]

                if orders_channel_id:
                    channel = bot.get_channel(orders_channel_id)
                    await channel.send(embed=discord.Embed(
                        title="📥 طلب جديد",
                        description=f"{desc}\nالعميل: <@{self.parent.user_id}>",
                        color=discord.Color.blue()
                    ))

                user = interaction.user
                embed = discord.Embed(title="💰 فاتورة الطلب", color=discord.Color.gold())
                embed.add_field(name="🛍️ المتجر", value=store_name, inline=False)
                embed.add_field(name="📦 تفاصيل الطلب", value=desc, inline=False)
                embed.add_field(name="💳 رابط الدفع", value=payment_link or "لا يوجد", inline=False)
                await user.send(embed=embed)
                await user.send("📝 كيف تقيم الطلب؟", view=ReviewButtons(user.id, desc, self.parent.guild_id))
                await interaction.followup.send("✅ تم إرسال الفاتورة والتقييم في الخاص.", ephemeral=True)

            except:
                await interaction.followup.send("❌ لم يتم تنفيذ الطلب بسبب عدم الرد.", ephemeral=True)

@tree.command(name="طلب", description="طلب منتج من المتجر")
async def طلب(interaction: discord.Interaction):
    await interaction.response.send_message("📋 اختر القسم:", view=OrderView(interaction.guild_id, interaction.user.id), ephemeral=True)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ تم تسجيل الدخول: {bot.user}")

keep_alive()
bot.run(os.getenv("TOKEN"))
