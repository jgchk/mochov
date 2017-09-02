import random

import discord
from discord.ext import commands
from markov.markov import Markov, EmptyModelError


def setup(bot):
    bot.add_cog(Mochov(bot))


def check_manage_server_permission(ctx):
    author = ctx.message.author
    channel = ctx.message.channel
    return author.permissions_in(channel).manage_server


class Mochov:
    def __init__(self, bot):
        self.bot = bot

        self.models = {}

    async def on_message(self, message):
        self.store_message(message)

    def store_message(self, message):
        if message.author.bot:
            return False
        if not message.clean_content:
            return False
        if message.clean_content[0] == self.bot.command_prefix:
            return False

        if message.author.id not in self.models:
            self.models[message.author.id] = Markov(prefix=message.author.id)
        self.models[message.author.id].add_line_to_index(message.clean_content.split())
        return True

    @commands.command(pass_context=True, aliases=["m"])
    async def mochov(self, ctx, member: discord.Member, *start_text):

        if member is None:
            member = ctx.message.author

        if member.id not in self.models:
            self.models[member.id] = Markov(prefix=member.id)

        try:
            sentences = []
            while len(sentences) < random.randint(1, 10):
                sentence = []
                while len(sentence) < random.randint(1, 10):
                    if start_text:
                        sentence = self.models[member.id].generate(max_words=100, seed=list(start_text))
                    else:
                        sentence = self.models[member.id].generate(max_words=100)
                sentences.append(sentence)
        except EmptyModelError:
            await self.bot.say("Not enough data for {}".format(member))
        else:
            message = ". ".join([" ".join(sentence) for sentence in sentences]) + "."
            await self.bot.say(message)

    @commands.command(pass_context=True, aliases=["build_model"])
    @commands.check(check_manage_server_permission)
    async def build_models(self, ctx, num_messages: int, member: discord.Member = None):
        counter = 0
        async for message in self.bot.logs_from(ctx.message.channel, limit=num_messages):
            if not member or message.author == member:
                counter += 1
                self.store_message(message)
        await self.bot.say("Successfully stored {:d} messages".format(counter))

    @commands.command(pass_context=True, aliases=["clear_model"])
    @commands.check(check_manage_server_permission)
    async def clear_models(self, ctx, member: discord.Member = None):
        if member:
            confirmation_msg = await self.bot.say("Are you sure you want to delete data for {}?".format(member))
        else:
            confirmation_msg = await self.bot.say("Are you sure you want to delete all data?")
        await self.bot.add_reaction(confirmation_msg, "✅")
        await self.bot.add_reaction(confirmation_msg, "❌")

        reaction = await self.bot.wait_for_reaction(["✅", "❌"], message=confirmation_msg, timeout=60,
                                                    user=ctx.message.author)
        await self.bot.delete_message(confirmation_msg)
        if reaction is None or reaction.reaction.emoji == "❌":
            return

        if member:
            self.models[member.id].flush()
        else:
            models = list(self.models.values())
            if models:
                models[0].flush(all=True)

        await self.bot.say("Deleted data.")
