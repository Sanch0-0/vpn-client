class AppState:
    def __init__(self):
        self.connected = False
        self.connected_at = None
        self.current_server = None
        self.servers = []

        self.token = None
        self.refresh_token = None

        self.error = None

        self.user = None
        self.is_authenticated = False
        self.is_loading = False


W, H = 375, 725
app_state = AppState()
