from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, View
from config import DB_URL, TOKEN, PROFILE_CHANNEL
from untils import check_server_status

client = MongoClient(DB_URL)
db = client['cpe_discord']
collection = db['students']

class RegistrationModal(discord.ui.Modal, title='นักศึกษา CPE ลงทะเบียน'):
    def __init__(self):
        super().__init__(title="นักศึกษา CPE ลงทะเบียน", timeout=None)
        self.student_id = TextInput(
            label="รหัสประจำตัวนักศึกษา",
            placeholder="ใส่รหัสประจำตัวนักศึกษา (ตัวอย่างเช่น: 6501157)",
            min_length=7,
            max_length=7
        )
        self.add_item(self.student_id)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            student_id = self.student_id.value           
            batch = f"25{student_id[:2]}"  
            batchRole = f'CPE {student_id[:2]}'
            print(f"Checking database for student ID: {student_id} and batch: {batch}")
            student = collection.find_one({"id": student_id})
            try:
                verified_status = student["verified"]
            except:
                verified_status = None
            
            if student and not verified_status:
                fullname = student["name"]
                await interaction.response.send_message(f"✅ ยืนยันตัวตนสำเร็จ! ยินดีต้อนรับ: {fullname}", ephemeral=True)

                embed = discord.Embed(title="**IDENTITY CONFIRMATION**", color=discord.Color.blue())
                embed.add_field(name="ชื่อ - นามสกุล :", value=fullname, inline=True)
                embed.add_field(name="รหัสนักศึกษา :", value=student_id, inline=False)
                embed.add_field(name="ปีการศึกษา :", value=batch, inline=False)  
                embed.add_field(name=f"Discord ID : {interaction.user.display_name}#{interaction.user.discriminator}", value=interaction.user.mention, inline=True)
                embed.add_field(name="RawID :", value=str(interaction.user.id), inline=False) 
                if interaction.user.avatar:
                    embed.set_thumbnail(url=interaction.user.avatar.url)
                embed.set_footer(text="Powered By CPE Discord bot")

                # ส่ง embed ไปยัง Channel ที่ระบุ output
                channel = await bot.fetch_channel(PROFILE_CHANNEL)
                await channel.send(embed=embed)
                    
                # เพิ่ม Role ตามปีการศึกษา
                guild = interaction.guild
                role_name = f"{batchRole}"
                role = discord.utils.get(guild.roles, name=role_name)

                if role:
                    await interaction.user.add_roles(role)
                    print(f"Added role {role_name} to {interaction.user.name}")
                    filter = {"id": student_id}
                    update = {"$set": {"verified": True}}
                    collection.update_one(student, update)
                else:
                    print(f"Role {role_name} not found")

            elif student and verified_status:
                await interaction.response.send_message(f"❗ รหัสนักศึกษา: {student_id} เคยลงทะเบียนแล้ว", ephemeral=True)
            else:
                await interaction.response.send_message(f"❗ ไม่พบรหัสนักศึกษา: {student_id} กรุณาลงทะเบียนยืนยันตัวตน", ephemeral=True, view=RegisterButton(student_id))
        except Exception as e:
            print(f"Error processing registration: {e}")
            if not interaction.response.is_done():
                try:
                    await interaction.response.send_message("❌ เกิดข้อผิดพลาดในการยืนยันตัวตน", ephemeral=True)
                except discord.errors.NotFound:
                    print("Interaction not found, cannot send response.")

class RegisterButton(discord.ui.View):
    def __init__(self, student_id=None):
        super().__init__()
        self.student_id = student_id

    @discord.ui.button(label="ลงทะเบียนยืนยันตัวตน", style=discord.ButtonStyle.primary)
    async def register(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FullRegistrationModal(self.student_id))

