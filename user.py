from flask_login import UserMixin

class User(UserMixin):

    def __init__(self, user_info):
        self.id = user_info[0]
        self.email = user_info[1]
        self.password = user_info[4] 
        self.companyName = user_info[2]
        self.companyUrl = user_info[3]
