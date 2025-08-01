import gdown

# Link file Google Drive public
url = "https://drive.google.com/uc?id=1UYD05VutTzExD8BRsLu44zRJbjiCnXEr"
output = "file_dung.zip"  # d?i tên file tùy ý

gdown.download(url, output, quiet=False)