class FullRegistrationModal(discord.ui.Modal, title='ลงทะเบียนใหม่'):
    def __init__(self, student_id):
        super().__init__(title="ลงทะเบียนเข้าสู่ระบบ CPE Discord")
        self.student_id = student_id  # ใช้รหัสนักศึกษาจาก ฟังชันก์ RegistrationModal
        self.student_id_input = TextInput(
            label="รหัสประจำตัวนักศึกษา (ตรวจสอบให้ถูกต้อง)",
            placeholder="ใส่รหัสประจำตัวนักศึกษาใหม่หากไม่ถูกต้อง",
            default=student_id,
            min_length=7,
            max_length=7
        )
        self.first_name = TextInput(
            label="ชื่อจริง",
            placeholder="ใส่ชื่อจริงพร้อมคำนำหน้า (ตัวอย่างเช่น: นายเอกภพ)"
        )
        self.last_name = TextInput(
            label="นามสกุล",
            placeholder="ใส่นามสกุล (ตัวอย่างเช่น: เติมกระโทก)"
        )
        self.add_item(self.student_id_input)
        self.add_item(self.first_name)
        self.add_item(self.last_name)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            student_id = self.student_id_input.value
            batch = f"25{student_id[:2]}"  
            batchRole = f'CPE {student_id[:2]}'
            first_name = self.first_name.value
            last_name = self.last_name.value
            fullname = f"{first_name} {last_name}"

            # ตรวจสอบว่ารหัสนักศึกษาไม่ซ้ำกัน
            existing_student = collection.find_one({"id": student_id})
            if existing_student:
                await interaction.response.send_message(f"❗รหัสนักศึกษา: {student_id} ถูกใช้แล้ว กรุณาใช้รหัสนักศึกษาอื่น", ephemeral=True)
                return

            new_entry = {
                "id": student_id,
                "name": fullname,
                "verified": True
            }
            collection.insert_one(new_entry)

            embed = discord.Embed(title="**IDENTITY CONFIRMATION**", color=discord.Color.green())
            embed.add_field(name="ชื่อ - นามสกุล :", value=fullname, inline=True)
            embed.add_field(name="รหัสนักศึกษา :", value=student_id, inline=False)
            embed.add_field(name="ปีการศึกษา :", value=batch, inline=False)  # ใช้ batch ที่ได้จากสองตัวแรกของรหัสนักศึกษา
            embed.add_field(name=f"Discord ID : {interaction.user.display_name}#{interaction.user.discriminator}", value=interaction.user.mention, inline=True)
            embed.add_field(name="RawID :", value=str(interaction.user.id), inline=False)
            if interaction.user.avatar:
                embed.set_thumbnail(url=interaction.user.avatar.url) 
            embed.set_footer(text="Powered By CPE Discord bot")
            
            channel = await bot.fetch_channel(PROFILE_CHANNEL)
            await channel.send(embed=embed)
            
            await interaction.response.send_message(f"ลงทะเบียนรหัสนักศึกษา: {student_id} สำเร็จ ✅\nยินดีต้อนรับ: {fullname}", ephemeral=True)
            
            # เพิ่ม Role ตามปีการศึกษา
            guild = interaction.guild
            role_name = f"{batchRole}"
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await interaction.user.add_roles(role)
                print(f"Added role {role_name} to {interaction.user.name}")
            else:
                print(f"Role {role_name} not found")

        except Exception as e:
            print(f"Error processing registration: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ เกิดข้อผิดพลาดในการลงทะเบียน", ephemeral=True)

class RegistrationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="ยืนยันตัวตนเข้าสู่ CPE Rangsit", style=discord.ButtonStyle.green, custom_id='registration_view:green')
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RegistrationModal()
        await interaction.response.send_modal(modal)

class CPE_Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.messages = True
        super().__init__(command_prefix=commands.when_mentioned_or('!'), intents=intents)

    async def setup_hook(self) -> None:
        self.add_view(RegistrationView())

bot = CPE_Bot()

@bot.command()
async def show_button(ctx):
    if ctx.author.id == 954286753395638292:
        register_button = RegistrationView()
        embed=discord.Embed(title="**[ HOW TO USE REGISTRATION ]**", color=0xa40444)
        embed.set_author(name="CPE Rangsit", icon_url="https://cdn.discordapp.com/attachments/1066638063889043496/1132392746817163374/306979451_487566176743264_2534228259878049728_n.png")
        embed.add_field(name=''':white_check_mark:  __วิธีการลงทะเบียนยืนยันตัวตน__  :white_check_mark: 
        \u200b''', value="\n", inline=False)
        embed.add_field(name="",
                    value="**```กดปุ่มสีเขียวด้านล่างเพื่อกรอกข้อมูล```**\u200b\a",
                    inline=False)
        embed.add_field(name="หากมีปัญหาขัดข้องหรือไม่สามารถยืนยันตัวตนได้", value="", inline=False)
        embed.add_field(name='''โปรดติดต่อแอดมินดังต่อไปนี้
        \u200b''', value="<@854696173007929354> <@954286753395638292> <@523486356933181470>", inline=False)
        await ctx.send(embed=embed, view=register_button)
    else:
        await ctx.message.delete()
        
bot.run(TOKEN)