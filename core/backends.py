from axes.backends import AxesStandaloneBackend
from core.models import CustomUser
from django.contrib.auth.hashers import check_password
import logging
logger = logging.getLogger(__name__)

class CustomUserBackend(AxesStandaloneBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        logger.debug(f"Attempting to authenticate user: {username}")
        try:
            if CustomUser.objects.filter(staff_id=username).exists():
                user = CustomUser.objects.get(staff_id=username)
            elif CustomUser.objects.filter(roll_number=username).exists():
                user = CustomUser.objects.get(roll_number=username)
            else:
                return None

            if user and check_password(password, user.password):
                return user
            else:
                logger.debug(f"Password for student {username} is incorrect")

        except CustomUser.DoesNotExist:
            logger.debug(f"User {username} does not exist")
            return None
    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
