from asyncpg import UniqueViolationError

from db_api.schemas.hotel import Hotel
from db_api.schemas.user import User


async def add_user(id: int, name: str):
    try:
        user = User(id=id, name=name)

        await user.create()

    except UniqueViolationError:
        pass


async def select_user(id: int):
    user = await User.query.where(User.id == id).gino.first()

    return user


async def add_hotel(id: int, name: str, address: str, distance: float, night_price: int,
                    all_period_price: int, link: str):
    hotel = Hotel(id=id, name=name, address=address, distance=distance, night_price=night_price,
                  all_period_price=all_period_price, link=link)

    await hotel.create()


async def choose_hotels(user_id: int):
    hotels = await Hotel.query.where(Hotel.id == user_id).gino.all()
    return hotels
