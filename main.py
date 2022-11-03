from create import *



# Choosing a new Baka in chat
async def new_baka_member(chat_id) -> None:
    try:
        # Getting information about registered chat users
        # DATABASE
        users = await get_entries(User, chat_id)
    except Exception as e:
        logging.error(f"FUNC: new_baka_member (1)\nCHAT: {chat_id}\nError: {str(e)}", exc_info=True)
        # TELEGRAM
        await bot.send_message(chat_id=chat_id, text=client_text["TEXT"]["TECHNICAL_MAINTENANCE"])
        return
    # If there are registered users in the chat room
    if users != []:
        # User Choice
        user_idx = random.randrange(1, 10000) % len(users)
        # Getting user information on telegram servers
        # TELEGRAM
        user_info = await bot.get_chat_member(chat_id, users[user_idx].user_id)
        # If a user does not have enough social ratings
        if (users[user_idx].social_points < FINE_BAKA):
            try:
                # Give the user a bonus = PRICE_BUYBACK
                # DATABASE
                await change_social_points(User, chat_id, users[user_idx].user_id, BONUS)
            except Exception as e:
                logging.info(f"FUNC: new_baka_member (2)\nCHAT: {chat_id}\nError: {str(e)}", exc_info=True)
                # TELEGRAM
                await bot.send_message(chat_id=chat_id, text=f"{client_text['TEXT']['TECHNICAL_MAINTENANCE']}")
                return
            # Chat notification about issuing a bonus to the user
            # TELEGRAM
            sticker_indx = random.randrange(0, len(client_text['STICKERS']['BONUS']))
            await bot.send_message(
                chat_id=chat_id,
                text=client_text['TEXT']['NO_BAKA_MONEY'].format(
                    user_info['user']['first_name'],
                    BONUS
                )
            )
            await bot.send_sticker(chat_id=chat_id, sticker=f"{client_text['STICKERS']['BONUS'][sticker_indx]}")
            # Removing a user from the applicant pool
            users.pop(user_idx)
            # Choosing a new user
            if len(users) == 0:
                # TELEGRAM
                await bot.send_message(chat_id=chat_id, text=client_text['TEXT']['NO_USER_FOR_BAKA'])
                return
            user_idx = random.randrange(1, 10000) % len(users)
            # Getting user information on telegram servers
            # TELEGRAM
            user_info = await bot.get_chat_member(chat_id, users[user_idx].user_id)
        try:
            # Issue a fine=FINE_BAKA to the user
            # DATABASE
            await change_social_points(User, chat_id, users[user_idx].user_id, -FINE_BAKA)
        except Exception as e:
            logging.error(f"FUNC: new_baka_member (3)\nCHAT: {chat_id}\nError: {str(e)}", exc_info=True)
            await bot.send_message(chat_id=chat_id, text=client_text["TEXT"]["TECHNICAL_MAINTENANCE"])
            return
        try:
            # Making changes about the new Baka in the database
            await reset_field_baka(User, chat_id)
            await set_filed_baka(User, chat_id, users[user_idx].user_id)
        except Exception as e:
            logging.error(f"FUNC: new_baka_member (4)\nCHAT: {chat_id}\nError: {str(e)}", exc_info=True)
            try:
                # In the case of an error, you must try to return the previous values in the database
                await change_social_points(User, chat_id, users[user_idx].user_id, FINE_BAKA)
            except Exception as e2:
                logging.error(f"FUNC: new_baka_member (5)\nCHAT: {chat_id}\nError: {str(e2)}", exc_info=True)
            await bot.send_message(chat_id=chat_id, text=client_text["TEXT"]["TECHNICAL_MAINTENANCE"])
            return
        sticker_indx = random.randrange(0, len(client_text['STICKERS']['NEW_BAKA']))
        # Notification of new Baka in chat
        await bot.send_message(
            chat_id=chat_id,
            text=client_text["TEXT"]["NEW_BAKA"].format(
                user_info['user']['first_name'],
                PRICE_BUYBACK
            )
        )
        await bot.send_sticker(chat_id=chat_id, sticker=f"{client_text['STICKERS']['NEW_BAKA'][sticker_indx]}")
        return
    # Notification of absence of registered users in the chat room
    await bot.send_message(chat_id=chat_id, text=client_text["TEXT"]["NO_MUCH_REG_MEMBERS"])



