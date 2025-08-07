from .client_bot import build as build_client

client_app = build_client()

bots_by_secret = {
    "client": client_app,
}
