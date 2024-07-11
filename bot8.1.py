from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, View
import logging
from secret import DB_URL, TOKEN

CHANNEL = "general" # ✅・identify
# TARGET_CHANNEL_ID = 1258359384648450088# Show Embed

# ตั้งค่า logging
logging.basicConfig(level=logging.DEBUG)

# ตั้งค่า MongoDB client
client = MongoClient(DB)  # แก้ไขตามการตั้งค่า MongoDB 
db = client['cpe_discord']  # ชื่อฐานข้อมูล
collection = db['students']  # ชื่อคอลเล็กชัน

def check_server_status():
    logging.debug("Scanning DB server health")
    try:
        info = client.server_info() # Forces a call.
        logging.debug(info)
    except ConnectionFailure:
        logging.error("server is down.")
    logging.debug("Finish Scanning")

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

class RegistrationModal(discord.ui.Modal, title='นักศึกษา CPE ลงทะเบียน'):
    def __init__(self):
        super().__init__(title="นักศึกษา CPE ลงทะเบียน")
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
            
            if student_id.startswith("67"):
                await interaction.response.send_message(f"❗ นักศึกษาปี 67 รหัสนักศึกษา: {student_id} กรุณากดปุ่มลงทะเบียน", ephemeral=True, view=RegisterButton(student_id))
                return
            
            batch = f"25{student_id[:2]}"  
            batchRole = student_id[:2]
            logging.debug(f"Checking database for student ID: {student_id} and batch: {batch}")
            student = collection.find_one({"id": student_id})


            if student: # exits
                fullname = student["name"]
                await interaction.response.send_message(f"✅ ยืนยันตัวสำเร็จ ยินดีต้อนรับ: {fullname}", ephemeral=True)

                # สร้าง embed
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
                target_channel = bot.get_channel(1258359347189383260)  # ใส่ ID Channel ที่ต้องการ
                if target_channel:
                    await target_channel.send(embed=embed, view=VerifyButtonView())
                    
                # เพิ่ม Role ตามปีการศึกษา
                guild = interaction.guild
                role_name = f"{batchRole}"
                role = discord.utils.get(guild.roles, name=role_name)

                if role:
                    await interaction.user.add_roles(role)
                    logging.info(f"Added role {role_name} to {interaction.user.name}")
                else:
                    logging.warning(f"Role {role_name} not found")

            else:
                await interaction.response.send_message(f"❗ไม่พบรหัสนักศึกษา: {student_id} กรุณาลงทะเบียนยืนยันตัวตน", ephemeral=True, view=RegisterButton(student_id))
        except Exception as e:
            logging.error(f"Error processing registration: {e}")
            if not interaction.response.is_done():
                try:
                    await interaction.response.send_message("❌ เกิดข้อผิดพลาดในการยืนยันตัวตน", ephemeral=True)
                except discord.errors.NotFound:
                    logging.error("Interaction not found, cannot send response.")

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
            placeholder="ใส่ชื่อจริง (ตัวอย่างเช่น: นายเอกภพ)"
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
            batchRole = student_id[:2]
            first_name = self.first_name.value
            last_name = self.last_name.value
            fullname = f"{first_name} {last_name}"

            # ตรวจสอบว่ารหัสนักศึกษาไม่ซ้ำกัน
            existing_student = collection.find_one({"id": student_id})
            logging.warning('here' + str(existing_student))
            if existing_student:
                await interaction.response.send_message(f"❗รหัสนักศึกษา: {student_id} ถูกใช้แล้ว กรุณาใช้รหัสนักศึกษาอื่น", ephemeral=True)
                return

            new_entry = {
                "id": student_id,
                "name": fullname,
                "batch": batch
            }

            collection.insert_one(new_entry)

            
            embed = discord.Embed(title="**ลงทะเบียนสำเร็จ**", color=discord.Color.green())
            embed.add_field(name="ชื่อ - นามสกุล :", value=fullname, inline=True)
            embed.add_field(name="รหัสนักศึกษา :", value=student_id, inline=False)
            embed.add_field(name="ปีการศึกษา :", value=batch, inline=False)  # ใช้ batch ที่ได้จากสองตัวแรกของรหัสนักศึกษา
            embed.add_field(name=f"Discord ID : {interaction.user.display_name}#{interaction.user.discriminator}", value=interaction.user.mention, inline=True)
            embed.add_field(name="RawID :", value=str(interaction.user.id), inline=False)
            
            # ตรวจสอบว่าผู้ใช้มีรูปประจำตัวหรือไม่
            if interaction.user.avatar:
                embed.set_thumbnail(url=interaction.user.avatar.url)
                
            embed.set_footer(text="Powered By CPE Discord bot")
            
            target_channel = bot.get_channel(1258359384648450088)  # ใส่ Channel ID สำหรับลงทะเบียนใหม่
            target_channel67 = bot.get_channel(1259360958837555242)

            # Send embed to target_channel67 if student ID starts with "67"
            if student_id.startswith("67"):
                if target_channel67:
                    await target_channel67.send(embed=embed, view=VerifyButtonView())
            else:
                if target_channel:
                    await target_channel.send(embed=embed, view=VerifyButtonView())
            

            await interaction.response.send_message(f"ลงทะเบียนรหัสนักศึกษา: {student_id} สำเร็จ ✅\nยินดีต้อนรับ: {fullname}", ephemeral=True)
            
            # เพิ่ม Role ตามปีการศึกษา
            guild = interaction.guild
            role_name = f"{batchRole}"
            role = discord.utils.get(guild.roles, name=role_name)

            if role:
                await interaction.user.add_roles(role)
                logging.info(f"Added role {role_name} to {interaction.user.name}")
            else:
                logging.warning(f"Role {role_name} not found")

        except Exception as e:
            logging.error(f"Error processing registration: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ เกิดข้อผิดพลาดในการลงทะเบียน", ephemeral=True)



class RegistrationView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="ยืนยันตัวตนเข้าสู่ CPE ดิสคอร์ด ✅", style=discord.ButtonStyle.green)
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        logging.debug("Verify button had clicked.")
        modal = RegistrationModal()
        await interaction.response.send_modal(modal)
        logging.debug("Modal sent.")

class VerifyButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}! Ready to send registration forms.')
    check_server_status()
    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name=CHANNEL) # ✅・identify
        if channel:
            await channel.send(view=RegistrationView())

@bot.event
async def on_guild_join(guild):
    channel = discord.utils.get(guild.text_channels, name=CHANNEL) # ✅・identify
    if channel:
        await channel.send(view=RegistrationView())
        
bot.run(TOKEN)
