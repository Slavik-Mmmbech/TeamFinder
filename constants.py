# Общие константы для приложений

# Статусные константы
STATUS_OPEN = "open"
STATUS_CLOSED = "closed"
STATUS_CHOICES = [
  (STATUS_OPEN, "Open"),
  (STATUS_CLOSED, "Closed"),
]

# Пагинация
PAG_PER_PAGE = 12

RESULTS_END = 20

## Особые константы для приложения projects

MAX_LENGTH_RROJECT = 200
MAX_STATUS_LENGTH = 6


## Особые константы для приложения users

# Максимальная длина
MAX_ABOUT_LENGTH= 256
MAX_LENGTH_USER = 124
PHONE_LENGTH = 12

# Цвета для генерации аватаров
AVATAR_COLORS = [
    "#1abc9c",
    "#2ecc71",
    "#3498db",
    "#9b59b6",
    "#34495e",
    "#16a085",
    "#27ae60",
]

# Инфо для генерации аватаров
AVATAR_SIZE = (256, 256)
AVATAR_FONT_NAME = "Neue_Haas_Grotesk_Display_Pro_75_Bold.otf"
AVATAR_FONT_SIZE = 120
AVATAR_TEXT_COLOR = "#ffffff"
AVATAR_IMAGE_FORMAT = "PNG"

SEARCH_RES = 10