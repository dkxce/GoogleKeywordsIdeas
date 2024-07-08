
### HELP cmd line args: 
###
###  -f "./google_oauth.json"
###
### SEE `how_to.md`

import os
import re
import sys
import socket
import hashlib
import argparse
import webbrowser 

from pathlib import Path
from urllib.parse import unquote
from google_auth_oauthlib.flow import Flow # google-auth
from google.ads.googleads.client import GoogleAdsClient # google-ads


YAML_CONFIG_HOWTO = 'https://developers.google.com/google-ads/api/docs/client-libs/python/configuration'
YAML_CONFIG_BLANK = 'https://github.com/googleads/google-ads-python/blob/main/google-ads.yaml'

YAML_PATH         = "./google-ads.yaml"   # Google Ads Credintals
JSON_PATH         = './google_oauth.json' # Google Project Client Credintals

REDIRECT_HOST     = '127.0.0.1'
REDIRECT_PORT     = 8008


def __is_port_in_use__(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def __get_free_port_from__(port: int) -> int:
    while __is_port_in_use__(port): port += 1
    return port


def __get_token__(client_secrets_path, scopes) -> str:
    """
    @client_secrets_path: a path to client secrets JSON file
    @scopes: a list of API scopes to include in the auth request: 
        https://developers.google.com/identity/protocols/oauth2/scopes
    """
    
    PORT = __get_free_port_from__(REDIRECT_PORT) if REDIRECT_HOST in ['127.0.0.1','localhost'] else REDIRECT_PORT
    
    flow = Flow.from_client_secrets_file(client_secrets_path, scopes=scopes)
    flow.redirect_uri = f'http://{REDIRECT_HOST}:{PORT}'    
    passthrough_val = hashlib.sha256(os.urandom(1024)).hexdigest()
    auth_url, _ = flow.authorization_url(access_type="offline", state=passthrough_val, prompt="consent", include_granted_scopes="true", )

    print("Paste this URL into your browser:\n")
    print(auth_url)
    print(f"\nWaiting for authorization ...")
    webbrowser.open(auth_url)

    # Retrieves an authorization code by opening a socket to receive the redirect request and parsing the query parameters set in the URL.
    code = unquote(__get_authorization_code__(passthrough_val,PORT))
    # Pass the code back into the OAuth module to get a refresh token.
    flow.fetch_token(code=code)
    refresh_token = flow.credentials.refresh_token

    print(f"\nYour refresh token is:\n{refresh_token}\n")
    print(f"Add your refresh token to your client library configuration file `{YAML_PATH}` as described here: ")
    print(f"{YAML_CONFIG_HOWTO}\n")
    print(f"Blank file you can get here:\n{YAML_CONFIG_BLANK}")
    
    return refresh_token


def __get_authorization_code__(passthrough_val, port) -> str:
    """
    Opens a socket to handle a single HTTP request containing auth tokens.
    @passthrough_val: an anti-forgery token used to verify the request received by the socket.
    Returns:
        access token from the Google Auth service.
    """
    
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((REDIRECT_HOST, port))
    sock.listen(1)
    connection, _ = sock.accept()
    data = connection.recv(1024)
    
    params = __parse_raw_query_params__(data)
    try:
        if not params.get("code"):
            error = params.get("error")
            message = f"<b>Failed to retrieve authorization code. Error: {error}</b>"
            raise ValueError(message)
        elif params.get("state") != passthrough_val:
            message = "<b>State token does not match the expected state.</b>"
            raise ValueError(message)
        else:
            message = f"<b>Authorization code was successfully retrieved.</b><p>You can find out refresh token in <b>console</b> or <b>output log</b></p>"
            message += (f"Add your refresh token to your client library configuration file `<b>{YAML_PATH}</b>` as described here: <br/>")
            message += (f'<a target="_blank" href="{YAML_CONFIG_HOWTO}">{YAML_CONFIG_HOWTO}</a><br/><br/>')
            message += (f'Blank file you can get here: <br/> <a target="_blank" href="{YAML_CONFIG_BLANK}">{YAML_CONFIG_BLANK}</a><br/>')
    except ValueError as error:
        print(error)
        if __name__ == "__main__": sys.exit(1)
        raise error
    finally:
        response = (f"HTTP/1.1 200 OK\nContent-Type: text/html\n\n{message}")
        connection.sendall(response.encode())
        connection.close()
    return params.get("code")


def __parse_raw_query_params__(data) -> dict:
    decoded = data.decode("utf-8")
    match = re.search(r"GET\s\/\?(.*) ", decoded)
    params = match.group(1)
    pairs = [pair.split("=") for pair in params.split("&")]
    return {key: val for key, val in pairs}


def get_refresh_token(json_file: str = JSON_PATH, additional_scopes: list | None = None) -> str:
    '''
    Get OAuth Client Refresh Token for `google-ads.yaml` file.
    @json_file - path to `google-ads.yaml` file
    @additional_scopes - a list of API scopes to include in the auth request (https://developers.google.com/identity/protocols/oauth2/scopes)
    '''
   
    configured_scopes = ["https://www.googleapis.com/auth/adwords"]
    if additional_scopes: configured_scopes.extend(additional_scopes)
    return __get_token__(json_file, configured_scopes)


if __name__ == "__main__":
    
    if not YAML_PATH or not (yaml_file := Path(YAML_PATH)) or not yaml_file.is_file():
        
        json_path = JSON_PATH if (jfile := Path(JSON_PATH)) and jfile.is_file() else None
        parser = argparse.ArgumentParser(description="Generates OAuth Client Refresh Token")
        parser.add_argument("-f", "--file", type=str, required=False, default=JSON_PATH, help="Google OAuth JSON file with client id and secret",)
        
        try: get_refresh_token(json_path or parser.parse_args().file)
        except: print()
        
    else:
        
        gc = GoogleAdsClient.load_from_storage(path=YAML_PATH,version="v17")
        valid = "valid" if gc.credentials.valid else "invalid"
        
        print(f'GoogleAdsClient Credintals is {valid}:\n')
        print(f' login_customer_id:\n  {gc.login_customer_id}')
        print(f' developer_token:\n  {gc.developer_token}')
        print(f' client_id:\n  {gc.credentials.client_id}')
        print(f' client_secret:\n  {gc.credentials.client_secret}')
        print(f' refresh_token:\n  {gc.credentials.refresh_token}')
        
    print()
    input('Press Enter to Exit')