# Events bot
@dp.my_chat_member_handler()
async def my_chat_member(event: types.ChatMemberUpdated) -> None:
    if event["old_chat_member"]["status"] == "left":
        if event["new_chat_member"]["status"] == "member":
            try:
                await create_entry(User, event['from']['id'], event["chat"]["id"], 1)
                await new_admin(User, event["chat"]["id"], event['from']['id'])
            except Exception as e:
                logging.error(f"FUNC: my_chat_member (1)\nCHAT: {event['chat']['id']}\nError: {str(e)}", exc_info=True)
                await bot.send_message(chat_id=event["chat"]["id"], text=client_text["TEXT"]["TECHNICAL_MAINTENANCE"])
                await bot.leave_chat(event["chat"]["id"])
                await delete_entries(User, event["chat"]["id"])
                return
            await bot.send_message(chat_id=event["chat"]["id"], text=f"{client_text['TEXT']['INVITE_HANDLER']}\n\n{client_text['TEXT']['INVITE'].format(PRICE_BUYBACK)}")
            return
    elif event["old_chat_member"]["status"] == "member":
        if event["new_chat_member"]["status"] == "left":
            try:
                # Bot kicked from chat
                await delete_entries(User, event["chat"]["id"])
            except Exception as e:
                logging.error(f"FUNC: my_chat_member (3)\nCHAT: {event['chat']['id']}\nError: {str(e)}", exc_info=True)
                return
            return


@dp.message_handler(ChatTypeFilter([types.ChatType.GROUP, types.ChatType.SUPERGROUP]), content_types=types.ContentType.LEFT_CHAT_MEMBER)
async def left_user(message: types.Message) -> None:
    if not message.left_chat_member.is_bot:
        await delete_entry(User, message.chat.id, message.left_chat_member.id)
        await message.reply(client_text['TEXT']['MEMBER_LEFT'])
        admins = await get_admins(User, message.chat.id)
        if admins == []:
            await message.answer(client_text['TEXT']['NO_ADMIN_IN_CHAT'])
            users = await get_entries_social_stats(User, message.chat.id, 1)
            if users == []:
                await message.answer(client_text['TEXT']['SHOGUN_LEFT'])
                await bot.leave_chat(message.chat.id)
                await delete_entries(User, message.chat.id)
                return
            # Getting user information on telegram servers
            user_info = await bot.get_chat_member(message.chat.id, users[0].user_id)
            await new_admin(User, message.chat.id, users[0].user_id)
            await message.answer(client_text['TEXT']['NEW_RANDOM_ADMIN'].format(user_info['user']['first_name']))


# The "help"/"info" message handler. Shows information for using the bot.
@dp.message_handler(ChatTypeFilter([types.ChatType.GROUP, types.ChatType.SUPERGROUP]), commands=['help', 'info', 'start'], state=None)
async def help_call(message: types.Message) -> None:
    await message.reply(f"{client_text['TEXT']['INVITE_HANDLER']}\n\n{client_text['TEXT']['INVITE'].format(PRICE_BUYBACK)}")


# The "/top_points" command handler. Top users by social rating.
@dp.message_handler(ChatTypeFilter([types.ChatType.GROUP, types.ChatType.SUPERGROUP]), commands='top_points')
async def soical_stats(message: types.Message) -> None:
    try:
        user = await get_entry(User, message.chat.id, message.from_user.id)
        # Getting information about registered chat users
        users = await get_entries_social_stats(User, message.chat.id, 10)
    except Exception as e:
        logging.error(f"FUNC: soical_stats (1)\nCHAT: {message.chat.id}\nError: {str(e)}", exc_info=True)
        await message.answer(client_text["TEXT"]["TECHNICAL_MAINTENANCE"])
        return
    if user.user_id == zero_object.user_id:
        await message.reply(text=client_text['TEXT']['UNKNOWN_USER'])
        return
    # If there are registered users in the chat room
    if users != []:
        # Message generation
        msg = f"{client_text['TEXT']['SOCIAL_STATS_HANDLER']}\n"
        i = 1
        for user in users:
            # Getting user information on telegram servers
            user_info = await bot.get_chat_member(message.chat.id, user.user_id)
            msg += client_text['TEXT']['SOCIAL_STATS'].format(str(i), user_info['user']['first_name'], user.social_points)
            i += 1
        await message.answer(msg)
        return
    # There are no registered users in the chat room
    await message.answer(client_text['TEXT']['NO_SOCIAL_STATS'])


