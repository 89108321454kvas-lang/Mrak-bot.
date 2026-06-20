import discord
from discord.ext import commands
import time
import traceback
import asyncio
import io
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  

bot = commands.Bot(command_prefix='!', intents=intents)

# ===== НАСТРОЙКИ (ЗАМЕНИ ID СВОИМИ) =====
APPLICATION_CHANNEL_ID = 1517656038080254043 # Канал для кнопки
TICKET_CHANNEL_ID = 1517656038080254043 # Канал для заявок
STAFF_ROLE_ID = 1517676531734941896      
LOG_CHANNEL_ID = 1517844036264788080     
TRIAL_ROLE_ID = 1517641157608476732      
# =========================================

class ApplicationModal(discord.ui.Modal, title='📝 Заявка в REDHELL'):
    nickname = discord.ui.TextInput(
        label='1️⃣ Игровой никнейм',
        placeholder='Введите ваш игровой ник...',
        required=True,
        max_length=50
    )
    
    game_level = discord.ui.TextInput(
        label='2️⃣ Уровень игры',
        placeholder='Ваш уровень в игре...',
        required=True,
        max_length=50
    )
    
    families = discord.ui.TextInput(
        label='3️⃣ Семьи и причины ухода',
        placeholder='Семьи и причины ухода...',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=500
    )
    
    ooc_name = discord.ui.TextInput(
        label='4️⃣ Имя ООС',
        placeholder='Ваше имя в реальной жизни...',
        required=True,
        max_length=50
    )
    
    ooc_age = discord.ui.TextInput(
        label='5️⃣ Возраст ООС',
        placeholder='Ваш возраст...',
        required=True,
        max_length=3
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            if not self.nickname.value.strip() or not self.game_level.value.strip() or \
               not self.families.value.strip() or not self.ooc_name.value.strip() or \
               not self.ooc_age.value.strip():
                await interaction.followup.send(
                    '❌ Все поля должны быть заполнены!',
                    ephemeral=True
                )
                return
            
            try:
                age_int = int(self.ooc_age.value)
                if age_int < 1 or age_int > 120:
                    await interaction.followup.send(
                        '❌ Возраст должен быть от 1 до 120 лет!',
                        ephemeral=True
                    )
                    return
            except ValueError:
                await interaction.followup.send(
                    '❌ Возраст должен быть числом!',
                    ephemeral=True
                )
                return
            
            print(f'📝 Новая заявка от {interaction.user}:')
            print(f' Ник: {self.nickname.value}')
            print(f' Уровень: {self.game_level.value}')
            print(f' Имя ООС: {self.ooc_name.value}')
            print(f' Возраст ООС: {self.ooc_age.value}')
            
            ticket_channel = interaction.guild.get_channel(TICKET_CHANNEL_ID)
            if not ticket_channel:
                await interaction.followup.send(
                    '❌ Канал для заявок не найден! Обратитесь к администрации.',
                    ephemeral=True
                )
                return
            
            application_data = {
                'user': interaction.user,
                'nickname': self.nickname.value,
                'game_level': self.game_level.value,
                'families': self.families.value,
                'ooc_name': self.ooc_name.value,
                'ooc_age': self.ooc_age.value
            }
            
            embed = discord.Embed(
                title='📋 Новая заявка в REDHELL',
                description=(
                    f'**Заявитель:** {interaction.user.mention}\n'
                    f'**Discord-тег:** {interaction.user}\n\n'
                    f'**1️⃣ Игровой никнейм:** {self.nickname.value}\n'
                    f'**2️⃣ Уровень игры:** {self.game_level.value}\n'
                    f'**3️⃣ Семьи и причины ухода:** {self.families.value}\n'
                    f'**4️⃣ Имя ООС:** {self.ooc_name.value}\n'
                    f'**5️⃣ Возраст ООС:** {self.ooc_age.value}\n\n'
                    '---\n'
                    '**Статус:** ⏳ Ожидает проверки'
                ),
                color=0xff6b6b,
                timestamp=interaction.created_at
            )
            embed.set_footer(text=f'ID заявки: {interaction.user.id}')
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            await ticket_channel.send(
                f'{interaction.guild.get_role(STAFF_ROLE_ID).mention} 📢 Новая заявка!'
            )
            await ticket_channel.send(embed=embed, view=ApplicationActions(interaction.user, application_data))
            
            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(
                    title='📩 Новая заявка',
                    description=(
                        f'**Пользователь:** {interaction.user.mention}\n'
                        f'**Ник:** {self.nickname.value}\n'
                        f'**Уровень:** {self.game_level.value}\n'
                        f'**Имя ООС:** {self.ooc_name.value}\n'
                        f'**Возраст ООС:** {self.ooc_age.value}\n'
                        f'**Время:** {discord.utils.format_dt(interaction.created_at)}'
                    ),
                    color=0x00ff88,
                    timestamp=interaction.created_at
                )
                await log_channel.send(embed=log_embed)
            
            await interaction.followup.send(
                f'✅ Заявка успешно отправлена! Ожидайте проверки.',
                ephemeral=True
            )
            
        except Exception as e:
            error_text = traceback.format_exc()
            print(f'❌ ОШИБКА в on_submit:\n{error_text}')
            
            await interaction.followup.send(
                f'❌ Произошла ошибка при отправке заявки. Попробуйте снова.\n'
                f'Ошибка: {str(e)[:100]}',
                ephemeral=True
            )

class ApplicationActions(discord.ui.View):
    def __init__(self, applicant, application_data):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.application_data = application_data
    
    @discord.ui.button(
        label='✅ Принять',
        style=discord.ButtonStyle.success,
        custom_id='accept_application'
    )
    async def accept_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(STAFF_ROLE_ID) not in interaction.user.roles:
            await interaction.response.send_message('❌ Нет прав!', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            trial_role = interaction.guild.get_role(TRIAL_ROLE_ID)
            if not trial_role:
                await interaction.followup.send('❌ Роль не найдена!', ephemeral=True)
                return
            
            await self.applicant.add_roles(trial_role, reason='Заявка принята в REDHELL')
            
            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(f'✅ {self.applicant} принят в REDHELL')
            
            try:
                dm_embed = discord.Embed(
                    title='🎉 Добро пожаловать в REDHELL!',
                    description='Ваша заявка **принята**! Вы на испытательном сроке.',
                    color=0x00ff00
                )
                await self.applicant.send(embed=dm_embed)
            except:
                pass
            
            await interaction.message.edit(
                content='✅ **Заявка ПРИНЯТА!**',
                embed=None,
                view=None
            )
            
            embed = discord.Embed(
                title='✅ Заявка ПРИНЯТА!',
                description=(
                    f'**Заявитель:** {self.applicant.mention}\n'
                    f'**Discord-тег:** {self.applicant}\n\n'
                    f'**Игровой никнейм:** {self.application_data["nickname"]}\n'
                    f'**Уровень игры:** {self.application_data["game_level"]}\n'
                    f'**Имя ООС:** {self.application_data["ooc_name"]}\n'
                    f'**Возраст ООС:** {self.application_data["ooc_age"]}\n\n'
                    '---\n'
                    f'**Принял:** {interaction.user.mention}'
                ),
                color=0x00ff00,
                timestamp=interaction.created_at
            )
            await interaction.channel.send(embed=embed)
            
            await interaction.followup.send('✅ Заявка принята!', ephemeral=True)
            
        except Exception as e:
            error_text = traceback.format_exc()
            print(f'❌ Ошибка в accept_application:\n{error_text}')
            await interaction.followup.send(f'❌ Ошибка: {str(e)[:100]}', ephemeral=True)
    
    @discord.ui.button(
        label='❌ Отклонить',
        style=discord.ButtonStyle.danger,
        custom_id='reject_application'
    )
    async def reject_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.get_role(STAFF_ROLE_ID) not in interaction.user.roles:
            await interaction.response.send_message('❌ Нет прав!', ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            try:
                dm_embed = discord.Embed(
                    title='❌ Заявка отклонена',
                    description='Ваша заявка в REDHELL **отклонена**.',
                    color=0xff0000
                )
                await self.applicant.send(embed=dm_embed)
            except:
                pass
            
            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(f'❌ Заявка {self.applicant} отклонена')
            
            await interaction.message.edit(
                content='❌ **Заявка ОТКЛОНЕНА!**',
                embed=None,
                view=None
            )
            
            embed = discord.Embed(
                title='❌ Заявка ОТКЛОНЕНА',
                description=(
                    f'**Заявитель:** {self.applicant.mention}\n'
                    f'**Discord-тег:** {self.applicant}\n\n'
                    '---\n'
                    f'**Отклонил:** {interaction.user.mention}'
                ),
                color=0xff0000,
                timestamp=interaction.created_at
            )
            await interaction.channel.send(embed=embed)
            
            await interaction.followup.send('❌ Заявка отклонена!', ephemeral=True)
            
        except Exception as e:
            error_text = traceback.format_exc()
            print(f'❌ Ошибка в reject_application:\n{error_text}')
            await interaction.followup.send(f'❌ Ошибка: {str(e)[:100]}', ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label='📩 Подать заявку',
        style=discord.ButtonStyle.primary,
        custom_id='create_ticket'
    )
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal())

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен!')
    print(f'📊 На серверах: {len(bot.guilds)}')
    print(f'🆔 ID бота: {bot.user.id}')
    print('=' * 50)
    print(f'📌 Канал с кнопкой: {APPLICATION_CHANNEL_ID}')
    print(f'📌 Канал для заявок: {TICKET_CHANNEL_ID}')

@bot.command(name='ticket')
@commands.has_permissions(administrator=True)
async def ticket_command(ctx):
    embed = discord.Embed(
        title='📝 Заявка в REDHELL',
        description=(
            'Нажмите кнопку ниже и заполните анкету.\n'
            'После отправки ваша заявка будет рассмотрена.\n\n'
            '**Заполняйте ответы внимательно!**'
        ),
        color=0xff6b6b
    )
    embed.set_footer(text='REDHELL | Сегодня')
    await ctx.send(embed=embed, view=TicketView())

@bot.command(name='setconfig')
@commands.has_permissions(administrator=True)
async def set_config(
    ctx,
    application_channel_id: int,
    ticket_channel_id: int,
    staff_role_id: int,
    log_channel_id: int,
    trial_role_id: int
):
    global APPLICATION_CHANNEL_ID, TICKET_CHANNEL_ID, STAFF_ROLE_ID, LOG_CHANNEL_ID, TRIAL_ROLE_ID
    APPLICATION_CHANNEL_ID = application_channel_id
    TICKET_CHANNEL_ID = ticket_channel_id
    STAFF_ROLE_ID = staff_role_id
    LOG_CHANNEL_ID = log_channel_id
    TRIAL_ROLE_ID = trial_role_id
    await ctx.send('✅ Конфигурация обновлена!')

@bot.command(name='checktrial')
@commands.has_permissions(administrator=True)
async def check_trial(ctx, member: discord.Member = None):
    member = member or ctx.author
    trial_role = ctx.guild.get_role(TRIAL_ROLE_ID)
    
    if trial_role in member.roles:
        await ctx.send(f'✅ {member.mention} на испытательном сроке')
    else:
        await ctx.send(f'❌ {member.mention} не на испытательном сроке')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Нет прав!')
    else:
        print(f'❌ Ошибка команды: {error}')
        print(traceback.format_exc())

if __name__ == "__main__":
    TOKEN = os.environ.get('TOKEN')
    if not TOKEN:
        print('❌ Ошибка: Токен не найден! Добавьте переменную окружения TOKEN')
        exit(1)
    bot.run(TOKEN)