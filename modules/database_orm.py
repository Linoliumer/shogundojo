from peewee import *

DB_PATH = "data/database.db"
INIT_SOCIAL_RATING = 1500
db = SqliteDatabase(DB_PATH)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    id = PrimaryKeyField(null=False)
    user_id = BigIntegerField(unique=False)
    chat_id = BigIntegerField(unique=False)
    admin = IntegerField(unique=False)
    social_points = BigIntegerField(unique=False)
    baka = IntegerField(unique=False)
    baka_times = IntegerField(unique=False)

    class Meta:
        db_table = "users"


def none_object(User) -> User:
    """
    Create a neutral object
    :return:
    """
    zero = User(
        user_id=0,
        chat_id=0,
        admin=0,
        social_points=0,
        baka=0,
        baka_times=0,
    )
    return zero

zero_object = none_object(User)


async def create_entry(User, user_id: int, chat_id: int, admin: int) -> bool:
    """
    Creates a record in the table with changed parameters, if there is no similar record in the table.
    True - record was created
    False - similar record exists in the table
    :param user_id:
    :param chat_id:
    :param admin:
    :return:
    """
    try:
        User.get(User.user_id == user_id, User.chat_id == chat_id)
    except DoesNotExist:
        User.create(
            user_id=user_id,
            chat_id=chat_id,
            admin=admin,
            social_points=INIT_SOCIAL_RATING,
            baka=0,
            baka_times=0
        )
        return True
    return False

async def delete_entries(User, chat_id: int) -> None:
    """
    Deletes records that contain the chat_id field from the database
    :param chat_id:
    :return:
    """
    User.delete().where(User.chat_id == chat_id).execute()

async def delete_entry(User, chat_id: int, user_id: int) -> None:
    """
    Deletes the record with user_id and chat_id fields from the table
    :param chat_id:
    :param user_id:
    :return:
    """
    User.delete().where(User.chat_id == chat_id, User.user_id == user_id).execute()

async def reset_field_baka(User, chat_id: int) -> None:
    """
    Resets the value of the field "baka" in all records with the field chat_id
    :param chat_id:
    :return:
    """
    User.update(baka=0).where(User.chat_id == chat_id).execute()

async def set_filed_baka(User, chat_id: int, user_id: int) -> None:
    """
    Sets the value of the field "baka" in the record with chat_id and user_id
    :param chat_id:
    :param user_id:
    :return:
    """
    User.update(baka=1, baka_times=User.baka_times + 1).where(
        User.user_id == user_id,
        User.chat_id == chat_id
    ).execute()

async def get_entries(User, chat_id: int) -> list:
    """
    Get an array of records with the chat_id field
    :param chat_id:
    :return:
    """
    users = User.select().where(User.chat_id == chat_id)
    users = [user for user in users]
    return users

async def get_chats(User) -> list:
    """
    Get an array of chat_id values
    :return:
    """
    chats = User.select(User.chat_id).distinct()
    chats = [chat.chat_id for chat in chats]
    return chats

async def get_entry_baka(User, chat_id: int) -> User:
    """
    Get a record with the value (baka == 0) of the chat_id field
    :param chat_id:
    :return:
    """
    try:
        user = User.get(User.chat_id == chat_id, User.baka == 1)
    except DoesNotExist:
        return zero_object
    return user

async def get_entries_baka_times(User, chat_id: int, limit: int) -> list:
    """
    Get up to 'limit' records with the maximum value of the baka_times field by the chat_id field
    :param chat_id:
    :param limit:
    :return:
    """
    bakas = User.select().where(User.baka_times > 0, User.chat_id == chat_id).order_by(
        User.baka_times.desc()).limit(limit)
    bakas = [baka for baka in bakas]
    return bakas

async def get_entries_social_stats(User, chat_id: int, limit: int) -> list:
    """
    Get up to 10 records with the maximum value of the social_points field by the chat_id field
    :param chat_id:
    :param limit:
    :return:
    """
    users = User.select().where(User.chat_id == chat_id).order_by(
        User.social_points.desc()).limit(limit)
    users = [user for user in users]
    return users

async def get_entry(User, chat_id: int, user_id: int) -> User:
    """
    Get a record by the user_id and chat_id fields
    :param chat_id:
    :param user_id:
    :return:
    """
    try:
        user = User.get(User.chat_id == chat_id, User.user_id == user_id)
    except DoesNotExist:
        return zero_object
    return user

