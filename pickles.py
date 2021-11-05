import pickle

with open('/var/www/webApp/users_data.pckl','wb') as users_data:
    users = {}
    pickle.dump(users, users_data)
    