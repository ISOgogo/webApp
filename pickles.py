import pickle

with open('users_data.pckl','wb') as users_data:
    users = {}
    pickle.dump(users, users_data)
    