# The "/top_baka" command handler. Shows chat statistics.
@dp.message_handler(ChatTypeFilter([types.ChatType.GROUP, types.ChatType.SUPERGROUP]), commands='top_baka')
async def baka_times(message: types.Message) -> None:
    try:
        user = await get_entry(User, message.chat.id, message.from_user.id)
        # Getting no more than 10 registered users with the highest number of baka_times
        bakas = await get_entries_baka_times(User, message.chat.id, 10)
    except Exception as e:
        logging.error(f"FUNC: baka_times (1)\nCHAT: {message.chat.id}\nError: {str(e)}", exc_info=True)
        await message.answer(client_text["TEXT"]["TECHNICAL_MAINTENANCE"])
        return
    if user.user_id == zero_object.user_id:
        await message.reply(text=client_text['TEXT']['UNKNOWN_USER'])
        return
    # If there are no users in the chat room that
    if bakas != []:
        # Message generation
        msg = f"{client_text['TEXT']['BAKA_TIMES_HANDLER']}\n"
        i = 1
        for baka in bakas:
            # Getting user information on telegram servers
            user_info = await bot.get_chat_member(message.chat.id, baka.user_id)
            msg += client_text['TEXT']['BAKA_TIMES'].format(str(i), user_info['user']['first_name'], baka.baka_times)
            i += 1
        await message.answer(msg)
        return
    # Notification of the absence of tank statistics
    await bot.send_message(chat_id=message.chat.id, text=client_text['TEXT']['NO_BAKA_STATS'])



# The "/reg" command handler. Signing up for the bot.
@dp.message_handler(ChatTypeFilter([types.ChatType.GROUP, types.ChatType.SUPERGROUP]), commands='reg')
async def reg_member(message: types.Message) -> None:
    try:
        # Attempting to register a user / Create a database entry
        user_was_not_logged = await create_entry(User, message.from_user.id, message.chat.id, 0)
    except Exception as e:
        logging.error(f"FUNC: reg_member (1)\nCHAT: {message.chat.id}\nUSER:\n{message.from_user.id}\nError: {str(e)}", exc_info=True)
        await message.reply(text=client_text["TEXT"]["TECHNICAL_MAINTENANCE"])
        return
    # User has just registered
    if user_was_not_logged:
        # Getting user information on telegram servers
        user_info = await bot.get_chat_member(message.chat.id, message.from_user.id)
        sticker_indx =  random.randrange(0, len(client_text['STICKERS']['SUCCESSFULL_REGISTRATION']))
        await message.reply(text=client_text["TEXT"]["SUCCESSFULL_REGISTRATION"].format(user_info['user']['first_name']))
        await bot.send_sticker(chat_id=message.chat.id, sticker=f"{client_text['STICKERS']['SUCCESSFULL_REGISTRATION'][sticker_indx]}")
        return
    # User is already registered
    await message.reply(text=client_text["TEXT"]["REGISTERED_MEMBER"])


# The "/my_stat" command handler. Displays personal chat statistics.
@dp.message_handler(ChatTypeFilter([types.ChatType.GROUP, types.ChatType.SUPERGROUP]), commands='my_stat', state=None)
async def statistic_member(message: types.Message) -> None:
    try:
        # Getting information about the chat user
        user = await get_entry(User, message.chat.id, message.from_user.id)
    except Exception as e:
        logging.error(f"FUNC: statistic_member (1)\nCHAT: {message.chat.id}\nUSER:\n{message.from_user.id}\nError: {str(e)}", exc_info=True)
        await message.reply(client_text['TEXT']['TECHNICAL_MAINTENANCE'])
        return
    # If there is information about the user
    if user.user_id != zero_object.user_id:
        # Getting user information on telegram servers
        user_info = await bot.get_chat_member(message.chat.id, message.from_user.id)
        role = "Самурай"
        baka_now = "Да"
        if user.baka == 0:
            baka_now = "Нет"
        if user.admin == 1:
            role = "Сёгунат/Родзю"
        await message.reply(
            text=f"{client_text['TEXT']['MEMBER_STATS_HANDLER'].format(user_info['user']['first_name'])}\n\n{client_text['TEXT']['MEMBER_STATS'].format(role,user.social_points,baka_now,user.baka_times)}")
        return
    # Notification that the user is not registered
    await message.reply(text=client_text['TEXT']['UNKNOWN_USER'])


