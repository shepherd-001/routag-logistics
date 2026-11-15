from faker import Faker

from config.logger import get_logger
from config.settings import get_settings

settings = get_settings()
logger = get_logger()
fake = Faker()
