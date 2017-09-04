import random
import string
import time
from mochov.utils.context_managers import Typing

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

    @commands.command(pass_context=True, aliases=["gen", "g"])
    async def generate(self, ctx, member: discord.Member, *start_text):
        async with Typing(self.bot):
            if member is None:
                member = ctx.message.author

            try:
                message = self.generate_message(member, start_text)
            except EmptyModelError:
                await self.bot.say("Not enough data for {}".format(member))
            else:
                await self.bot.say(message)

    def generate_message(self, member, start_text=None, num_sentences=random.randint(1, 10),
                         words_per_sentence=random.randint(1, 10)):
        if member.id not in self.models:
            self.models[member.id] = Markov(prefix=member.id)

        sentences = []
        while len(sentences) < num_sentences:
            if start_text and not sentences:
                sentence = self.models[member.id].generate(max_words=100, seed=list(start_text))
            else:
                sentence = []
                while len(sentence) < words_per_sentence:
                    sentence += self.models[member.id].generate(max_words=100)
            sentences.append(sentence)
        message = ""
        for sentence in sentences:
            message += " ".join(sentence)
            if sentence and sentence[-1] and sentence[-1][-1] not in string.punctuation:
                message += ". "
        return message

    def check_random_guess_command(self, message):
        if not message.clean_content.startswith("{prefix}guess".format(prefix=self.bot.command_prefix)):
            return False
        if len(message.clean_content.split(maxsplit=1)) != 2:
            return False
        return True

    @commands.command(pass_context=True, aliases=["rand", "r"])
    async def random(self, ctx):
        async with Typing(self.bot):
            rand_members = list(ctx.message.channel.server.members)
            random.shuffle(rand_members)
            rand_member = None

            message = None
            for member in rand_members:
                try:
                    message = self.generate_message(member, num_sentences=random.randint(1, 3),
                                                    words_per_sentence=random.randint(5, 10))
                except EmptyModelError:
                    continue
                else:
                    rand_member = member

            if not message:
                await self.bot.say(
                    "Not enough data for users in this channel. Try running {prefix}store_history first.".format(
                        prefix=self.bot.command_prefix))

            await self.bot.say("\"{}\"".format(message))
            await self.bot.say("Use {prefix}guess <member> to guess who the quote above is mimicking.".format(
                prefix=self.bot.command_prefix))

        tries = 3
        timeout = 120
        time_end = time.time() + timeout
        while tries > 0 and time.time() < time_end:
            msg = await self.bot.wait_for_message(timeout=1, channel=ctx.message.channel,
                                                  check=self.check_random_guess_command)
            if not msg:
                continue

            if msg.mentions:
                guess = msg.mentions[0]
            else:
                guess_text = msg.clean_content.split(maxsplit=1)[1]
                if guess_text.startswith("\""):
                    guess_text = guess_text[1:]
                if guess_text.endswith("\""):
                    guess_text = guess_text[:-1]
                server = msg.channel.server
                guess = server.get_member(guess_text)
                if not guess:
                    guess = server.get_member_named(guess_text)
                    if not guess:
                        await self.bot.say("Could not find member \"{}\".".format(guess_text))
                        continue

            if guess == rand_member:
                await self.bot.say("Correct! The message is based off of {}!".format(rand_member.display_name))
                return
            else:
                await self.bot.say("{} is incorrect.".format(guess.display_name))
                tries -= 1
        if tries <= 0:
            await self.bot.say("Ran out of tries. The correct answer was {}.".format(rand_member.display_name))
        else:
            await self.bot.say("Timed out. The correct answer was {}.".format(rand_member.display_name))

    @commands.command(pass_context=True)
    @commands.check(check_manage_server_permission)
    async def store_history(self, ctx, num_messages: int, member: discord.Member = None):
        async with Typing(self.bot):
            counter = 0
            async for message in self.bot.logs_from(ctx.message.channel, limit=num_messages):
                if not member or message.author == member:
                    counter += 1
                    self.store_message(message)
            await self.bot.say("Successfully stored {:d} messages".format(counter))

    @commands.command(pass_context=True)
    @commands.check(check_manage_server_permission)
    async def clear_cache(self, ctx, member: discord.Member = None):
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
