import os
import random
import discord
from tabulate import tabulate
from discord.ext import commands
from io import BytesIO
from dotenv import load_dotenv
from script import find_spreads, find_em
import pandas as pd

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

@bot.command(name='spreads', help='View/filter spreads for an option')
async def spreads(ctx, ticker: str, exp_date: str, spread_type: str, rr: float = None, pop: float = None):
    res = find_spreads(ticker.lower(), exp_date, spread_type.lower(), rr, pop)
    if isinstance(res, pd.DataFrame) and not res.empty:
        caption = '☑ Results for {} {} Contracts\n☑ Spread Type: {}, Risk/Reward Ratio >= {}, PoP >= {}%'.format(ticker.upper(), exp_date, spread_type, rr, pop)
        filename = '{}_{}_{}_{}_{}.txt'.format(ticker, exp_date, spread_type, rr, pop)
        await ctx.send(caption, file=discord.File(BytesIO(tabulate(res, headers='keys', tablefmt='psql', showindex=False).encode('utf-8')), filename))
    elif isinstance(res, str):
        await ctx.send(res)

@bot.command(name='em', help='Calculate the volatility and expected move for a contract')
async def em(ctx, ticker: str, exp_date: str):
    res = find_em(ticker, exp_date)
    await ctx.send(res)

@spreads.error
async def do_repeat_handler(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing some positional arguments 😥')
        await ctx.send('Usage ```!spreads [TICKER] [EXP_DATE (MM/DD/YYYY)] [SPREAD_TYPE (CS/DS)] [RISK/REWARD (OPTIONAL)] [POP (OPTIONAL)]```')
        await ctx.send('Example ```!spreads AMD 11/20/2020 DS or !spreads AMD 11/20/2020 DS 2 25```')
        await ctx.send('Risk reward filtering - For DS, this should be greater than 2 and for CS it should be greater than .25')
        await ctx.send('PoP filtering - For DS, this should be greater than 20 and for CS it should be greater than 50')

@em.error
async def do_repeat_handler(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Missing some positional arguments 😥')
        await ctx.send('Usage ```!em [TICKER] [EXP_DATE (MM/DD/YY)]```')
        await ctx.send('Example ```!em AMD 11/20/20```')

bot.run(TOKEN)