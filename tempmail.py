import requests

base_url = "https://api.mail.tm/"
header = {"Accept": "application/json", "Content-Type": "application/json"}


class TempMail:
    def __init__(self, address, password):
        self._address = address
        self._password = password
        self._data = {"address": address, "password": password}


    def generate(self):
        try:
            account = requests.post(base_url + "accounts", headers=header, json=self._data)
            get_token = requests.post(base_url + "token", headers=header, json=self._data).json()
            self._token = get_token.get("token")

            if not self._token:
                message = account.json().get("detail")
                raise GenerateError(message)

        except Exception as error:
            raise GenerateError(error)

        else:
            if account.status_code == 422:
                header.update({"Authorization": "bearer " + self._token})
                account = requests.get(base_url + "me", headers=header).json()
            else:
                account = account.json()
            return account


    def get_messages(self):
        header.update({"Authorization": "bearer " + self._token})
        self._auth_header = header
        messages = requests.get(base_url + "messages", headers=self._auth_header).json()
        return messages


class Error(Exception):
    pass


class GenerateError(Error):
    def __init__(self, message):
        self.message = message


def domains():
    available_domains = requests.get(base_url + "domains", headers=header).json()
    return available_domains
