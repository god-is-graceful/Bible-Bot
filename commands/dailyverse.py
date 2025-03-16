import discord, json, sqlite3, requests, re
from discord.ext import commands
from bs4 import BeautifulSoup

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)

conn = sqlite3.connect('data/user_settings.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS user_settings
             (user_id INTEGER PRIMARY KEY, default_translation TEXT)''')

# Italics font

def format_verse_text(text):
    return re.sub(r'\[([^\]]+)\]', r'*\1*', text)

@client.tree.command(name="dailyverse", description="Displays the verse of the day from the Bible")
async def dailyverse(interaction: discord.Interaction):
    await interaction.response.defer()
   
    user_id = interaction.user.id

    c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    user_data = c.fetchone()
   
    if not user_data or not user_data[1]:
        embed = discord.Embed(
            title="Set the default Bible translation",
            description='To use the Bible passage search function, you must first set the default Bible translation using the `/setversion` command. To set the default Bible translation, you need to specify a translation abbreviation. All translation abbreviations are available in `/versions`',
            color=12370112)
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    translation = user_data[1]

    with open(f'resources/bibles/{translation}.json', 'r', encoding='utf-8') as file:
        bible = json.load(file)
        
    with open('resources/translations/translations.json', 'r', encoding='utf-8') as file:
        translations = json.load(file)

    response = requests.get("https://www.verseoftheday.com/")
    soup = BeautifulSoup(response.text, 'html.parser')
    reference_div = soup.find("div", class_="reference")
    link = reference_div.find("a", href=True)
    verse_reference = link.text.strip()
    
    book, chapter_verse = verse_reference.rsplit(" ", 1)
    chapter, verses = chapter_verse.split(":")
    chapter = int(chapter)
    
    verse_range = verses.split("-")
    start_verse = int(verse_range[0])
    end_verse = int(verse_range[1]) if len(verse_range) > 1 else start_verse
    
    text = []

    for verse in bible:
        if verse['book_name'] == book and verse['chapter'] == chapter and start_verse <= verse['verse'] <= end_verse:
            text.append(f"**({verse['verse']})** {format_verse_text(verse['text'])}")

    if start_verse == end_verse:
        title = f"{book} {chapter}:{start_verse}"
    else:
        title = f"{book} {chapter}:{start_verse}-{end_verse}"

    embed = discord.Embed(
        title=title,
        description=" ".join(text),
        color=12370112
    )

    embed.set_footer(text=translations[translation])
    await interaction.followup.send(embed=embed, ephemeral=True)