async def change_social_points(User, chat_id: int, user_id: int, amount: int) -> None:
    """
    Change the social_points field in the record with the chat_id and user_id fields
    :param chat_id:
    :param user_id:
    :param amount:
    :return:
    """
    User.update(social_points=User.social_points + amount).where(
        User.chat_id == chat_id, User.user_id == user_id
    ).execute()

async def new_admin(User, chat_id: int, user_id: int) -> None:
    """
    Changes admin field to 1 in record with user_id, chat_id
    :param chat_id:
    :param user_id:
    :return:
    """
    User.update(admin=1).where(User.chat_id == chat_id, User.user_id == user_id).execute()

async def delete_admin(User, chat_id: int, user_id: int) -> None:
    """
    Changes admin field to 1 in record with user_id, chat_id
    :param chat_id:
    :param user_id:
    :return:
    """
    User.update(admin=0).where(User.chat_id == chat_id, User.user_id == user_id).execute()

async def get_admins(User, chat_id: int) -> list:
    """
    Get entries where admin = 1 and chat_id
    :param chat_id:
    :return:
    """
    admins = User.select().where(User.chat_id == chat_id, User.admin == 1)
    admins = [admin for admin in admins]
    return admins






'''
async def bot_kicked(User, chat_id):
    User.delete().where(User.chat_id == chat_id).execute()


async def reg_user(User, user_id, chat_id):
    try:
        User.get(User.user_id==user_id, User.chat_id==chat_id)
    except DoesNotExist:
        User.create(
            user_id=user_id,
            chat_id=chat_id,
            active=1,
            admin=0,
            social_points=1500,
            baka=0,
            baka_times=0
        )
        return True
    return False


async def left_user_bd(User, chat_id, user_id):
    User.delete().where(User.chat_id == chat_id, User.user_id == user_id).execute()


async def reset_baka_chat(User, chat_id):
    User.update(baka=0).where(User.chat_id == chat_id).execute()

async def new_baka(User, chat_id, user_id):
    User.update(baka=0).where(User.chat_id == chat_id).execute()
    User.update(baka=1, baka_times=User.baka_times + 1).where(
        User.user_id == user_id,
        User.chat_id == chat_id
    ).execute()




async def get_users(User, chat_id):
    users = User.select().where(User.chat_id == chat_id, User.active == 1)
    users = [[user.user_id, user.social_points] for user in users]
    if users == []:
        return None
    return users

async def get_chats(User):
    chats = User.select(User.chat_id).distinct()
    chats = [chat.chat_id for chat in chats]
    if chats == []:
        return None
    return chats


async def get_baka(User, chat_id):
    try:
        user = User.get(User.chat_id == chat_id, User.active == 1, User.baka == 1)
    except DoesNotExist:
        return None
    return user.user_id

async def get_user(User, user_id):
    user = User.select().where(User.user_id == user_id, User.active == 1)
    user = [[user_entry.chat_id, user_entry.social_points, user_entry.baka, user_entry.baka_times] for user_entry in user]
    if user == []:
        return None
    return user


async def get_baka_times(User, chat_id):
    bakas = User.select().where(User.baka_times > 0, User.chat_id==chat_id).order_by(User.baka_times.desc()).limit(10)
    bakas = [[baka.user_id, baka.baka_times] for baka in bakas]
    if bakas == []:
        return None
    return bakas

async def get_social_stats(User, chat_id):
    users = User.select().where(User.active==1, User.chat_id==chat_id).order_by(User.social_points.desc()).limit(10)
    users = [[user.user_id, user.social_points] for user in users]
    if users == []:
        return None
    return users


async def get_user_stat(User, chat_id,  user_id):
    try:
        user = User.get(User.chat_id == chat_id, User.user_id == user_id, User.active == 1)
    except DoesNotExist:
        return None
    return user


async def give_social_points(User, chat_id, user_id, amount):
    User.update(social_points=User.social_points+int(amount)).where(User.active == 1, User.chat_id == chat_id, User.user_id == user_id).execute()


async def new_admin(User, chat_id, user_id):
    User.update(admin=1).where(User.chat_id == chat_id, User.user_id == user_id).execute()

async def delete_admin(User, chat_id, user_id):
    User.update(admin=0).where(User.chat_id == chat_id, User.user_id == user_id).execute()

async def get_admins(User, chat_id):
    admins = User.select().where(User.chat_id == chat_id, User.admin == 1)
    admins = [admin.user_id for admin in admins]
    if admins == []:
        return None
    return admins
'''