# The "/baka" command handler. Current baka.
@dp.message_handler(ChatTypeFilter([types.ChatType.GROUP, types.ChatType.SUPERGROUP]), commands='baka')
async def baka_member(message: types.Message) -> None:
    try:
        # Getting information about Baka chat
        user = await get_entry(User,message.chat.id, message.from_user.id)
        baka = await get_entry_baka(User, message.chat.id)
    except Exception as e:
        logging.error(f"FUNC: baka_member (1)\nCHAT: {message.chat.id}\nError: {str(e)}", exc_info=True)
        await message.answer(text=client_text["TEXT"]["TECHNICAL_MAINTENANCE"])
        return
    if user.user_id == zero_object.user_id:
        await message.reply(text=client_text['TEXT']['UNKNOWN_USER'])
        return
    # If the information about Baka chat is
    if baka.user_id != zero_object.user_id:
        # Getting user information on telegram servers
        user_info = await bot.get_chat_member(message.chat.id, baka.user_id)
        await message.answer(
            text=client_text["TEXT"]["BAKA_USER"].format(
                user_info['user']['first_name'],
                PRICE_BUYBACK
            )
        )
        return
    # If there is no information about Baka chat, select a new Baka in chat.
    await new_baka_member(message.chat.id)



# "/buyback" callback handler. Payoff from the role of Baka
@dp.message_handler(ChatTypeFilter([types.ChatType.GROUP, types.ChatType.SUPERGROUP]), commands="buyback", state=None)
async def buyback(message: types.Message) -> None:
    try:
        # Getting information about the chat user
        user = await get_entry(User, message.chat.id, message.from_user.id)
    except Exception as e:
        logging.error(f"FUNC: buyback (1)\nCHAT: {message.chat.id}\nUSER:\n{message.from_user.id}\nError: {str(e)}", exc_info=True)
        await message.reply(client_text['TEXT']['TECHNICAL_MAINTENANCE'])
        return
    # If the user is registered
    if user.user_id != zero_object.user_id:
        # If he is Baka now
        if user.baka == 1:
            # If he has a sufficient social rating
            if user.social_points >= PRICE_BUYBACK:
                # Getting user information on telegram servers
                user_info = await bot.get_chat_member(message.chat.id, message.from_user.id)
                # You can only buy off a tank once before the wipe
                if user.chat_id not in users_buyback:
                    users_buyback[user.chat_id] = False
                # If there has already been a redemption
                if users_buyback[user.chat_id] == True:
                    await message.reply(client_text['TEXT']['BUYBACK_COOLDOWN'].format(user_info['user']['first_name']))
                    return
                users_buyback[user.chat_id] = True
                try:
                    # Take away a user's PRICE_BUYBACK social rating
                    await change_social_points(User, message.chat.id, message.from_user.id, -PRICE_BUYBACK)
                except Exception as e:
                    logging.error(f"FUNC: buyback (2)\nCHAT: {message.chat.id}\nUSER:\n{message.from_user.id}\nError: {str(e)}", exc_info=True)
                    await message.reply(client_text['TEXT']['TECHNICAL_MAINTENANCE'])
                    return
                sticker_indx = random.randrange(0, len(client_text['STICKERS']['BUYBACK']))
                await message.answer(client_text['TEXT']['BUYBACK_NOTIFICATION'].format(
                    user_info['user']['first_name']
                    )
                )
                await bot.send_sticker(chat_id=message.chat.id,
                                       sticker=f"{client_text['STICKERS']['BUYBACK'][sticker_indx]}")
                try:
                    # Select a new Baka in chat.
                    await new_baka_member(message.chat.id)
                except Exception as e:
                    logging.error(f"FUNC: buyback (3)\nCHAT: {message.chat.id}\nError: {str(e)}", exc_info=True)
                    await message.answer(client_text['TEXT']['TECHNICAL_MAINTENANCE'])
                    return
                return
            # Notice that social rating is not enough for buyback
            await message.reply(client_text['TEXT']['NO_MONEY_BUYBACK'])
            return
        # Notification that the user is not Baka
        await message.reply(client_text['TEXT']['NO_BAKA'])
        return
    # Notification that the user is not registered
    await message.reply(client_text['TEXT']['UNKNOWN_USER'])


