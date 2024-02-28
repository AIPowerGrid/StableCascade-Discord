import asyncio
import os
from dotenv import load_dotenv
from gradio_client import Client
import nextcord
from nextcord.ext import commands
import random
import re

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
gradio_client = Client("http://127.0.0.1:7860/")
image_generation_queue = asyncio.Queue()
channel_id = yourchannelid

async def process_image_generation():
    while True:
        ctx, message = await image_generation_queue.get()
        random_color = random.randint(0, 0xFFFFFF)
        
        # if ctx.channel.id == 99999999:
        #     image_generation_queue.task_done()
        #     continue

        if ctx.channel.id == channel_id and ctx.channel.permissions_for(ctx.guild.me).send_messages:
            try:
                components = message.split()
                prompt_components = []
                flag_processing = False
                for component in components:
                    if component.startswith('-'):
                        flag_processing = True
                    if not flag_processing:
                        prompt_components.append(component)
                prompt = ' '.join(prompt_components)

                width, height = 1024, 1024
                seed = random.randint(0, 2147483647)
                
                #Prior Inference Steps
                steps = 20

                #Prior Guidance Scale
                pgs = 4

                #Decoder Inference Steps
                dis = 10
                negative_prompt = ""

                if '-seed' in message:
                    seed_index = components.index('-seed') + 1
                    if seed_index < len(components):
                        seed = int(components[seed_index])

                for i, component in enumerate(components):
                    if component == '-ar' and i + 1 < len(components):
                        try:
                            width, height = map(int, components[i + 1].split('x'))
                        except ValueError:
                            width, height = 1024, 1024
                    elif component == '-steps' and i + 1 < len(components):
                        steps = max(10, min(30, int(components[i + 1])))
                    elif component == '-PGS' and i + 1 < len(components):
                        pgs = max(0, min(20, int(components[i + 1])))
                    elif component == '-DIS' and i + 1 < len(components):
                        dis = max(4, min(12, int(components[i + 1])))

                negative_prompt_match = re.search(r"\[(.*?)\]", message)
                if negative_prompt_match:
                    negative_prompt_content = negative_prompt_match.group(1)
                    if negative_prompt_content:
                        negative_prompt = negative_prompt_content
                    else:
                        negative_prompt = ""

                result = gradio_client.predict(prompt, negative_prompt, seed, width, height, steps, pgs, dis, 0, 1, api_name="/run")

                image_path = result
                embed_image = nextcord.Embed(color=random_color)
                embed_image.set_image(url="attachment://image.png")
                embed_prompt = nextcord.Embed(description=prompt, color=random_color)

                details_description = (
                    f"\U0001F4CF {width}x{height} "  # Ruler emoji for dimensions
                    f"\U0001F331 {seed} "  # Seedling emoji for seed
                    f"\U0001F463 {steps} "  # Footprints emoji for Steps
                    f"\U0001F9ED {dis} "  # Abacus for DIS, suggesting calculation or progression in steps
                    f"\U0001F3C3 {pgs} "  # Runner emoji for PGS, representing guided progress
                    f"\U0001F3D7 3 Stage Stable Cascade on the Würstchen architecture"  # Construction for architecture
                )

                embed_details = nextcord.Embed(description=details_description, color=random_color)
                message_with_mention = f"\U0001F9E0 {ctx.author.mention}"
                await ctx.send(content=message_with_mention, embeds=[embed_image, embed_prompt, embed_details], file=nextcord.File(image_path, filename="image.png"))

            except Exception as e:
                await ctx.send(f"Sorry {ctx.author.mention}, there was an error processing your request: {e}")
            finally:
                image_generation_queue.task_done()

@bot.command(name='dream')
async def dream(ctx, *, prompt: str):
    channel_id = 1208069458753753118

    if ctx.channel.id != channel_id:
        await ctx.send("This command can only be used in the designated channel.")
        return 

    await ctx.send(f"Thanks {ctx.author.mention}, your request is queued. Please wait...")
    await image_generation_queue.put((ctx, prompt))
    
    bot.loop.create_task(process_image_generation())

bot.run(DISCORD_BOT_TOKEN)