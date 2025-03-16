import discord, sqlite3, json, re
from discord.ext import commands
from random import choice, randint

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

conn = sqlite3.connect('data/user_settings.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS user_settings
             (user_id INTEGER PRIMARY KEY, default_translation TEXT, timezone TEXT)''')

# Italics font

def format_verse_text(text):
    return re.sub(r'\[([^\]]+)\]', r'*\1*', text)

@client.tree.command(name="random", description="Displays random Bible verse")
async def random(interaction: discord.Interaction):

    await interaction.response.defer()

    user_id = interaction.user.id
    c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()
    
    if not user_data:
        embed = discord.Embed(
            title="Set the default Bible translation",
            description='To use the Bible passage search function, you must first set the default Bible translation using the `/setversion` command. To set the default Bible translation, you need to specify a translation abbreviation. All translation abbreviations are available in `/versions`',
            color=12370112)
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    translation = user_data[1]

    with open(f'resources/bibles/{translation}.json', 'r') as file:
        bible = json.load(file)

    with open('resources/translations/translations.json', 'r', encoding='utf-8') as f:
        translations = json.load(f)
    
    count = randint(1, 10)
    
    random_start = choice(bible)
    book_name = random_start["book_name"]
    chapter_number = random_start["chapter"]

    same_chapter_verses = [
        verse for verse in bible if verse["book_name"] == book_name and verse["chapter"] == chapter_number
    ]

    same_chapter_verses.sort(key=lambda x: x["verse"])

    start_index = same_chapter_verses.index(random_start)
    selected_verses = same_chapter_verses[start_index:start_index + count]

    verses_text = ""
    
    first_verse_number = selected_verses[0]["verse"]
    last_verse_number = selected_verses[-1]["verse"]

    for selected_verse in selected_verses:
        verse_number = selected_verse["verse"]
        text = selected_verse["text"]

        verses_text += f"**({verse_number})** {format_verse_text(text)} "

    if first_verse_number == last_verse_number:
        title = f"{book_name} {chapter_number}:{first_verse_number}"
    else:
        title = f"{book_name} {chapter_number}:{first_verse_number}-{last_verse_number}"

    embed = discord.Embed(
        title=title,
        description=verses_text,
        color=12370112
    )
    embed.set_footer(text=translations[translation])

    await interaction.followup.send(embed=embed)