# The "/new_admin" command handler. Assigning a user as an administrator.
@dp.message_handler(ChatTypeFilter([types.ChatType.GROUP, types.ChatType.SUPERGROUP]), commands="new_admin", state=None)
async def new_admin_member(message: types.Message) -> None:
    try:
        # Getting information about the chat user
        user = await get_entry(User, message.chat.id, message.from_user.id)
    except Exception as e:
        logging.error(f"FUNC: new_admin_member (1)\nCHAT: {message.chat.id}\nUSER:\n{message.from_user.id}\nError: {str(e)}", exc_info=True)
        await message.reply(client_text['TEXT']['TECHNICAL_MAINTENANCE'])
        return
    # If the user is registered
    if user.user_id != zero_object.user_id:
        # The command contains an attached message from the desired user and the caller is an administrator
        if (message.reply_to_message != None) and (user.admin == 1):
            try:
                # Getting information about the new admin chat
                member = await get_entry(User, message.chat.id, message.reply_to_message.from_user.id)
            except Exception as e:
                logging.error(f"FUNC: new_admin_member (2)\nCHAT: {message.chat.id}\nUSER:\n{message.reply_to_message.from_user.id}\nError: {str(e)}", exc_info=True)
                await message.reply(client_text['TEXT']['TECHNICAL_MAINTENANCE'])
                return
            # If the new admin is registered
            if member.user_id != zero_object.user_id:
                # Getting user information on telegram servers
                user_info = await bot.get_chat_member(message.chat.id, member.user_id)
                # If the new admin is not admin
                if member.admin == 0:
                    try:
                        # Making changes to the database / Assigning an administrator
                        await new_admin(User, message.chat.id, member.user_id)
                    except Exception as e:
                        logging.error(f"FUNC: new_admin_member (3)\nCHAT: {message.chat.id}\nUSER:\n{member.user_id}\nError: {str(e)}", exc_info=True)
                        await message.reply(client_text['TEXT']['TECHNICAL_MAINTENANCE'].format(user_info['user']['first_name']))
                        return

                    sticker_indx =  random.randrange(0, len(client_text['STICKERS']['NEW_ADMIN']))
                    # Notification of a new chat administrator
                    await message.reply(client_text['TEXT']['NEW_ADMIN'].format(user_info['user']['first_name']))
                    await bot.send_sticker(chat_id=message.chat.id,
                                           sticker=f"{client_text['STICKERS']['NEW_ADMIN'][sticker_indx]}")
                    return
                # The user is already a chat administrator
                await message.reply(client_text['TEXT']['MEMBER_IS_ADMIN'].format(user_info['user']['first_name']))
                return
            # User is unregistered
            await message.reply(client_text['TEXT']['UNKNOWN_MEMBER'])
            return
        return


