import json

import requests
import datetime
import base64
from urllib.parse import urlencode

client_id = "8423c787562c4c20b401b24b5f1af268"
client_secret = "d3b5599d7e97442dbaedf43a69b4dd5f"
#user_id = "12172986606"

class SpotifyAPI(object):
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    token_url = "https://accounts.spotify.com/api/token"
    profile_url = "https://api.spotify.com/v1/users/"
    current_profile_url = "https://api.spotify.com/v1/me"
    auth_url = "https://accounts.spotify.com/authorize?client_id=8423c787562c4c20b401b24b5f1af268&scopes=playlist-modify-public&response_type=code&redirect_uri=http%3A%2F%2Fgoogle.com%2F"

    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret
        self.playlist_id = None
        self.all_song_info = {}

    def get_client_creds(self):
        #return base64 encoded string
        client_id = self.client_id
        client_secret = self.client_secret

        if client_secret==None or client_id==None:
            raise Exception("You must set client id and/or client secret")
        client_creds = f"{client_id}:{client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()

    def get_token_headers(self):
        client_creds_b64 = self.get_client_creds()
        print(client_creds_b64)
        return {
            "Authorization": f"Basic {client_creds_b64}"
        }

    def get_token_data(self):
        return {
            "grant_type": "client_credentials"
        }

    def get_auth_data(self):
        return {
            "grant_type": "authorization_code",
            "code": "8423c787562c4c20b401b24b5f1af268",
            "redirect_uri": "http%3A%2F%2Fgoogle.com%2F"
        }

    def auth_edit(self):
        r = requests.get(self.test)
        if r.status_code not in range(200, 299):
            return {}
        #return r.json()
        auth_url = self.auth_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        '''
        auth_req = requests.post(auth_url, data=token_data, headers=token_headers)
        if auth_req.status_code not in range(200, 299):
            print("nope")
            raise Exception("Could not authenticate client.")
        data = r.json()
        return True
        '''

    def perform_auth(self):
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        r = requests.post(token_url, data=token_data, headers=token_headers)
        if r.status_code not in range(200, 299):
            raise Exception("Could not authenticate client.")
        data = r.json()
        now = datetime.datetime.now()
        access_token = data['access_token']
        expires_in = data['expires_in']  # seconds
        expires = now + datetime.timedelta(seconds=expires_in)
        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        return True

    def get_access_token(self):
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now:
            self.perform_auth()
            return self.get_access_token()
        elif token == None:
            self.perform_auth()
            return self.get_access_token()
        return token

    def get_resource_header(self):
        access_token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        return headers

    def get_resource(self, lookup_id, resource_type='albums', version='v1'):
        endpoint = f"https://api.spotify.com/{version}/{resource_type}/{lookup_id}"
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()

    def get_spotify_uri(self, song_name, artist):
        """Search For the Song"""
        access_token = self.get_access_token()
        query = f"https://api.spotify.com/v1/search?query=track%3A{song_name}+artist%3A{artist}&type=track&offset=0&limit=20"
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
        )
        response_json = response.json()
        songs = response_json["tracks"]["items"]

        # only use the first song
        uri = songs[0]["uri"]
        print(uri)
        return uri


    def find_playlist(self):
        profile_url = self.get_user_profile()
        profile_url = str(profile_url) + "/playlists"
        headers = self.get_resource_header()
        r = requests.get(profile_url, headers=headers)
        user = r.json()

        playlist_names = [user['items'][i]['name'] for i in range(len(user['items']))]

        look_for_playlist = input("Which playlist do you want to add music to?\n")
        look_for_playlist = str(look_for_playlist).lower()

        index_of_playlist = 0
        count = 0

        for playlist in playlist_names:
            if str(playlist).lower() == look_for_playlist:
                index_of_playlist = count
                break
            count = count + 1

        playlist_id = user['items'][index_of_playlist]['id']
        return playlist_id

    def get_user_profile(self):
        user_id = input("What is your Spotify user id?\n")
        profile_url = self.profile_url + str(user_id)
        self.profile_url = profile_url

        return profile_url

    def add_song_to_playlist(self):
        access_token = self.get_access_token()
        headers = self.get_resource_header()
        headers2 = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        playlist_id = self.find_playlist()
        query = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

        song_name = str(input("What song do you want to add?\n")) #query
        s_artist = str(input("Who is the artist?\n")) #search_type

        search_info = {"song_name": song_name, "artist": s_artist,
                       "spotify_uri": self.get_spotify_uri(song_name, s_artist)}

        self.all_song_info["Song"] = search_info

        uris = [info["spotify_uri"]
                for song, info in self.all_song_info.items()]

        request_data = json.dumps(uris)

        r = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            })

        r2 = requests.get(query, headers=headers)
        songs_dict = r2.json()
        songs = [songs_dict['items'][i]['track']['name'] for i in range(len(songs_dict['items']))]
        #print(songs)

        if r.status_code != 200:
            print(r.status_code)
            print(r.json())
            return{}
        return r.json()

    def search_playlist(self):
        profile_url = self.get_user_profile()
        profile_url = str(profile_url) + "/playlists"
        headers = self.get_resource_header()
        r = requests.get(profile_url, headers=headers)
        user = r.json()

        playlist_names = [user['items'][i]['name'] for i in range(len(user['items']))]

        look_for_playlist = input("Which playlist do you want to add music to?\n")
        look_for_playlist = str(look_for_playlist).lower()

        index_of_playlist = 0
        count = 0

        for playlist in playlist_names:
            if str(playlist).lower() == look_for_playlist:
                index_of_playlist = count
                break
            count = count + 1

        playlist_id = user['items'][index_of_playlist]['id']

        url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        r2 = requests.get(url, headers=headers)
        songs_dict = r2.json()
        songs = [songs_dict['items'][i]['track']['name'] for i in range(len(songs_dict['items']))]
        print(songs)


#user_id = "12172986606"

spotify = SpotifyAPI(client_id,client_secret)

#spotify.auth_edit()

spotify.add_song_to_playlist()

'''
headers2 = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {access_token}"
}

add_to_playlist = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
#r2 = requests.get(add_to_playlist, headers=headers2)
'''

