import requests
from requests import Response
from typing import List, Dict, Tuple, Union

from .errors import UnauthorizedError, Error, Forbidden, NotFoundError
from .types import Token, Permission, Ban


class Client:
    """Client to interface with the SpamWatch API."""
    def __init__(self, token: str, *, host: str = 'https://api.spamwat.ch') -> None:
        """
        Args:
            token: The Authorization Token
            host: The API host. Defaults to the official API.
        """
        self._token = token
        self._host = host
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {self._token}"})
        self._token = self.get_self()
        self.permission = self._token.permission

    def _make_request(self, path: str, method: str = 'get', **kwargs) -> Tuple[Dict, Response]:
        """
        Make a request and handle errors

        Args:
            path: Path on the API without a leading slash
            method: The request method. Defaults to GET
            **kwargs: Keyword arguments passed to the request method.

        Returns: The json response and the request object

        """
        req = self._session.request(method, f'{self._host}/{path}',
                                    **kwargs)
        if req.status_code in [200, 201]:
            return req.json(), req
        if req.status_code == 204:
            return {}, req
        elif req.status_code == 401:
            raise UnauthorizedError("Make sure your Token is correct")
        elif req.status_code == 403:
            raise Forbidden(self._token)
        elif req.status_code == 404:
            raise NotFoundError()
        else:
            raise Error(req)

    def version(self) -> Dict[str, str]:
        """Get the API version"""
        return self._make_request('version')[0]

    # region Tokens
    def get_tokens(self) -> List[Token]:
        """Get all tokens
        Requires Root permission

        Returns: A list of Tokens

        """
        data, req = self._make_request('tokens')
        return [Token(**token) for token in data]

    def create_token(self, userid: int, permission: Permission) -> Token:
        """Creates a token with the given parameters
        Requires Root permission

        Args:
            userid: The Telegram User ID of the token owner
            permission: The permission level the Token should have

        Returns: The created Token

        """
        data, req = self._make_request('tokens', method='post',
                                       json={"id": userid,
                                             "permission": permission.name})
        return Token(**data)

    def get_self(self) -> Token:
        """Gets the Token that the request was made with."""
        data, req = self._make_request('tokens/self')
        return Token(**data)

    def get_token(self, token_id: int) -> Token:
        """Get a token using its ID
        Requires Root permission

        Args:
            token_id: The token ID

        Returns: The token

        """
        data, req = self._make_request(f'tokens/{token_id}')
        return Token(**data)

    def delete_token(self, token_id: int) -> None:
        """Delete a token using its ID

        Args:
            token_id: The id of the token

        """
        self._make_request(f'tokens/{token_id}', method='delete')

    # endregion

    # region Bans
    def get_bans(self) -> List[Ban]:
        """Get a list of all bans
        Requires Admin Permission

        Returns: A list of Bans

        """
        data, req = self._make_request('banlist')
        return [Ban(**ban) for ban in data]

    def add_ban(self, user_id: int, reason: str) -> None:
        """Adds a ban

        Args:
            user_id: ID of the banned user
            reason: Reason why the user was banned
        """
        self._make_request(f'banlist', method='post',
                           json=[{
                               "id": user_id,
                               "reason": reason
                           }])

    def add_bans(self, data: List[Ban]) -> None:
        """Add a list of Bans

        Args:
            data: List of Ban objects
        """
        data = [{"id": d.id, "reason": d.reason} for d in data]
        self._make_request(f'banlist', method='post',
                           json=data)

    def get_ban(self, user_id, not_found_ok=False) -> Union[Ban, None]:
        """Gets a ban

        Args:
            user_id: ID of the user
            not_found_ok: Return None on 404 not found (user not banned)

        Returns: Ban object or None

        """
        try:
            data, req = self._make_request(f'banlist/{user_id}')
            return Ban(**data)
        except NotFoundError as err:
            if not_found_ok:
                return
            else:
                raise err

    def delete_ban(self, user_id) -> None:
        """Remove a ban"""
        self._make_request(f'banlist/{user_id}', method='delete')
    # endregion