# The "/delete_admin" command handler. Removing a user from the administrator role.
@dp.message_handler(ChatTypeFilter([types.ChatType.GROUP, types.ChatType.SUPERGROUP]), commands="delete_admin", state=None)
async def delete_admin_member(message: types.Message):
    try:
        # Getting information about the chat user
        user = await get_entry(User, message.chat.id, message.from_user.id)
    except Exception as e:
        logging.error(f"FUNC: delete_admin_member (1)\nCHAT: {message.chat.id}\nUSER:\n{message.from_user.id}\nError: {str(e)}", exc_info=True)
        await message.reply(client_text['TEXT']['TECHNICAL_MAINTENANCE'])
        return
    # If the user is registered
    if user.user_id != zero_object.user_id:
        # The command contains an attached message from the desired user and the caller is an administrator
        if (message.reply_to_message != None) and (user.admin == 1):
            try:
                # Getting information about the old admin chat
                member = await get_entry(User, message.chat.id, message.reply_to_message.from_user.id)
            except Exception as e:
                logging.error(f"FUNC: delete_admin_member (2)\nCHAT: {message.chat.id}\nUSER:\n{message.reply_to_message.from_user.id}\nError: {str(e)}", exc_info=True)
                await message.reply(client_text['TEXT']['TECHNICAL_MAINTENANCE'])
                return
            # If the old admin is registered
            if member.user_id != zero_object.user_id:
                # If the old admin is admin
                if member.admin == 1:
                    try:
                        # Making changes to the database / Removing a user from the administrator role
                        await delete_admin(User, message.chat.id, member.user_id)
                    except Exception as e:
                        logging.error(f"FUNC: delete_admin_member (3)\nCHAT: {message.chat.id}\nUSER:\n{member.user_id}\nError: {str(e)}", exc_info=True)
                        await message.reply(client_text['TEXT']['TECHNICAL_MAINTENANCE'])
                        return

                    sticker_indx =  random.randrange(0, len(client_text['STICKERS']['DELETE_ADMIN']))
                    # Getting user information on telegram servers
                    user_info = await bot.get_chat_member(message.chat.id, member.user_id)
                    # Notification of removal from the administrator role
                    await message.reply(client_text['TEXT']['DELETE_ADMIN'].format(user_info['user']['first_name']))
                    await bot.send_sticker(chat_id=message.chat.id,
                                           sticker=f"{client_text['STICKERS']['DELETE_ADMIN'][sticker_indx]}")
                    return
                # User is not an administrator
                await message.reply(client_text['TEXT']['MEMBER_IS_NOT_ADMIN'])
                return
            # The user is not a chat administrator
            await message.reply(client_text['TEXT']['UNKNOWN_MEMBER'])
            return
        return


# The "/give_sp" command handler. Changing the social rating of users.
@dp.message_handler(ChatTypeFilter([types.ChatType.GROUP, types.ChatType.SUPERGROUP]), commands="give_sp", state=None)
async def give_sp_member(message: types.Message) -> 0:
    command = (str(message.text).split(' '))
    if len(command) == 1:
        return
    try:
        # Getting information about the chat user
        user = await get_entry(User, message.chat.id, message.from_user.id)
    except Exception as e:
        logging.error(f"FUNC: give_sp_member (1)\nCHAT: {message.chat.id}\nUSER:\n{message.from_user.id}\nError: {str(e)}", exc_info=True)
        await message.reply(client_text['TEXT']['TECHNICAL_MAINTENANCE'])
        return
    # If the user is registered
    if user.user_id != zero_object.user_id:
        # The command contains an attached message from the desired user and the caller is an administrator
        if (message.reply_to_message != None) and (user.admin == 1):
            try:
                member = await get_entry(User, message.chat.id, message.reply_to_message.from_user.id)
            except Exception as e:
                logging.error(f"CHAT: {message.chat.id}\nUSER: {message.reply_to_message.from_user.id}\n{str(e)}")
                await message.reply(client_text['TEXT']['TECHNICAL_MAINTENANCE'])
                return
            # Getting information about the target user chat
            if member.user_id != zero_object.user_id:
                # Getting amount
                try:
                    amount = int(command[1])
                except Exception as e:
                    logging.error(f"FUNC: give_sp_member (2)\nCHAT: {message.chat.id}\nUSER: {message.from_user.id}\n{str(e)}")
                    await message.reply(client_text['TEXT']['ERROR_AMOUNT'])
                    return
                try:
                    # Changing the social rating of the selected user
                    await change_social_points(User, message.chat.id, member.user_id, amount)
                except Exception as e:
                    logging.error(f"FUNC: give_sp_member (3)\nCHAT: {message.chat.id}\nUSER: {member.user_id}\n{str(e)}")
                    await message.reply(client_text['TEXT']['TECHNICAL_MAINTENANCE'])
                    return
                # Getting user information on telegram servers
                user_info = await bot.get_chat_member(message.chat.id, member.user_id)
                # Forming a commentary
                comment = ""
                if len(command) > 2:
                    comment = "\nПричина:"
                    for i in range(2, len(command)):
                        comment += f" {command[i]}"
                # If the amount is positive
                if amount >= 0:
                    sticker_indx =  random.randrange(0, len(client_text['STICKERS']['GIVE_SP_POS']))
                    await message.answer(client_text['TEXT']['GIVE_SP_POS'].format(
                            user_info['user']['first_name'],
                            amount,
                            comment
                        )
                    )
                    await bot.send_sticker(chat_id=message.chat.id,
                                           sticker=f"{client_text['STICKERS']['GIVE_SP_POS'][sticker_indx]}")
                    return
                # If the amount is negative
                sticker_indx = random.randrange(0, len(client_text['STICKERS']['GIVE_SP_NEG']))
                await message.answer(client_text['TEXT']['GIVE_SP_NEG'].format(
                        user_info['user']['first_name'],
                        amount,
                        comment
                    )
                )
                await bot.send_sticker(chat_id=message.chat.id,
                                       sticker=f"{client_text['STICKERS']['GIVE_SP_NEG'][sticker_indx]}")
                return
            # The user is not a chat administrator
            await message.reply(client_text['TEXT']['UNKNOWN_MEMBER'])
            return
        return


