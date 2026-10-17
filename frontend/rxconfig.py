import reflex as rx

config = rx.Config(
    app_name="itam_pro",
    frontend_port=3000,
    backend_port=8000,
    disable_plugins=[rx.plugins.SitemapPlugin],
)
