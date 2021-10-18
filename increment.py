import pickle
def increment(user):
    users = {}
    with open('/var/www/webApp/users_data.pckl', 'rb') as users_data:  
        users = pickle.load(users_data) 
    users[user]["sell_count"] += 1
    with open('/var/www/webApp/users_data.pckl', 'wb') as users_data:
        pickle.dump(users, users_data)