@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), commands=["start","info"], state=None)
async def start(message: types.Message) -> None:
    await message.reply(f"{client_text['TEXT']['INFO_HANDLER']}\n\n{client_text['TEXT']['INVITE'].format(PRICE_BUYBACK)}\n\n{client_text['TEXT']['INFO']}")


@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), commands=["reg"], state=None)
async def start(message: types.Message) -> None:
    await message.reply(f"{client_text['TEXT']['COMMAND_REG']}")


@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), commands=["baka"], state=None)
async def start(message: types.Message) -> None:
    await message.reply(f"{client_text['TEXT']['COMMAND_BAKA'].format(FINE_BAKA, EVENT_TIME_MAIN)}")


@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), commands=["buyback"], state=None)
async def start(message: types.Message) -> None:
    await message.reply(f"{client_text['TEXT']['COMMAND_BUYBACK'].format(PRICE_BUYBACK, EVENT_TIME_MAIN)}")


@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), commands=["my_stat"], state=None)
async def start(message: types.Message) -> None:
    await message.reply(f"{client_text['TEXT']['COMMAND_STAT']}")


@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), commands=["top_baka"], state=None)
async def start(message: types.Message) -> None:
    await message.reply(f"{client_text['TEXT']['COMMAND_TOP_BAKA']}")


@dp.message_handler(ChatTypeFilter(types.ChatType.PRIVATE), commands=["top_points"], state=None)
async def start(message: types.Message) -> None:
    await message.reply(f"{client_text['TEXT']['COMMAND_TOP_POINTS']}")


@dp.message_handler(ChatTypeFilter([types.ChatType.GROUP, types.ChatType.SUPERGROUP]))
async def message_handler(message: types.Message):

    if message.chat.id not in users_activity:
        users_activity[message.chat.id] = []
    for user in users_activity[message.chat.id]:
        if user.user_id == message.from_user.id:
            ok = await user.noflud()
            return
    users_activity[message.chat.id].append(User_Active(message.from_user.id))



async def activity_bonuses(chat_id):
    if chat_id in users_activity:
        baka = await get_entry_baka(User, chat_id)
        for user in users_activity[chat_id]:
            fold = 0
            if user.user_id == baka.user_id:
                fold = 1
            bonus = user.bonus - int((user.bonus/FINE)*fold)
            try:
                await change_social_points(User, chat_id, user.user_id, bonus)
            except Exception as e:
                logging.error(f"FUNC: activity_bonuses (1)\nCHAT: {chat_id}\nUSER: {user.user_id}\n{str(e)}")
        users_activity[chat_id] = []


# Selecting a new baka in all chats
async def chats_event_baka():
    try:
        chats = await get_chats(User)
    except Exception as e:
        logging.error(str(e))
        return
    if chats != []:
        for chat_id in chats:
            await activity_bonuses(chat_id)
            await reset_field_baka(User, chat_id)
    users_activity = {}
    users_buyback = {}


# Time looped event
async def scheduler():

    aioschedule.every().day.at("06:00").do(chats_event_baka)
    while (True):
        await aioschedule.run_pending()
        await asyncio.sleep(1)


# Registration of parallel events
async def on_startup(_):
    logging.info("Registration of parallel events")
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    try:
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    except:
        logging.info("Trying start polling")







